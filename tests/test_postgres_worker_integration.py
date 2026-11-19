"""Real PostgreSQL tests for queue claiming and expired-lease recovery.

These tests use an isolated schema in a disposable CI PostgreSQL service. They
intentionally do not connect to Supabase or apply production migrations.
"""
from __future__ import annotations

import os
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

DATABASE_URL = os.environ.get("MOTOCICL_TEST_DATABASE_URL")


@unittest.skipUnless(DATABASE_URL, "MOTOCICL_TEST_DATABASE_URL is not configured")
class PostgresWorkerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        cls.psycopg = psycopg
        cls.schema = "motocicl_it_" + uuid.uuid4().hex
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            conn.execute(f'CREATE SCHEMA "{cls.schema}"')
        from motocicl.automation.postgres_store import PostgresCycleStore
        cls.store = PostgresCycleStore(
            DATABASE_URL,
            connect_factory=lambda url: psycopg.connect(
                url, options=f"-c search_path={cls.schema}"
            ),
        )
        with cls.connection() as conn:
            conn.execute("""
                CREATE TABLE yj64_task_queue (
                    task_id BIGSERIAL PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    locked_at TIMESTAMPTZ,
                    lock_owner TEXT,
                    last_error TEXT,
                    blocked_reason TEXT,
                    deadline_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    dedupe_key TEXT NOT NULL UNIQUE
                )
            """)
            conn.execute("""
                CREATE TABLE yj64_provider_request_reservations (
                    reservation_id BIGSERIAL PRIMARY KEY,
                    queue_task_id BIGINT NOT NULL REFERENCES yj64_task_queue(task_id),
                    state TEXT NOT NULL,
                    last_error_classification TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE yj64_task_checkpoints (
                    checkpoint_id BIGSERIAL PRIMARY KEY,
                    queue_task_id BIGINT NOT NULL REFERENCES yj64_task_queue(task_id),
                    sequence BIGINT NOT NULL,
                    checkpoint JSONB NOT NULL
                )
            """)

    @classmethod
    def tearDownClass(cls):
        with cls.psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            conn.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')

    @classmethod
    def connection(cls):
        return cls.psycopg.connect(
            DATABASE_URL, options=f"-c search_path={cls.schema}"
        )

    def enqueue(self, dedupe_key):
        with self.connection() as conn:
            row = conn.execute(
                """INSERT INTO yj64_task_queue (task_type, payload, dedupe_key)
                   VALUES ('integration_test', '{"ok": true}'::jsonb, %s)
                   RETURNING task_id""",
                (dedupe_key,),
            ).fetchone()
        return row[0]

    def test_two_workers_claim_distinct_tasks_concurrently(self):
        self.enqueue("concurrent-a")
        self.enqueue("concurrent-b")
        barrier = threading.Barrier(2)

        def claim(worker_id):
            barrier.wait(timeout=5)
            return self.store.claim_next_task(worker_id, lease_seconds=30)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(claim, ("worker-a", "worker-b")))

        self.assertTrue(all(result is not None for result in results))
        self.assertEqual(len({result["task_id"] for result in results}), 2)
        self.assertEqual(
            {result["worker_id"] for result in results}, {"worker-a", "worker-b"}
        )

    def test_expired_lease_is_reclaimed_and_old_owner_is_rejected(self):
        task_id = self.enqueue("expired-lease")
        with self.connection() as conn:
            conn.execute(
                """UPDATE yj64_task_queue
                   SET state = 'running', attempts = 1, lock_owner = 'dead-worker',
                       locked_at = now() - interval '90 seconds'
                   WHERE task_id = %s""",
                (task_id,),
            )

        reclaimed = self.store.claim_next_task("replacement-worker", lease_seconds=30)
        self.assertEqual(reclaimed["task_id"], task_id)
        self.assertEqual(reclaimed["attempts"], 2)
        self.assertFalse(self.store.renew_task_lease(task_id, "dead-worker", 30))
        self.assertTrue(self.store.renew_task_lease(task_id, "replacement-worker", 30))

    def test_expired_ambiguous_provider_send_is_quarantined_not_replayed(self):
        task_id = self.enqueue("ambiguous-send")
        with self.connection() as conn:
            conn.execute(
                """UPDATE yj64_task_queue
                   SET state = 'running', attempts = 1, lock_owner = 'dead-worker',
                       locked_at = now() - interval '90 seconds'
                   WHERE task_id = %s""",
                (task_id,),
            )
            conn.execute(
                """INSERT INTO yj64_provider_request_reservations
                   (queue_task_id, state) VALUES (%s, 'sending')""",
                (task_id,),
            )

        claimed = self.store.claim_next_task("replacement-worker", lease_seconds=30)
        self.assertIsNone(claimed)
        with self.connection() as conn:
            task = conn.execute(
                "SELECT state, blocked_reason FROM yj64_task_queue WHERE task_id = %s",
                (task_id,),
            ).fetchone()
            reservation = conn.execute(
                """SELECT state, last_error_classification
                   FROM yj64_provider_request_reservations WHERE queue_task_id = %s""",
                (task_id,),
            ).fetchone()
        self.assertEqual(task, ("blocked", "request_outcome_unknown"))
        self.assertEqual(reservation, ("unknown", "worker_lease_expired"))


if __name__ == "__main__":
    unittest.main()
