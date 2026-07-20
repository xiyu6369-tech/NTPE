from __future__ import annotations
from pathlib import Path
from core.prompt_verification_canary_stage1257.framework import AUTHORIZATION_TOKEN, Stage1257Config, build_preflight
ROOT = Path(__file__).resolve().parent
def test_stage1257_root_acceptance() -> None:
    result, plan = build_preflight(ROOT, Stage1257Config("offline-root", AUTHORIZATION_TOKEN), clean_override=True)
    assert result["status"] == "PASS" and plan is not None
    assert result["claim_created"] is False and result["provider_requests"] == 0
if __name__ == "__main__": test_stage1257_root_acceptance(); print("TE_V720_STAGE1257_ROOT_ACCEPTANCE=PASS")
