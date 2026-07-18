from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lcr_governance_baseline_consumption import (
    VERIFIED,
    audit_governance_baseline_consumption,
    load_governance_baseline,
)
from core.shared.evidence import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_PATH = ROOT / "artifacts/lcr_batch111/governance_baseline_consumption_evidence.json"
MANIFEST_PATH = ROOT / "manifests/lcr_batch111_governance_baseline_consumption_audit_manifest.json"

SOURCE_FILES = (
    "core/lcr_governance_baseline_consumption/__init__.py",
    "core/lcr_governance_baseline_consumption/audit.py",
    "core/lcr_governance_baseline_consumption/errors.py",
    "core/lcr_governance_baseline_consumption/loader.py",
    "core/lcr_governance_baseline_consumption/models.py",
    "core/lcr_governance_baseline_consumption/verifier.py",
    "audits/legacy_capability_recovery/batch11_1/generate_lcr_batch111_audit.py",
    "docs/releases/lcr/LCR_BATCH111_GOVERNANCE_BASELINE_CONSUMPTION_AUDIT.md",
)
TEST_FILES = (
    "ntpe_lcr_batch111_governance_baseline_consumption_audit_test.py",
    "tests/unit/test_lcr_governance_baseline_consumption.py",
    "tests/integration/test_lcr_batch111_governance_baseline_consumption_audit.py",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(paths: tuple[str, ...]) -> dict[str, str]:
    return {relative: _sha(ROOT / relative) for relative in paths}


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload))


def main() -> int:
    reference, baseline = load_governance_baseline(ROOT)
    result = audit_governance_baseline_consumption(ROOT)
    if result.status != VERIFIED:
        raise SystemExit(f"Batch 11.1 audit rejected: {result.violations}")

    dependency_count = sum(len(items) for items in baseline["dependency_graph"].values())
    evidence = {
        "batch_id": "11.1",
        "schema_version": "1.0",
        "source_baseline": reference.source_manifest_path,
        "source_activation_gate": reference.activation_gate,
        "baseline_manifest_sha256": reference.source_manifest_sha256,
        "capability_count": len(baseline["capabilities"]),
        "dependency_count": dependency_count,
        "taxonomy_count": 19,
        "production_hook_count": reference.production_hook_count,
        "consumed_claims": 1,
        "authorization_state": dict(reference.authorization_state),
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "runtime_changed": False,
        "provider_changed": False,
        "prompt_changed": False,
        "resume_changed": False,
        "output_changed": False,
        "active_integration": False,
        "audit_status": result.status,
        "deterministic_fingerprint": result.deterministic_fingerprint,
    }
    _write(EVIDENCE_PATH, evidence)

    manifest = {
        "batch": "11.1",
        "schema_version": "1.0",
        "activation_gate": VERIFIED,
        "source_baseline": reference.source_manifest_path,
        "source_activation_gate": reference.activation_gate,
        "source_baseline_sha256": reference.source_manifest_sha256,
        "capability_count": 18,
        "dependency_count": dependency_count,
        "taxonomy_count": 19,
        "production_hook_count": 1,
        "consumed_claims": 1,
        "authorization_state": dict(reference.authorization_state),
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "runtime_behavior_changed": False,
        "provider_behavior_changed": False,
        "prompt_behavior_changed": False,
        "resume_behavior_changed": False,
        "output_behavior_changed": False,
        "active_integration": False,
        "retry_allowed": False,
        "fallback_allowed": False,
        "automatic_rollout_authorized": False,
        "formal_output_replacement_authorized": False,
        "source_files": list(SOURCE_FILES),
        "source_hashes": _hashes(SOURCE_FILES),
        "test_files": list(TEST_FILES),
        "test_hashes": _hashes(TEST_FILES),
        "evidence_files": [EVIDENCE_PATH.relative_to(ROOT).as_posix()],
        "evidence_hashes": {EVIDENCE_PATH.relative_to(ROOT).as_posix(): _sha(EVIDENCE_PATH)},
        "deterministic_fingerprint": result.deterministic_fingerprint,
    }
    _write(MANIFEST_PATH, manifest)
    print(json.dumps({
        "status": result.status,
        "evidence": EVIDENCE_PATH.relative_to(ROOT).as_posix(),
        "manifest": MANIFEST_PATH.relative_to(ROOT).as_posix(),
        "fingerprint": result.deterministic_fingerprint,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
