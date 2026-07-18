from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.lcr_governance_baseline_consumption import (
    VERIFIED,
    audit_governance_baseline_consumption,
    load_governance_baseline,
)
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "manifests/lcr_batch110_governance_freeze_manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_consumes_real_batch110_frozen_artifacts_without_modifying_them():
    before = _sha(BASELINE)
    result = audit_governance_baseline_consumption(ROOT)
    after = _sha(BASELINE)
    assert before == after == "16148eb7543d877a4544f4bae884987d0f4d14e74873736f9fee0f9d9b4da213"
    assert result.status == VERIFIED
    assert result.violations == ()
    assert all((
        result.baseline_verified,
        result.manifest_hashes_verified,
        result.capability_registry_verified,
        result.dependency_graph_verified,
        result.taxonomy_verified,
        result.claim_ledger_verified,
        result.production_hook_count_verified,
        result.authorization_state_verified,
    ))


def test_reference_matches_frozen_counts_claim_and_authorizations():
    reference, payload = load_governance_baseline(ROOT)
    assert len(payload["capabilities"]) == 18
    assert payload["production_hook_count"] == reference.production_hook_count == 1
    assert all(value is False for value in reference.authorization_state.values())
    claim = json.loads((ROOT / "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json").read_text(encoding="utf-8"))
    assert claim["authorization_consumed"] is True
    assert claim["additional_execution_allowed"] is False
    assert claim["response_status_classification"] == "timeout"


def test_audit_is_canonical_deterministic_and_has_no_sensitive_payload():
    values = [audit_governance_baseline_consumption(ROOT).to_dict() for _ in range(3)]
    encoded = [canonical_json_bytes(value) for value in values]
    assert encoded[0] == encoded[1] == encoded[2]
    forbidden = (b"api_key", b"provider_payload", b"raw_prompt", b"response_body", b"source_text")
    assert not any(item in encoded[0].lower() for item in forbidden)


def test_consumption_layer_has_no_provider_network_or_runtime_hook_imports():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "core/lcr_governance_baseline_consumption").glob("*.py"))
    ).lower()
    assert "requests." not in source
    assert "httpx" not in source
    assert "urllib.request" not in source
    assert "provider_manager" not in source
    assert "run_read_only_lcr_shadow_hook(package)" not in source


def test_batch111_manifest_and_evidence_are_canonical_complete_and_hash_valid():
    manifest = ROOT / "manifests/lcr_batch111_governance_baseline_consumption_audit_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest.read_bytes() == canonical_json_bytes(payload)
    assert payload["activation_gate"] == VERIFIED
    assert (payload["capability_count"], payload["taxonomy_count"], payload["production_hook_count"]) == (18, 19, 1)
    assert all(value is False for value in payload["authorization_state"].values())
    for section in ("source_hashes", "test_hashes", "evidence_hashes"):
        for relative, expected in payload[section].items():
            assert _sha(ROOT / relative) == expected, relative
    evidence = json.loads((ROOT / payload["evidence_files"][0]).read_text(encoding="utf-8"))
    assert evidence["audit_status"] == VERIFIED
    assert evidence["provider_requests_added"] == evidence["network_requests_added"] == 0
    assert all(evidence[name] is False for name in ("runtime_changed", "provider_changed", "prompt_changed", "resume_changed", "output_changed", "active_integration"))
