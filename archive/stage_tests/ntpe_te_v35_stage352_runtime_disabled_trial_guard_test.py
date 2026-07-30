from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeDisabledTrialContract,
    RuntimeDisabledTrialGuard,
    RuntimeIntegrationFeatureFlag,
)


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def _safe_contract() -> dict:
    return RuntimeDisabledTrialContract().build_contract(metadata={"profile": "disabled-trial-guard"})


def _enabled_flag() -> dict:
    return RuntimeIntegrationFeatureFlag().resolve(config={"runtime_scheduler_integration_enabled": True})


def _request() -> dict:
    return {
        "request_type": "disabled_trial",
        "runtime_id": "demo-352",
        "source_text": "raw source must not be copied",
        "chunks": ["raw chunk 1", "raw chunk 2"],
    }


def _assert_summary_is_safe(result: dict) -> None:
    summary = result["request_summary"]
    summary_text = repr(summary)
    assert "raw source must not be copied" not in summary_text
    assert "raw chunk 1" not in summary_text
    assert "raw chunk 2" not in summary_text
    assert "source_text" not in summary["keys"]
    assert "text" not in summary["keys"]
    assert "chunks" not in summary["keys"]
    assert summary["has_source_text"] is True
    assert summary["chunk_count"] == 2


def test_runtime_disabled_trial_guard_blocks_unsafe_requests_and_contracts() -> None:
    guard = RuntimeDisabledTrialGuard()
    contract = _safe_contract()
    enabled_flag = _enabled_flag()

    missing_request = guard.guard(request=None, contract=contract, flag_state=enabled_flag)
    assert missing_request["blocked"] is True
    assert missing_request["reason"] == "missing_request"
    assert guard.validate_guard_result(missing_request)["valid"] is True

    disabled_flag = RuntimeIntegrationFeatureFlag().resolve()
    disabled_result = guard.guard(request=_request(), contract=contract, flag_state=disabled_flag)
    assert disabled_result["blocked"] is True
    assert disabled_result["reason"] == "runtime_integration_disabled"
    assert guard.validate_guard_result(disabled_result)["valid"] is True

    bad_default = guard.guard(
        request=_request(),
        contract={**contract, "default_mode": "enabled"},
        flag_state=enabled_flag,
    )
    assert bad_default["blocked"] is True
    assert bad_default["reason"] == "unsafe_default_mode"

    bad_touch = guard.guard(
        request=_request(),
        contract={**contract, "runtime_touch_mode": "read"},
        flag_state=enabled_flag,
    )
    assert bad_touch["blocked"] is True
    assert bad_touch["reason"] == "unsafe_touch_mode"

    bad_translation = guard.guard(
        request=_request(),
        contract={**contract, "real_translation": True},
        flag_state=enabled_flag,
    )
    assert bad_translation["blocked"] is True
    assert bad_translation["reason"] == "real_translation_enabled"


def test_runtime_disabled_trial_guard_allows_safe_enabled_mock_trial() -> None:
    guard = RuntimeDisabledTrialGuard()
    result = guard.guard(request=_request(), contract=_safe_contract(), flag_state=_enabled_flag())

    assert result["allowed"] is True
    assert result["blocked"] is False
    assert result["reason"] == "trial_allowed"
    assert result["stage"] == "3.5.2"
    assert result["trial_status"] == "allowed"
    assert guard.is_allowed(result) is True
    assert guard.validate_guard_result(result)["valid"] is True
    assert result["safety_boundaries"] == {
        "provider_runtime": "forbidden",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
        "real_translation": "forbidden",
    }
    _assert_summary_is_safe(result)


def test_runtime_disabled_trial_guard_no_runtime_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_production_runtime = "core.production_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        guard = RuntimeDisabledTrialGuard()
        result = guard.guard(request=_request(), contract=_safe_contract(), flag_state=_enabled_flag())

        assert result["allowed"] is True
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
    test_runtime_disabled_trial_guard_blocks_unsafe_requests_and_contracts()
    test_runtime_disabled_trial_guard_allows_safe_enabled_mock_trial()
    test_runtime_disabled_trial_guard_no_runtime_side_effects()
    print("NTPE TE-v3.5 Stage-3.5.2 Runtime Disabled Trial Guard PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
