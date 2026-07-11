from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightContract, RuntimeSafeHookPreflightGuard


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration preflight secret"


def test_stage362_runtime_safe_hook_preflight_guard_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        contract = RuntimeSafeHookPreflightContract().build_contract()
        guard = RuntimeSafeHookPreflightGuard()
        request = {
            "request_type": "safe_hook_preflight",
            "runtime_id": "integration-362",
            "source_text": SECRET_TEXT,
            "chunks": [SECRET_TEXT],
        }
        enabled_flag = {"enabled": True, "source": "config", "reason": "config_enabled"}

        blocked = guard.guard(request=request, contract=contract, flag_state={"enabled": False})
        allowed = guard.guard(request=request, contract=contract, flag_state=enabled_flag)

        assert blocked["reason"] == "runtime_integration_disabled"
        assert blocked["preflight_status"] == "blocked"
        assert allowed["reason"] == "preflight_allowed"
        assert allowed["preflight_status"] == "allowed"
        assert guard.is_allowed(allowed) is True
        assert guard.validate_guard_result(blocked)["valid"] is True
        assert guard.validate_guard_result(allowed)["valid"] is True
        assert SECRET_TEXT not in str(allowed)
        assert "source_text" not in allowed["request_summary"]["keys"]
        assert "chunks" not in allowed["request_summary"]["keys"]

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
