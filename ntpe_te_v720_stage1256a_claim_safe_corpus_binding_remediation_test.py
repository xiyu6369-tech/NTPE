from __future__ import annotations

import hashlib
import json
from tools.generate_te_v720_stage1256a_claim_safe_corpus_binding_remediation import (
    CLAIM, EXPECTED_CLAIM_SHA256, build_artifacts,
)

def test_stage1256a_root_acceptance() -> None:
    before = CLAIM.read_bytes(); first = build_artifacts(); second = build_artifacts()
    assert first == second and CLAIM.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == EXPECTED_CLAIM_SHA256
    summary = json.loads(next(data for path, data in first.items() if path.name == "remediation_summary.json"))
    assert summary["provider_requests_added"] == summary["network_requests_added"] == 0
    assert summary["activation_gate"] == "translation_quality_integration_ready_for_controlled_canary"

if __name__ == "__main__":
    test_stage1256a_root_acceptance(); print("TE_V720_STAGE1256A_ROOT_ACCEPTANCE=PASS")
