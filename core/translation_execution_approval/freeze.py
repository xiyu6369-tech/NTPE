from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_COMPONENT_NAME = "ntpe.translation_execution_governance"
_FREEZE_VERSION = "4.4"
_PACKAGE_SCHEMA = ("ntpe.translation_execution_package", "1.0")
_AUTHORIZATION_SCHEMA = (
    "ntpe.translation_execution_authorization_decision",
    "1.0",
)
_APPROVAL_SCHEMA = ("ntpe.translation_execution_approval_record", "1.0")
_ACTIVATION_GATE = "translation_execution_governance_frozen"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_RELATIVE_PATH = Path(
    "manifests/translation_execution_stage44_freeze_manifest.json"
)

_FROZEN_MODULES = (
    "core/translation_execution_approval/__init__.py",
    "core/translation_execution_approval/approver.py",
    "core/translation_execution_approval/errors.py",
    "core/translation_execution_approval/freeze.py",
    "core/translation_execution_approval/models.py",
    "core/translation_execution_approval/policy.py",
    "core/translation_execution_authorization/__init__.py",
    "core/translation_execution_authorization/errors.py",
    "core/translation_execution_authorization/evaluator.py",
    "core/translation_execution_authorization/models.py",
    "core/translation_execution_authorization/policy.py",
    "core/translation_execution_package/__init__.py",
    "core/translation_execution_package/builder.py",
    "core/translation_execution_package/errors.py",
    "core/translation_execution_package/models.py",
    "core/translation_execution_package/policy.py",
)

_PACKAGE_API = (
    "TranslationExecutionPackageBuilder",
    "TranslationExecutionPackage",
    "TranslationExecutionUnit",
    "ExecutionSourceReference",
    "ExecutionPackageFinding",
    "TranslationExecutionPackageError",
    "InvalidExecutionPackageInputError",
    "InvalidPreparationStateError",
    "ExecutionPackageConsistencyError",
    "ExecutionPackageInvariantError",
)
_AUTHORIZATION_API = (
    "TranslationExecutionAuthorizationEvaluator",
    "ExecutionAuthorizationDecision",
    "ExecutionAuthorizationFinding",
    "ExecutionAuthorizationPolicy",
    "TranslationExecutionAuthorizationError",
    "InvalidExecutionAuthorizationInputError",
    "InvalidExecutionPackageStateError",
    "ExecutionAuthorizationConsistencyError",
    "ExecutionAuthorizationPolicyError",
)
_APPROVAL_API = (
    "TranslationExecutionApprover",
    "ExplicitHumanApprovalRequest",
    "ExecutionApprovalRecord",
    "ExecutionApprovalFinding",
    "TranslationExecutionApprovalError",
    "InvalidExecutionApprovalInputError",
    "InvalidHumanApprovalRequestError",
    "ExecutionApprovalConsistencyError",
    "ExecutionApprovalScopeError",
    "ExecutionApprovalPolicyError",
)
_FREEZE_API = (
    "TranslationExecutionGovernanceFreezeMetadata",
    "TranslationExecutionGovernanceFreezeValidationResult",
    "TranslationExecutionGovernanceFreezeValidationError",
    "get_translation_execution_governance_freeze_metadata",
    "validate_translation_execution_governance_freeze",
)
_PUBLIC_API = _PACKAGE_API + _AUTHORIZATION_API + _APPROVAL_API + _FREEZE_API

_INVARIANTS = (
    "offline_only",
    "deterministic",
    "immutable_results",
    "canonical_json",
    "exact_utf8_sha256",
    "execution_package_chunk_mapping_one_to_one",
    "execution_package_reconstruction_exact",
    "execution_package_offsets_gap_free",
    "execution_package_offsets_non_overlapping",
    "execution_package_initial_attempt_count_zero",
    "execution_package_initial_provider_request_count_zero",
    "execution_package_translation_result_not_attached",
    "execution_package_authorization_flags_false",
    "authorization_default_denied",
    "authorization_requires_human_approval",
    "authorization_policy_cannot_be_relaxed",
    "authorization_package_validation_fail_closed",
    "authorization_tampering_rejected",
    "approval_request_caller_supplied",
    "approval_confirmation_token_required",
    "warning_acknowledgement_required",
    "approval_scope_exact",
    "approval_scope_not_auto_expanded",
    "approval_statement_not_persisted",
    "approval_statement_fingerprint_exact",
    "approval_record_package_bound",
    "approval_record_authorization_bound",
    "controlled_runtime_scope_requires_provider_translation_runtime_flags",
    "automatic_retry_never_authorized",
    "automatic_fallback_never_authorized",
    "output_replacement_never_authorized",
    "no_provider_execution",
    "no_network_execution",
    "no_translation_execution",
    "no_runtime_submission",
    "no_output_write",
    "no_production_hook",
    "production_integration_not_authorized",
)


class TranslationExecutionGovernanceFreezeValidationError(RuntimeError):
    """Raised when the Stage 4.4 governance baseline no longer validates."""


@dataclass(frozen=True)
class TranslationExecutionGovernanceFreezeMetadata:
    component_name: str
    freeze_version: str
    package_schema_name: str
    package_schema_version: str
    authorization_schema_name: str
    authorization_schema_version: str
    approval_schema_name: str
    approval_schema_version: str
    activation_gate: str
    frozen_modules: tuple[str, ...]
    public_api: tuple[str, ...]
    invariants: tuple[str, ...]
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    production_integration_authorized: bool


@dataclass(frozen=True)
class TranslationExecutionGovernanceFreezeValidationResult:
    valid: bool
    frozen_file_count: int
    public_api_count: int
    invariant_count: int
    activation_gate: str


_METADATA = TranslationExecutionGovernanceFreezeMetadata(
    component_name=_COMPONENT_NAME,
    freeze_version=_FREEZE_VERSION,
    package_schema_name=_PACKAGE_SCHEMA[0],
    package_schema_version=_PACKAGE_SCHEMA[1],
    authorization_schema_name=_AUTHORIZATION_SCHEMA[0],
    authorization_schema_version=_AUTHORIZATION_SCHEMA[1],
    approval_schema_name=_APPROVAL_SCHEMA[0],
    approval_schema_version=_APPROVAL_SCHEMA[1],
    activation_gate=_ACTIVATION_GATE,
    frozen_modules=_FROZEN_MODULES,
    public_api=_PUBLIC_API,
    invariants=_INVARIANTS,
    provider_execution_authorized=False,
    translation_execution_authorized=False,
    runtime_submission_authorized=False,
    automatic_retry_authorized=False,
    automatic_fallback_authorized=False,
    output_replacement_authorized=False,
    production_integration_authorized=False,
)

_RESULT = TranslationExecutionGovernanceFreezeValidationResult(
    valid=True,
    frozen_file_count=len(_FROZEN_MODULES),
    public_api_count=len(_PUBLIC_API),
    invariant_count=len(_INVARIANTS),
    activation_gate=_ACTIVATION_GATE,
)


def get_translation_execution_governance_freeze_metadata(
) -> TranslationExecutionGovernanceFreezeMetadata:
    """Return deterministic immutable Stage 4.4 freeze metadata."""
    return _METADATA


def validate_translation_execution_governance_freeze(
) -> TranslationExecutionGovernanceFreezeValidationResult:
    """Validate source, API, schema, and governance contracts without execution."""
    try:
        repository_root = Path(__file__).resolve().parents[2]
        manifest_path = repository_root / _MANIFEST_RELATIVE_PATH
        raw_manifest = manifest_path.read_bytes()
        if raw_manifest.startswith(b"\xef\xbb\xbf"):
            raise TranslationExecutionGovernanceFreezeValidationError(
                "Freeze manifest must not contain a BOM."
            )
        manifest_text = raw_manifest.decode("utf-8")
        manifest = json.loads(manifest_text)
        canonical = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if manifest_text not in {canonical, canonical + "\n"}:
            raise TranslationExecutionGovernanceFreezeValidationError(
                "Freeze manifest is not canonical JSON."
            )
        _validate_manifest_contract(manifest)
        _validate_public_api()
        _validate_source_inventory(repository_root, manifest)
        _validate_governance_contracts()
        return _RESULT
    except TranslationExecutionGovernanceFreezeValidationError:
        raise
    except Exception as error:
        raise TranslationExecutionGovernanceFreezeValidationError(
            f"Translation execution governance freeze validation failed: {error}"
        ) from error


def _validate_manifest_contract(manifest: dict[str, Any]) -> None:
    expected = {
        "component": _COMPONENT_NAME,
        "stage": _FREEZE_VERSION,
        "freeze_version": _FREEZE_VERSION,
        "activation_gate": _ACTIVATION_GATE,
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "translation_executions_added": 0,
        "runtime_submissions_added": 0,
        "output_writes_added": 0,
        "retry_executions_added": 0,
        "fallback_executions_added": 0,
        "production_hooks_added": 0,
        "production_integration_authorized": False,
    }
    for name, value in expected.items():
        if manifest.get(name) != value:
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Invalid freeze manifest field: {name}."
            )
    schemas = manifest.get("schemas")
    expected_schemas = {
        "package": list(_PACKAGE_SCHEMA),
        "authorization": list(_AUTHORIZATION_SCHEMA),
        "approval": list(_APPROVAL_SCHEMA),
    }
    if schemas != expected_schemas:
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen schema inventory drifted."
        )
    if tuple(manifest.get("public_api", ())) != _PUBLIC_API:
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen public API inventory drifted."
        )
    if tuple(manifest.get("invariants", ())) != _INVARIANTS:
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen invariant inventory drifted."
        )
    tests = manifest.get("validation_tests")
    if not isinstance(tests, list) or not tests or len(tests) != len(set(tests)):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Validation test inventory is invalid."
        )


def _validate_public_api() -> None:
    import core.translation_execution_approval as approval
    import core.translation_execution_authorization as authorization
    import core.translation_execution_package as package

    inventories = (
        (package, _PACKAGE_API),
        (authorization, _AUTHORIZATION_API),
        (approval, _APPROVAL_API + _FREEZE_API),
    )
    for module, expected in inventories:
        exports = tuple(module.__all__)
        if exports != expected or len(exports) != len(set(exports)):
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Public API inventory drifted: {module.__name__}."
            )
        for name in exports:
            value = getattr(module, name, None)
            if not name or name.startswith("_") or value is None:
                raise TranslationExecutionGovernanceFreezeValidationError(
                    f"Invalid public API export: {module.__name__}.{name}."
                )
            owner = getattr(value, "__module__", "")
            if owner and not owner.startswith(module.__name__):
                raise TranslationExecutionGovernanceFreezeValidationError(
                    f"Public API owner drifted: {module.__name__}.{name}."
                )
    if len(_PUBLIC_API) != len(set(_PUBLIC_API)):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Duplicate aggregate public API name detected."
        )


def _validate_source_inventory(
    repository_root: Path, manifest: dict[str, Any]
) -> None:
    entries = manifest.get("frozen_files")
    if not isinstance(entries, list):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen source inventory is missing."
        )
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen source paths are invalid or duplicated."
        )
    if tuple(paths) != _FROZEN_MODULES or paths != sorted(paths):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Frozen source inventory is incomplete, extra, or unsorted."
        )

    discovered = tuple(
        sorted(
            path.relative_to(repository_root).as_posix()
            for directory in (
                repository_root / "core" / "translation_execution_package",
                repository_root / "core" / "translation_execution_authorization",
                repository_root / "core" / "translation_execution_approval",
            )
            for path in directory.glob("*.py")
        )
    )
    if discovered != _FROZEN_MODULES:
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Formal Stage 4 source inventory drifted."
        )

    for entry in entries:
        relative = entry["path"]
        pure_path = PurePosixPath(relative)
        expected_hash = entry.get("sha256")
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or not relative.startswith("core/translation_execution_")
            or not relative.endswith(".py")
        ):
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Invalid frozen source path: {relative}."
            )
        if not isinstance(expected_hash, str) or not _HEX_64.fullmatch(expected_hash):
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Invalid frozen source hash: {relative}."
            )
        source_path = repository_root.joinpath(*pure_path.parts)
        if not source_path.is_file():
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Frozen source is missing: {relative}."
            )
        observed = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if observed != expected_hash:
            raise TranslationExecutionGovernanceFreezeValidationError(
                f"Frozen source hash mismatch: {relative}."
            )


def _validate_governance_contracts() -> None:
    from core.translation_execution_approval import models as approval_models
    from core.translation_execution_approval import policy as approval_policy
    from core.translation_execution_authorization import models as authorization_models
    from core.translation_execution_authorization import policy as authorization_policy
    from core.translation_execution_package import models as package_models
    from core.translation_execution_package import policy as package_policy

    if (
        (package_policy.SCHEMA_NAME, package_policy.SCHEMA_VERSION)
        != _PACKAGE_SCHEMA
        or package_policy.STRATEGY
        != "deterministic_offline_execution_package_v1"
        or package_policy.ACTIVATION_GATE
        != "translation_execution_package_prepared"
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Execution package schema contract drifted."
        )
    if (
        (authorization_policy.SCHEMA_NAME, authorization_policy.SCHEMA_VERSION)
        != _AUTHORIZATION_SCHEMA
        or authorization_policy.STRATEGY
        != "deterministic_fail_closed_authorization_v1"
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Authorization schema contract drifted."
        )
    if (
        (approval_policy.SCHEMA_NAME, approval_policy.SCHEMA_VERSION)
        != _APPROVAL_SCHEMA
        or approval_policy.STRATEGY
        != "explicit_human_scoped_execution_approval_v1"
        or approval_policy.ACTIVATION_GATE
        != "translation_execution_explicitly_approved"
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Approval schema contract drifted."
        )

    model_types = (
        package_models.ExecutionSourceReference,
        package_models.TranslationExecutionUnit,
        package_models.ExecutionPackageFinding,
        package_models.TranslationExecutionPackage,
        authorization_models.ExecutionAuthorizationPolicy,
        authorization_models.ExecutionAuthorizationFinding,
        authorization_models.ExecutionAuthorizationDecision,
        approval_models.ExplicitHumanApprovalRequest,
        approval_models.ExecutionApprovalFinding,
        approval_models.ExecutionApprovalRecord,
    )
    if any(
        not is_dataclass(model) or not model.__dataclass_params__.frozen
        for model in model_types
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Governance model immutability drifted."
        )

    package_defaults = package_policy.DEFAULT_POLICY
    if (
        package_defaults.unit_status != "prepared"
        or package_defaults.unit_attempt_count != 0
        or package_defaults.unit_provider_request_count != 0
        or package_defaults.unit_translation_result_attached is not False
        or any(package_defaults.authorization_flags.values())
        or "EXECUTION_NOT_AUTHORIZED" not in package_defaults.finding_codes
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Execution package default boundary drifted."
        )

    authorization_defaults = authorization_policy.DEFAULT_POLICY
    authorization_flags = (
        "provider_execution_authorized",
        "translation_execution_authorized",
        "runtime_submission_authorized",
        "automatic_retry_authorized",
        "automatic_fallback_authorized",
        "output_replacement_authorized",
    )
    if (
        any(getattr(authorization_defaults, name) for name in authorization_flags)
        or authorization_defaults.require_explicit_human_approval is not True
        or any(
            getattr(authorization_defaults, name)
            for name in authorization_policy.ALLOW_FLAG_NAMES
        )
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Default-denied authorization policy drifted."
        )

    if (
        approval_policy.CONFIRMATION_TOKEN
        != "APPROVE_CONTROLLED_TRANSLATION_EXECUTION"
        or approval_policy.WARNING_ACKNOWLEDGEMENT_TOKEN
        != "ACKNOWLEDGE_PACKAGE_WARNINGS"
        or approval_policy.APPROVAL_TYPES
        != ("single_unit", "selected_units", "full_package")
        or approval_policy.REQUIRED_REQUEST_FLAGS
        != (
            "approve_provider_execution",
            "approve_translation_execution",
            "approve_runtime_submission",
        )
        or approval_policy.PROHIBITED_REQUEST_FLAGS
        != (
            "approve_automatic_retry",
            "approve_automatic_fallback",
            "approve_output_replacement",
        )
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Explicit human approval policy drifted."
        )

    request_fields = tuple(
        field.name for field in fields(approval_models.ExplicitHumanApprovalRequest)
    )
    record_fields = tuple(
        field.name for field in fields(approval_models.ExecutionApprovalRecord)
    )
    decision_fields = tuple(
        field.name for field in fields(
            authorization_models.ExecutionAuthorizationDecision
        )
    )
    if (
        "approval_statement" not in request_fields
        or "approval_statement" in record_fields
        or "approval_statement_fingerprint" not in record_fields
        or "package_fingerprint" not in decision_fields
        or "package_fingerprint" not in record_fields
        or "authorization_fingerprint" not in record_fields
    ):
        raise TranslationExecutionGovernanceFreezeValidationError(
            "Fingerprint chain or statement-persistence contract drifted."
        )
