from __future__ import annotations

from pathlib import Path

from core.shared.evidence import canonical_json_bytes

from .errors import GovernanceConsumptionError
from .loader import load_governance_baseline, sha256_bytes
from .models import GovernanceConsumptionAuditResult
from .verifier import verify_governance_baseline


VERIFIED = "governance_baseline_consumption_verified"
REJECTED = "governance_baseline_consumption_rejected"
INVALID = "governance_baseline_consumption_invalid"


def _fingerprint(payload: dict[str, object]) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def _result(status: str, violations: tuple[str, ...], evidence: tuple[str, ...]) -> GovernanceConsumptionAuditResult:
    rejected = set(violations)
    verified = status == VERIFIED
    values: dict[str, object] = {
        "status": status,
        "baseline_verified": verified,
        "manifest_hashes_verified": verified or not any("manifest" in item or "required_file" in item for item in rejected),
        "capability_registry_verified": verified or not any("capability" in item for item in rejected),
        "dependency_graph_verified": verified or not any("dependency" in item for item in rejected),
        "taxonomy_verified": verified or not any("taxonomy" in item for item in rejected),
        "claim_ledger_verified": verified or not any("claim" in item for item in rejected),
        "production_hook_count_verified": verified or "production_hook_count_changed" not in rejected,
        "authorization_state_verified": verified or not any("authorization" in item for item in rejected),
        "violations": list(sorted(violations)),
        "evidence": list(sorted(evidence)),
    }
    return GovernanceConsumptionAuditResult(
        status=status,
        baseline_verified=bool(values["baseline_verified"]),
        manifest_hashes_verified=bool(values["manifest_hashes_verified"]),
        capability_registry_verified=bool(values["capability_registry_verified"]),
        dependency_graph_verified=bool(values["dependency_graph_verified"]),
        taxonomy_verified=bool(values["taxonomy_verified"]),
        claim_ledger_verified=bool(values["claim_ledger_verified"]),
        production_hook_count_verified=bool(values["production_hook_count_verified"]),
        authorization_state_verified=bool(values["authorization_state_verified"]),
        violations=tuple(sorted(violations)),
        evidence=tuple(sorted(evidence)),
        deterministic_fingerprint=_fingerprint(values),
    )


def audit_governance_baseline_consumption(
    root: str | Path,
    source_manifest_path: str = "manifests/lcr_batch110_governance_freeze_manifest.json",
) -> GovernanceConsumptionAuditResult:
    try:
        reference, payload = load_governance_baseline(root, source_manifest_path)
        violations, evidence = verify_governance_baseline(reference, payload, root)
        return _result(REJECTED if violations else VERIFIED, violations, evidence)
    except GovernanceConsumptionError as exc:
        return _result(exc.status, (exc.code,), ())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _result(INVALID, (f"unexpected_input_error:{type(exc).__name__}",), ())
