import contextlib
import io
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


class SupabaseIntegrationSmokeScriptTests(unittest.TestCase):
    def test_requires_all_live_secrets_before_connecting(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "verify_supabase_integration.py"
        namespace = runpy.run_path(str(script))
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(stderr):
            result = namespace["main"]()
        self.assertEqual(result, 2)
        self.assertIn("YJ64_DATABASE_URL", stderr.getvalue())
        self.assertIn("SUPABASE_URL", stderr.getvalue())
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
