"""Long-running Motocicl worker for the currently implemented CI task handlers.

This process intentionally handles only prepare_ci_fix and generate_ci_patch.
It does not claim to run the full autonomous engineering cycle or Council
Gateway tasks. Scale by starting additional identical processes; PostgreSQL
leases coordinate claims across processes.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable

PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from motocicl.automation.ci_fix_proposals import process_ci_fix_proposal
from motocicl.automation.ci_log_analysis import GEMINI_MODEL, GEMINI_PROFILE
from motocicl.automation.ci_patch_generation import process_ci_patch_generation
from motocicl.automation.gemini_adapter import GeminiGenerateContentAdapter
from motocicl.automation.postgres_store import PostgresCycleStore
from motocicl.automation.supabase_storage import SupabaseStorageArtifactStore
from motocicl.automation.worker import WorkerRunner

SUPPORTED_TASK_TYPES = ("prepare_ci_fix", "generate_ci_patch")


def _required_environment() -> None:
    required = ("YJ64_DATABASE_URL", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    missing = [key for key in required if not os.environ.get(key, "").strip()]
    if missing:
        raise RuntimeError("missing_required_environment:" + ",".join(missing))


def _build_runner() -> WorkerRunner:
    _required_environment()
    store = PostgresCycleStore(os.environ["YJ64_DATABASE_URL"])
    artifacts = SupabaseStorageArtifactStore.from_environment(
        bucket="yj64-private-artifacts",
        max_upload_bytes=6 * 1024 * 1024,
    )

    handlers = {
        "prepare_ci_fix": lambda task, context: process_ci_fix_proposal(
            task, context, artifact_store=artifacts
        )
    }

    # Patch generation is enabled only when its explicit zero-cost budget guard
    # passes. The profile is configuration, not a secret; no generation occurs
    # during startup or readiness checks.
    if os.environ.get("MOTOCICL_ENABLE_ZERO_COST_PATCH_WORKER", "").lower() == "true":
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            raise RuntimeError("patch_worker_enabled_without_gemini_api_key")
        store.set_provider_limit_profile(
            GEMINI_PROFILE,
            capacity_scope="gemini-free-tier-yj64-account",
            profile_source="operator_config",
        )
        limits = (store.get_cycle_usage().get("limits") or {})
        try:
            daily = Decimal(str(limits.get("daily_cost_usd")))
            monthly = Decimal(str(limits.get("monthly_cost_usd")))
        except (InvalidOperation, TypeError):
            raise RuntimeError("explicit_zero_cost_budget_required") from None
        if daily != 0 or monthly != 0:
            raise RuntimeError("zero_cost_budget_guard_rejected")
        adapter = GeminiGenerateContentAdapter(
            model=GEMINI_MODEL,
            limit_profile=GEMINI_PROFILE,
            artifact_store=artifacts,
        )
        handlers["generate_ci_patch"] = lambda task, context: process_ci_patch_generation(
            task, context, adapter=adapter, artifact_store=artifacts
        )

    worker_id = os.environ.get("MOTOCICL_WORKER_ID", "").strip()
    if not worker_id:
        worker_id = f"motocicl-{socket.gethostname()}-{os.getpid()}"
    lease_seconds = int(os.environ.get("MOTOCICL_LEASE_SECONDS", "600"))
    poll_seconds = float(os.environ.get("MOTOCICL_POLL_SECONDS", "5"))
    if not 30 <= lease_seconds <= 3600:
        raise RuntimeError("MOTOCICL_LEASE_SECONDS_must_be_30_to_3600")
    if not 1 <= poll_seconds <= 300:
        raise RuntimeError("MOTOCICL_POLL_SECONDS_must_be_1_to_300")

    return WorkerRunner(
        store,
        worker_id=worker_id,
        handlers=handlers,
        lease_seconds=lease_seconds,
        recovery_limit=100,
        allowed_task_types=list(handlers),
    )


def run_forever(
    runner: WorkerRunner,
    *,
    poll_seconds: float = 5,
    stop_requested: Callable[[], bool] = lambda: False,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Run one leased task per iteration; idle polling is bounded and stoppable."""
    if not 1 <= poll_seconds <= 300:
        raise ValueError("poll_seconds must be between 1 and 300")
    while not stop_requested():
        result = runner.run_once()
        status = result.get("status", "unknown")
        print(json.dumps({
            "event": "worker.iteration",
            "status": status,
            "task_id": result.get("task_id"),
            "worker": runner.worker_id,
        }, separators=(",", ":"), default=str), flush=True)
        if status == "idle":
            # Sleep in short slices so SIGTERM is acknowledged promptly.
            remaining = poll_seconds
            while remaining > 0 and not stop_requested():
                interval = min(1.0, remaining)
                sleep(interval)
                remaining -= interval
    print(json.dumps({"event": "worker.stopped", "worker": runner.worker_id}), flush=True)
    return 0


def main() -> int:
    stopping = False

    def request_stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    try:
        runner = _build_runner()
        poll_seconds = float(os.environ.get("MOTOCICL_POLL_SECONDS", "5"))
        print(json.dumps({
            "event": "worker.started",
            "worker": runner.worker_id,
            "task_types": sorted(runner.handlers),
            "mode": "long_running",
        }), flush=True)
        return run_forever(
            runner, poll_seconds=poll_seconds,
            stop_requested=lambda: stopping,
        )
    except Exception as exc:
        # Do not print exception messages: they may contain connection details.
        print(json.dumps({
            "event": "worker.start_failed",
            "error_type": type(exc).__name__,
        }), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
