from __future__ import annotations
from pathlib import Path
from core.prompt_verification_canary_stage1257.framework import AUTHORIZATION_TOKEN, Stage1257Config, build_preflight
ROOT = Path(__file__).resolve().parents[2]
def test_stage1257_exact_binding_and_claim_safe_order() -> None:
    result, plan = build_preflight(ROOT, Stage1257Config("offline-integration", AUTHORIZATION_TOKEN), clean_override=True)
    assert result["status"] == "PASS"
    assert plan["canonical_id"] == "canary-001-character-honorific"
    assert result["ordered_steps"][-1]["name"] == "stage1257_claim_eligibility_validation"
    assert result["claim_created"] is False and result["provider_requests"] == 0
