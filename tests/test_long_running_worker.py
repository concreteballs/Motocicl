import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_motocicl_worker.py"
SPEC = importlib.util.spec_from_file_location("run_motocicl_worker", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FakeRunner:
    worker_id = "test-worker"

    def __init__(self, results):
        self.results = iter(results)
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return next(self.results)


def test_run_forever_processes_tasks_and_stops_cleanly():
    runner = FakeRunner([
        {"status": "completed", "task_id": 1},
        {"status": "idle"},
    ])
    stop = {"value": False}
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        stop["value"] = True

    result = MODULE.run_forever(
        runner,
        poll_seconds=2,
        stop_requested=lambda: stop["value"],
        sleep=fake_sleep,
    )

    assert result == 0
    assert runner.calls == 2
    assert sleeps == [1.0]


def test_run_forever_does_not_sleep_after_non_idle_result():
    runner = FakeRunner([{"status": "completed", "task_id": 2}])
    stop = {"value": False}
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        stop["value"] = True

    # Stop after the first task without requiring a real timer.
    original_run_once = runner.run_once

    def run_once_and_stop():
        result = original_run_once()
        stop["value"] = True
        return result

    runner.run_once = run_once_and_stop
    result = MODULE.run_forever(
        runner,
        poll_seconds=1,
        stop_requested=lambda: stop["value"],
        sleep=fake_sleep,
    )

    assert result == 0
    assert sleeps == []


@pytest.mark.parametrize("poll_seconds", [0, -1, 301])
def test_run_forever_rejects_unbounded_poll_interval(poll_seconds):
    with pytest.raises(ValueError):
        MODULE.run_forever(FakeRunner([]), poll_seconds=poll_seconds)
