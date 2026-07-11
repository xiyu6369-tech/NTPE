from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import (
    RuntimeDisabledTrialContract,
    RuntimeDisabledTrialGuard,
    RuntimeIntegrationFeatureFlag,
)


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage352_runtime_disabled_trial_guard_boundaries_and_safe_summary() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        contract = RuntimeDisabledTrialContract().build_contract()
        flag = RuntimeIntegrationFeatureFlag().resolve(config={"runtime_scheduler_integration_enabled": True})
        request = {
            "request_type": "disabled_trial",
            "runtime_id": "integration-352",
            "text": "do not store this",
            "chunks": ["chunk source"],
        }
        guard = RuntimeDisabledTrialGuard()

        allowed = guard.guard(request=request, contract=contract, flag_state=flag)
        assert allowed["allowed"] is True
        assert allowed["reason"] == "trial_allowed"
        assert allowed["trial_status"] == "allowed"
        assert guard.validate_guard_result(allowed)["valid"] is True
        assert "do not store this" not in repr(allowed["request_summary"])
        assert "chunk source" not in repr(allowed["request_summary"])
        assert allowed["request_summary"]["keys"] == ["request_type", "runtime_id"]

        blocked = guard.guard(request=request, contract=contract, flag_state=RuntimeIntegrationFeatureFlag().resolve())
        assert blocked["blocked"] is True
        assert blocked["reason"] == "runtime_integration_disabled"
        assert guard.validate_guard_result(blocked)["valid"] is True

        bad_contract = {**contract, "provider_touch_mode": "connect"}
        unsafe = guard.guard(request=request, contract=bad_contract, flag_state=flag)
        assert unsafe["blocked"] is True
        assert unsafe["reason"] == "unsafe_touch_mode"

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key
