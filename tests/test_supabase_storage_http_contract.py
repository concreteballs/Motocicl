"""HTTP-level contract test for the Supabase Storage adapter.

Runs a disposable local HTTP server. This exercises urllib's real request and
response handling without Supabase credentials or external network access.
It is an API contract emulator, not the Supabase Storage implementation.
"""
from __future__ import annotations

import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest
from urllib.parse import unquote, urlsplit

from motocicl.automation.supabase_storage import SupabaseStorageArtifactStore


class StorageContractHandler(BaseHTTPRequestHandler):
    objects: dict[str, bytes] = {}
    requests_seen: list[tuple[str, str, str | None]] = []
    forced_status: int | None = None
    get_delay_seconds = 0.0

    def log_message(self, *_args):
        pass

    def _authorized(self) -> bool:
        return (
            self.headers.get("Authorization") == "Bearer local-contract-secret"
            and self.headers.get("Apikey") == "local-contract-secret"
        )

    def _key(self) -> str:
        path = unquote(urlsplit(self.path).path)
        prefix = "/storage/v1/object/"
        authenticated_prefix = "/storage/v1/object/authenticated/"
        if path.startswith(authenticated_prefix):
            return path[len(authenticated_prefix):]
        if path.startswith(prefix):
            return path[len(prefix):]
        return ""

    def _send(self, status: int, body: bytes = b"") -> None:
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        if body:
            self.send_header("Content-Type", "application/json")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_POST(self):
        key = self._key()
        StorageContractHandler.requests_seen.append(
            ("POST", key, self.headers.get("x-upsert"))
        )
        if not self._authorized():
            return self._send(401, b'{"message":"unauthorized"}')
        if StorageContractHandler.forced_status is not None:
            return self._send(
                StorageContractHandler.forced_status,
                b'{"message":"simulated storage failure"}',
            )
        if not key.startswith("yj64-private-artifacts/"):
            return self._send(404)
        payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if key in StorageContractHandler.objects:
            return self._send(409, b'{"message":"The resource already exists"}')
        StorageContractHandler.objects[key] = payload
        self._send(200, b'{"Key":"stored"}')

    def do_GET(self):
        key = self._key()
        StorageContractHandler.requests_seen.append(("GET", key, None))
        if not self._authorized():
            return self._send(401, b'{"message":"unauthorized"}')
        if StorageContractHandler.forced_status is not None:
            return self._send(
                StorageContractHandler.forced_status,
                b'{"message":"simulated storage failure"}',
            )
        if StorageContractHandler.get_delay_seconds:
            time.sleep(StorageContractHandler.get_delay_seconds)
        if not key.startswith("yj64-private-artifacts/"):
            return self._send(404)
        payload = StorageContractHandler.objects.get(key)
        if payload is None:
            return self._send(404, b'{"message":"not found"}')
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class SupabaseStorageHttpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        StorageContractHandler.objects = {}
        StorageContractHandler.requests_seen = []
        StorageContractHandler.forced_status = None
        StorageContractHandler.get_delay_seconds = 0.0
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), StorageContractHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        StorageContractHandler.objects = {}
        StorageContractHandler.requests_seen = []
        StorageContractHandler.forced_status = None
        StorageContractHandler.get_delay_seconds = 0.0

    def make_store(self):
        # The production adapter intentionally requires HTTPS. Construct the
        # instance directly so only this loopback test uses plain HTTP.
        from urllib.request import urlopen
        store = object.__new__(SupabaseStorageArtifactStore)
        store._base_url = self.base_url
        store._key = "local-contract-secret"
        store.bucket = "yj64-private-artifacts"
        store.timeout_seconds = 3.0
        store.max_upload_bytes = 1024 * 1024
        store._opener = urlopen
        return store

    def test_real_http_upload_download_and_idempotent_retry(self):
        store = self.make_store()
        payload = json.dumps({"artifact": "round-trip"}, sort_keys=True).encode()
        ref = store.put(
            namespace="integration-smoke/task-1",
            content=payload,
            content_type="application/json",
        )
        self.assertEqual(store.get(ref), payload)
        self.assertEqual(store.put(
            namespace="integration-smoke/task-1",
            content=payload,
            content_type="application/json",
        ), ref)
        self.assertEqual(store.get(ref), payload)

        digest = hashlib.sha256(payload).hexdigest()
        expected_key = f"yj64-private-artifacts/integration-smoke/task-1/{digest}"
        self.assertEqual(
            StorageContractHandler.requests_seen,
            [
                ("POST", expected_key, "false"),
                ("GET", expected_key, None),
                ("POST", expected_key, "false"),
                ("GET", expected_key, None),
                ("GET", expected_key, None),
            ],
        )


    def test_upload_rejects_unauthorized_and_server_errors(self):
        unauthorized = self.make_store()
        unauthorized._key = "wrong-local-secret"
        with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
            unauthorized.put(
                namespace="failures",
                content=b"secret",
                content_type="text/plain",
            )

        StorageContractHandler.forced_status = 503
        with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
            self.make_store().put(
                namespace="failures",
                content=b"retry later",
                content_type="text/plain",
            )

    def test_download_rejects_unauthorized_and_missing_objects(self):
        store = self.make_store()
        payload = b"known artifact"
        ref = store.put(
            namespace="failures",
            content=payload,
            content_type="text/plain",
        )

        unauthorized = self.make_store()
        unauthorized._key = "wrong-local-secret"
        with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
            unauthorized.get(ref)

        missing_ref = ref.rsplit("/", 1)[0] + "/" + ("0" * 64)
        with self.assertRaisesRegex(RuntimeError, "HTTP 404"):
            store.get(missing_ref)

    def test_download_timeout_is_propagated_without_returning_partial_data(self):
        from urllib.error import URLError
        store = self.make_store()
        payload = b"slow artifact"
        ref = store.put(
            namespace="failures",
            content=payload,
            content_type="text/plain",
        )
        store.timeout_seconds = 0.05
        StorageContractHandler.get_delay_seconds = 0.25
        with self.assertRaises((TimeoutError, URLError, OSError)):
            store.get(ref)


if __name__ == "__main__":
    unittest.main()
