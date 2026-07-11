from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationFeatureFlag, RuntimeOptInHookContract, RuntimeOptInHookGuard


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "integration hook guard secret"


def test_stage342_runtime_optin_hook_guard_boundaries_without_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        flag = RuntimeIntegrationFeatureFlag()
        contract = RuntimeOptInHookContract().build_contract()
        guard = RuntimeOptInHookGuard()
        request = {
            "caller": "translation_runtime",
            "runtime_id": "integration-342",
            "source_text": SECRET_TEXT,
            "chunks": [SECRET_TEXT],
        }

        blocked = guard.guard(request=request, contract=contract, flag_state=flag.resolve())
        allowed = guard.guard(
            request=request,
            contract=contract,
            flag_state=flag.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"}),
        )
        wrong_caller = guard.guard(
            request={**request, "caller": "provider_runtime"},
            contract=contract,
            flag_state=flag.resolve(env={"NTPE_RUNTIME_SCHEDULER_INTEGRATION": "enabled"}),
        )

        assert blocked["reason"] == "runtime_integration_disabled"
        assert blocked["blocked"] is True
        assert allowed["reason"] == "hook_allowed"
        assert guard.is_allowed(allowed) is True
        assert allowed["request_summary"]["runtime_id"] == "integration-342"
        assert allowed["request_summary"]["chunk_count"] == 1
        assert wrong_caller["reason"] == "invalid_caller"

        for result in (blocked, allowed, wrong_caller):
            assert guard.validate_guard_result(result)["valid"] is True
            assert result["safety_boundaries"]["provider_runtime"] == "external"
            assert result["safety_boundaries"]["http_client"] == "forbidden"
            assert result["safety_boundaries"]["api_key"] == "forbidden"
            assert result["safety_boundaries"]["launcher_flow"] == "unchanged"
            assert result["safety_boundaries"]["translation_runtime_flow"] == "unchanged"
            assert result["safety_boundaries"]["real_translation"] == "forbidden"
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
