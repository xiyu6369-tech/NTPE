from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeOptInHookMockBridge


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "hook bridge secret text"


def test_runtime_optin_hook_mock_bridge_paths() -> None:
    bridge = RuntimeOptInHookMockBridge()
    valid_request = {
        "caller": "translation_runtime",
        "runtime_id": "runtime-343",
        "request_type": "hook_bridge",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    default_blocked = bridge.run(request=valid_request)
    wrong_caller = bridge.run(
        request={**valid_request, "caller": "launcher"},
        config={"runtime_scheduler_integration_enabled": True},
    )
    completed = bridge.run(request=valid_request, config={"runtime_scheduler_integration_enabled": True})

    assert default_blocked["status"] == "hook_blocked"
    assert default_blocked["blocked"] is True
    assert default_blocked["orchestrator_result"] == {}
    assert default_blocked["runtime_report"] == {}
    assert default_blocked["export_outputs"] == {}
    assert default_blocked["hook_status"]["mode"] == "blocked"

    assert wrong_caller["status"] == "hook_blocked"
    assert wrong_caller["hook_guard_result"]["reason"] == "invalid_caller"
    assert wrong_caller["orchestrator_result"] == {}

    assert completed["status"] == "hook_mock_completed"
    assert completed["allowed"] is True
    assert completed["orchestrator_result"]["status"] == "mock_completed"
    assert completed["integration_status"]["mode"] == "mock"
    assert completed["integration_status"]["executed"] is False
    assert completed["integration_status"]["real_translation"] is False
    assert completed["runtime_report"]["mode"] == "mock"
    assert completed["export_outputs"]["mode"] == "mock"
    assert completed["export_outputs"]["merged_text"] == ""
    assert completed["export_outputs"]["chunk_results"] == []

    for result in (default_blocked, wrong_caller, completed):
        assert SECRET_TEXT not in str(result)
        assert bridge.validate_result(result)["valid"] is True


def test_runtime_optin_hook_mock_bridge_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        bridge = RuntimeOptInHookMockBridge()
        result = bridge.run(
            request={"caller": "translation_runtime", "text": SECRET_TEXT},
            config={"runtime_scheduler_integration_enabled": True},
        )

        assert result["status"] == "hook_mock_completed"
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
    test_runtime_optin_hook_mock_bridge_paths()
    test_runtime_optin_hook_mock_bridge_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.4 Stage-3.4.3 Runtime Opt-in Hook Mock Bridge PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
