from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.generate_te_v720_stage1256a_claim_safe_corpus_binding_remediation import CLAIM, EXPECTED_CLAIM_SHA256, build_artifacts

ROOT = Path(__file__).resolve().parents[2]

def test_historical_seal_identity_contract_and_zero_request_boundary() -> None:
    before = CLAIM.read_bytes(); artifacts = build_artifacts()
    assert hashlib.sha256(before).hexdigest() == EXPECTED_CLAIM_SHA256
    assert CLAIM.read_bytes() == before
    payloads = {path.name: json.loads(data) for path, data in artifacts.items()}
    assert payloads["corpus_identity_contract.json"]["logical_id"] == "canary-001"
    assert payloads["corpus_identity_contract.json"]["canonical_id"] == "canary-001-character-honorific"
    assert payloads["claim_lifecycle_validation.json"]["claim_replay_allowed"] is False
    assert payloads["remediation_summary.json"]["provider_requests_added"] == 0
    assert payloads["remediation_summary.json"]["network_requests_added"] == 0
    serialized = b"".join(artifacts.values()).lower()
    assert b"authorization:" not in serialized and b"api_key" not in serialized and b"bearer " not in serialized
