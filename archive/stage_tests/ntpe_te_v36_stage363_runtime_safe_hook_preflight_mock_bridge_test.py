from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightMockBridge


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "safe preflight secret text"


class SpyDisabledTrialBridge:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, request=None, config=None, env=None):
        self.calls += 1
        return {
            "status": "trial_mock_completed",
            "allowed": True,
            "blocked": False,
            "trial_guard_result": {"allowed": True, "blocked": False},
            "hook_bridge_result": {"status": "hook_mock_completed"},
            "trial_status": {"mode": "mock", "executed": False},
            "hook_status": {"mode": "mock", "executed": False},
            "integration_status": {
                "mode": "mock",
                "executed": False,
                "provider_runtime": "not_connected",
                "real_translation": False,
            },
            "runtime_report": {"mode": "mock", "jobs_total": 1, "jobs_done": 1, "jobs_failed": 0},
            "export_outputs": {
                "mode": "mock",
                "merged_text": "",
                "chunk_results": [],
                "failed_chunks": [],
            },
            "metadata": {"bridge": "spy_disabled_trial_bridge"},
        }


def _request() -> dict:
    return {
        "request_type": "safe_hook_preflight",
        "runtime_id": "runtime-363",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }


def test_runtime_safe_hook_preflight_mock_bridge_paths() -> None:
    spy = SpyDisabledTrialBridge()
    bridge = RuntimeSafeHookPreflightMockBridge(disabled_trial_bridge=spy)

    default_blocked = bridge.run(request=_request())

    assert default_blocked["status"] == "preflight_blocked"
    assert default_blocked["blocked"] is True
    assert default_blocked["disabled_trial_result"] == {}
    assert default_blocked["runtime_report"] == {}
    assert default_blocked["export_outputs"] == {}
    assert default_blocked["preflight_status"]["mode"] == "blocked"
    assert spy.calls == 0

    completed = bridge.run(request=_request(), config={"runtime_scheduler_integration_enabled": True})

    assert completed["status"] == "preflight_mock_completed"
    assert completed["allowed"] is True
    assert completed["disabled_trial_result"]["status"] == "trial_mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["mode"] == "mock"
    assert completed["export_outputs"]["mode"] == "mock"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []
    assert spy.calls == 1

    for result in (default_blocked, completed):
        assert SECRET_TEXT not in str(result)
        assert bridge.validate_result(result)["valid"] is True


def test_runtime_safe_hook_preflight_mock_bridge_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeSafeHookPreflightMockBridge()
        result = bridge.run(
            request={"request_type": "safe_hook_preflight", "runtime_id": "runtime-363", "text": SECRET_TEXT},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "preflight_mock_completed"
        assert result["disabled_trial_result"]["status"] == "trial_mock_completed"
        assert result["integration_status"]["executed"] is False
        assert result["integration_status"]["real_translation"] is False
        assert SECRET_TEXT not in str(result)
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_safe_hook_preflight_mock_bridge_paths()
    test_runtime_safe_hook_preflight_mock_bridge_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.6 Stage-3.6.3 Runtime Safe Hook Preflight Mock Bridge PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
