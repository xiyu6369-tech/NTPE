from __future__ import annotations
from pathlib import Path
from core.prompt_contract_verification_canary import CanaryConfig, execute_verification_canary

class _ForbiddenTransport:
    provenance = "real"
    def invoke(self, **_: object):
        raise AssertionError("Provider must not be invoked when preflight fails")

def test_preflight_failure_blocks_provider_and_writes_zero_request_summary() -> None:
    result = execute_verification_canary(CanaryConfig("offline", "invalid"), root=Path(__file__).resolve().parents[2], transport=_ForbiddenTransport())
    assert result["request_count"] == 0
    assert result["status"] == "preflight_failure_no_provider_request"
