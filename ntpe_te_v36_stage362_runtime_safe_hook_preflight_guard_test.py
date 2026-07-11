from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeSafeHookPreflightContract, RuntimeSafeHookPreflightGuard


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "preflight guard secret"


def _enabled_flag() -> dict[str, object]:
    return {
        "enabled": True,
        "source": "config",
        "reason": "config_enabled",
        "stage": "3.3.2",
    }


def _request() -> dict[str, object]:
    return {
        "request_type": "safe_hook_preflight",
        "runtime_id": "demo-362",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT, "another secret"],
    }


def test_runtime_safe_hook_preflight_guard_blocking_and_allowed_paths() -> None:
    contract_builder = RuntimeSafeHookPreflightContract()
    contract = contract_builder.build_contract()
    guard = RuntimeSafeHookPreflightGuard(contract_builder=contract_builder)

    missing_request = guard.guard(request=None, contract=contract, flag_state=_enabled_flag())
    disabled_flag = guard.guard(request=_request(), contract=contract, flag_state={"enabled": False})
    unsafe_default = guard.guard(request=_request(), contract={**contract, "default_mode": "enabled"}, flag_state=_enabled_flag())
    unsafe_touch = guard.guard(request=_request(), contract={**contract, "runtime_touch_mode": "read"}, flag_state=_enabled_flag())
    unsafe_translation = guard.guard(request=_request(), contract={**contract, "real_translation": True}, flag_state=_enabled_flag())
    allowed = guard.guard(request=_request(), contract=contract, flag_state=_enabled_flag())

    assert missing_request["reason"] == "missing_request"
    assert disabled_flag["reason"] == "runtime_integration_disabled"
    assert unsafe_default["reason"] == "unsafe_default_mode"
    assert unsafe_touch["reason"] == "unsafe_touch_mode"
    assert unsafe_translation["reason"] == "real_translation_enabled"
    assert allowed["reason"] == "preflight_allowed"
    assert allowed["allowed"] is True
    assert allowed["blocked"] is False
    assert allowed["preflight_status"] == "allowed"
    assert guard.is_allowed(allowed) is True

    for result in (missing_request, disabled_flag, unsafe_default, unsafe_touch, unsafe_translation, allowed):
        assert guard.validate_guard_result(result)["valid"] is True


def test_runtime_safe_hook_preflight_guard_request_summary_and_safety() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        guard = RuntimeSafeHookPreflightGuard()
        result = guard.guard(request=_request(), flag_state=_enabled_flag())

        assert result["allowed"] is True
        assert result["request_summary"]["request_type"] == "safe_hook_preflight"
        assert result["request_summary"]["runtime_id"] == "demo-362"
        assert result["request_summary"]["chunk_count"] == 2
        assert result["request_summary"]["has_source_text"] is True
        assert "source_text" not in result["request_summary"]["keys"]
        assert "text" not in result["request_summary"]["keys"]
        assert "chunks" not in result["request_summary"]["keys"]
        assert SECRET_TEXT not in str(result)
        assert result["safety_boundaries"] == {
            "provider_runtime": "forbidden",
            "http_client": "forbidden",
            "api_key": "forbidden",
            "launcher_flow": "unchanged",
            "translation_runtime_flow": "unchanged",
            "real_translation": "forbidden",
        }

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("core.production_runtime" in sys.modules) == before_production_runtime
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_safe_hook_preflight_guard_blocking_and_allowed_paths()
    test_runtime_safe_hook_preflight_guard_request_summary_and_safety()
    print("NTPE TE-v3.6 Stage-3.6.2 Runtime Safe Hook Preflight Guard PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
