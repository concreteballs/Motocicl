"""Apply the complete checked-in SQL migration chain to disposable PostgreSQL."""
from __future__ import annotations

import os
import unittest
from pathlib import Path

import psycopg

DATABASE_URL = os.environ.get("MOTOCICL_TEST_DATABASE_URL")
MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


@unittest.skipUnless(DATABASE_URL, "MOTOCICL_TEST_DATABASE_URL is not configured")
class PostgresMigrationChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                        CREATE ROLE anon NOLOGIN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                        CREATE ROLE authenticated NOLOGIN;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                        CREATE ROLE service_role NOLOGIN BYPASSRLS;
                    END IF;
                END
                $$;
            """)
            for migration in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")):
                conn.execute(migration.read_text(encoding="utf-8"))
            conn.commit()

    def test_all_expected_worker_tables_exist(self):
        expected = {
            "yj64_ci_events",
            "yj64_task_queue",
            "yj64_task_checkpoints",
            "yj64_model_request_attempts",
            "yj64_payload_manifests",
            "yj64_payload_chunks",
            "yj64_provider_limit_profiles",
            "yj64_provider_request_reservations",
            "yj64_ci_log_analyses",
            "yj64_ci_fix_proposals",
        }
        with psycopg.connect(DATABASE_URL) as conn:
            rows = conn.execute(
                """SELECT tablename FROM pg_tables
                   WHERE schemaname = 'public'"""
            ).fetchall()
        actual = {row[0] for row in rows}
        self.assertTrue(expected.issubset(actual), sorted(expected - actual))

    def test_server_only_queue_access_and_rls_are_preserved(self):
        with psycopg.connect(DATABASE_URL) as conn:
            queue_rls = conn.execute(
                """SELECT relrowsecurity FROM pg_class
                   WHERE oid = 'public.yj64_task_queue'::regclass"""
            ).fetchone()[0]
            anon_can_select = conn.execute(
                "SELECT has_table_privilege('anon', 'public.yj64_task_queue', 'SELECT')"
            ).fetchone()[0]
            authenticated_can_select = conn.execute(
                "SELECT has_table_privilege('authenticated', 'public.yj64_task_queue', 'SELECT')"
            ).fetchone()[0]
            service_can_select = conn.execute(
                "SELECT has_table_privilege('service_role', 'public.yj64_task_queue', 'SELECT')"
            ).fetchone()[0]
        self.assertTrue(queue_rls)
        self.assertFalse(anon_can_select)
        self.assertFalse(authenticated_can_select)
        self.assertTrue(service_can_select)

    def test_worker_recovery_columns_and_reservation_constraints_exist(self):
        with psycopg.connect(DATABASE_URL) as conn:
            columns = {
                row[0] for row in conn.execute(
                    """SELECT column_name FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = 'yj64_task_queue'"""
                ).fetchall()
            }
            constraints = {
                row[0] for row in conn.execute(
                    """SELECT conname FROM pg_constraint
                       WHERE conrelid = 'public.yj64_provider_request_reservations'::regclass"""
                ).fetchall()
            }
        self.assertTrue(
            {"deadline_at", "blocked_reason", "capacity_deferrals", "max_attempts"}
            .issubset(columns)
        )
        self.assertIn("yj64_provider_reservation_sent_state_has_timestamp", constraints)
        self.assertIn("yj64_provider_reservation_reconciliation_evidence", constraints)


if __name__ == "__main__":
    unittest.main()
