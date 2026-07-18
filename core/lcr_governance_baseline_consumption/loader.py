from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.shared.evidence import canonical_json_bytes

from .errors import GovernanceBaselineInvalidError, GovernanceBaselineRejectedError
from .models import GovernanceBaselineReference


DEFAULT_SOURCE_MANIFEST = "manifests/lcr_batch110_governance_freeze_manifest.json"
EXPECTED_SOURCE_MANIFEST_SHA256 = "16148eb7543d877a4544f4bae884987d0f4d14e74873736f9fee0f9d9b4da213"
EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_BATCH_ID = "11.0"
EXPECTED_ACTIVATION_GATE = "lcr_governance_baseline_frozen"
TAXONOMY_PATH = "audits/legacy_capability_recovery/batch10_9/LCR_BATCH109_TAXONOMY_REPORT.json"
CLAIM_LEDGER_PATH = "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json"
AUTHORIZATION_FIELDS = (
    "active_production_authorized",
    "automatic_rollout_authorized",
    "production_integration_authorized",
    "formal_output_replacement_authorized",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_payload_hash(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GovernanceBaselineInvalidError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except GovernanceBaselineInvalidError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GovernanceBaselineInvalidError("source_manifest_invalid_json") from exc
    if not isinstance(value, dict):
        raise GovernanceBaselineInvalidError("source_manifest_not_object")
    return value


def resolve_allowed_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise GovernanceBaselineInvalidError("invalid_relative_path")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise GovernanceBaselineInvalidError("path_traversal_rejected")
    candidate = root.joinpath(*rel.parts)
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise GovernanceBaselineInvalidError("symlink_escape_rejected")
    try:
        candidate.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise GovernanceBaselineInvalidError(f"required_file_unavailable:{relative}") from exc
    if not candidate.is_file():
        raise GovernanceBaselineInvalidError(f"required_file_unavailable:{relative}")
    return candidate


def load_governance_baseline(
    root: str | Path,
    source_manifest_path: str = DEFAULT_SOURCE_MANIFEST,
) -> tuple[GovernanceBaselineReference, dict[str, Any]]:
    base = Path(root).resolve(strict=True)
    if source_manifest_path != DEFAULT_SOURCE_MANIFEST:
        raise GovernanceBaselineInvalidError("alternate_source_manifest_rejected")
    source = resolve_allowed_file(base, source_manifest_path)
    raw = source.read_bytes()
    source_sha = sha256_bytes(raw)
    if source_sha != EXPECTED_SOURCE_MANIFEST_SHA256:
        raise GovernanceBaselineRejectedError("source_manifest_hash_mismatch")
    payload = load_json_bytes(raw)
    if raw != canonical_json_bytes(payload):
        raise GovernanceBaselineInvalidError("source_manifest_not_canonical")
    if payload.get("governance_schema_version") != EXPECTED_SCHEMA_VERSION:
        raise GovernanceBaselineInvalidError("source_schema_mismatch")
    if payload.get("batch") != EXPECTED_BATCH_ID:
        raise GovernanceBaselineInvalidError("source_batch_mismatch")
    if payload.get("activation_gate") != EXPECTED_ACTIVATION_GATE:
        raise GovernanceBaselineRejectedError("source_activation_gate_mismatch")

    child_hashes = payload.get("child_manifest_hashes")
    capabilities = payload.get("capabilities")
    graph = payload.get("dependency_graph")
    frozen_hashes = payload.get("frozen_evidence_hashes")
    authorization = payload.get("production_boundaries")
    if not isinstance(child_hashes, dict) or not isinstance(capabilities, list):
        raise GovernanceBaselineInvalidError("source_manifest_schema_invalid")
    if not isinstance(graph, dict) or not isinstance(frozen_hashes, dict) or not isinstance(authorization, dict):
        raise GovernanceBaselineInvalidError("source_manifest_schema_invalid")
    if TAXONOMY_PATH not in frozen_hashes or CLAIM_LEDGER_PATH not in frozen_hashes:
        raise GovernanceBaselineInvalidError("frozen_evidence_reference_missing")
    if set(authorization) != set(AUTHORIZATION_FIELDS):
        raise GovernanceBaselineInvalidError("authorization_schema_invalid")

    reference = GovernanceBaselineReference(
        schema_version=EXPECTED_SCHEMA_VERSION,
        batch_id=EXPECTED_BATCH_ID,
        activation_gate=EXPECTED_ACTIVATION_GATE,
        source_manifest_path=source_manifest_path,
        source_manifest_sha256=source_sha,
        child_manifest_hashes=MappingProxyType(dict(sorted(child_hashes.items()))),
        capability_registry_hash=canonical_payload_hash(capabilities),
        dependency_graph_hash=canonical_payload_hash(graph),
        taxonomy_hash=frozen_hashes[TAXONOMY_PATH],
        claim_ledger_hash=frozen_hashes[CLAIM_LEDGER_PATH],
        production_hook_count=payload.get("production_hook_count"),
        authorization_state=MappingProxyType({key: authorization[key] for key in AUTHORIZATION_FIELDS}),
    )
    return reference, payload
