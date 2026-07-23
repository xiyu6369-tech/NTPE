from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import dataclass, is_dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_COMPONENT_NAME = "ntpe.controlled_runtime_preparation"
_FREEZE_VERSION = "5.4"
_SUBMISSION_SCHEMA = ("ntpe.controlled_runtime_submission_package", "1.0")
_ADAPTER_SCHEMA = ("ntpe.controlled_runtime_adapter_request", "1.0")
_EXECUTION_PLAN_SCHEMA = ("ntpe.controlled_runtime_execution_plan", "1.0")
_ACTIVATION_GATE = "controlled_runtime_preparation_frozen"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_RELATIVE_PATH = Path("manifests/controlled_runtime_stage54_freeze_manifest.json")

_FROZEN_MODULES = (
    "core/controlled_runtime_adapter/__init__.py",
    "core/controlled_runtime_adapter/adapter.py",
    "core/controlled_runtime_adapter/errors.py",
    "core/controlled_runtime_adapter/models.py",
    "core/controlled_runtime_adapter/policy.py",
    "core/controlled_runtime_execution_plan/__init__.py",
    "core/controlled_runtime_execution_plan/errors.py",
    "core/controlled_runtime_execution_plan/freeze.py",
    "core/controlled_runtime_execution_plan/models.py",
    "core/controlled_runtime_execution_plan/planner.py",
    "core/controlled_runtime_execution_plan/policy.py",
    "core/controlled_runtime_submission/__init__.py",
    "core/controlled_runtime_submission/builder.py",
    "core/controlled_runtime_submission/errors.py",
    "core/controlled_runtime_submission/models.py",
    "core/controlled_runtime_submission/policy.py",
)
_SUBMISSION_API = (
    "ControlledRuntimeSubmissionBuilder", "RuntimeSubmissionPackage",
    "RuntimeSubmissionUnit", "RuntimeSubmissionSourceReference",
    "RuntimeSubmissionFinding", "ControlledRuntimeSubmissionError",
    "InvalidRuntimeSubmissionInputError", "RuntimeSubmissionConsistencyError",
    "RuntimeSubmissionScopeError", "RuntimeSubmissionPolicyError",
    "RuntimeSubmissionInvariantError",
)
_ADAPTER_API = (
    "ControlledRuntimeAdapter", "RuntimeAdapterRequest", "RuntimeAdapterUnit",
    "RuntimeAdapterSourceReference", "RuntimeAdapterCapabilityProfile",
    "RuntimeAdapterPreparationResult", "RuntimeAdapterFinding",
    "ControlledRuntimeAdapterError", "InvalidRuntimeAdapterInputError",
    "RuntimeAdapterConsistencyError", "RuntimeAdapterCapabilityError",
    "RuntimeAdapterInvariantError", "RuntimeAdapterPolicyError",
)
_EXECUTION_PLAN_API = (
    "ControlledRuntimeExecutionPlanner", "ControlledRuntimeExecutionPlan",
    "ControlledRuntimeExecutionStep", "ControlledRuntimeExecutionSourceReference",
    "ControlledRuntimeExecutionPolicy", "ControlledRuntimeExecutionFinding",
    "ControlledRuntimeExecutionPlanError", "InvalidControlledRuntimeExecutionInputError",
    "ControlledRuntimeExecutionConsistencyError", "ControlledRuntimeExecutionPolicyError",
    "ControlledRuntimeExecutionInvariantError", "ControlledRuntimeExecutionScopeError",
)
_FREEZE_API = (
    "ControlledRuntimePreparationFreezeMetadata",
    "ControlledRuntimePreparationFreezeValidationResult",
    "ControlledRuntimePreparationFreezeValidationError",
    "get_controlled_runtime_preparation_freeze_metadata",
    "validate_controlled_runtime_preparation_freeze",
)
_PUBLIC_API = _SUBMISSION_API + _ADAPTER_API + _EXECUTION_PLAN_API + _FREEZE_API
_INVARIANTS = (
    "offline_only", "deterministic", "immutable_results", "canonical_json",
    "exact_utf8_sha256", "submission_scope_exact", "submission_scope_not_expanded",
    "submission_units_not_merged", "submission_units_not_resegmented",
    "submission_units_order_preserved", "submission_partial_coverage_semantics_frozen",
    "submission_execution_counters_zero", "submission_runtime_not_executed",
    "adapter_mapping_one_to_one", "adapter_scope_preserved",
    "adapter_authorization_preserved", "adapter_execution_capabilities_disabled",
    "adapter_provider_capability_disabled", "adapter_translation_capability_disabled",
    "adapter_writes_disabled", "adapter_capability_policy_cannot_be_relaxed",
    "adapter_runtime_not_invoked", "adapter_provider_not_invoked",
    "adapter_translation_not_invoked", "execution_plan_single_unit_only",
    "execution_plan_explicit_unit_selection_required", "execution_plan_no_auto_selection",
    "execution_plan_provider_request_limit_one", "execution_plan_retry_limit_zero",
    "execution_plan_fallback_limit_zero", "execution_plan_sequential_only",
    "execution_plan_execution_enablement_disabled", "execution_plan_not_started",
    "execution_plan_not_completed", "authorization_and_enablement_separated",
    "runtime_authorization_does_not_imply_enablement",
    "provider_authorization_does_not_imply_enablement",
    "translation_authorization_does_not_imply_enablement", "no_runtime_execution",
    "no_provider_execution", "no_network_execution", "no_translation_execution",
    "no_output_write", "no_resume_write", "no_cache_write", "no_retry_execution",
    "no_fallback_execution", "no_production_hook", "production_integration_not_authorized",
)

class ControlledRuntimePreparationFreezeValidationError(RuntimeError):
    """Raised when the Stage 5.4 controlled runtime freeze no longer validates."""

@dataclass(frozen=True)
class ControlledRuntimePreparationFreezeMetadata:
    component_name: str
    freeze_version: str
    submission_schema_name: str
    submission_schema_version: str
    adapter_schema_name: str
    adapter_schema_version: str
    execution_plan_schema_name: str
    execution_plan_schema_version: str
    activation_gate: str
    frozen_modules: tuple[str, ...]
    public_api: tuple[str, ...]
    invariants: tuple[str, ...]
    runtime_execution_authorized: bool
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_execution_enabled: bool
    provider_execution_enabled: bool
    translation_execution_enabled: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    output_write_authorized: bool
    resume_write_authorized: bool
    cache_write_authorized: bool
    production_integration_authorized: bool

@dataclass(frozen=True)
class ControlledRuntimePreparationFreezeValidationResult:
    valid: bool
    frozen_file_count: int
    public_api_count: int
    invariant_count: int
    activation_gate: str

_METADATA = ControlledRuntimePreparationFreezeMetadata(
    component_name=_COMPONENT_NAME, freeze_version=_FREEZE_VERSION,
    submission_schema_name=_SUBMISSION_SCHEMA[0], submission_schema_version=_SUBMISSION_SCHEMA[1],
    adapter_schema_name=_ADAPTER_SCHEMA[0], adapter_schema_version=_ADAPTER_SCHEMA[1],
    execution_plan_schema_name=_EXECUTION_PLAN_SCHEMA[0],
    execution_plan_schema_version=_EXECUTION_PLAN_SCHEMA[1], activation_gate=_ACTIVATION_GATE,
    frozen_modules=_FROZEN_MODULES, public_api=_PUBLIC_API, invariants=_INVARIANTS,
    runtime_execution_authorized=False, provider_execution_authorized=False,
    translation_execution_authorized=False, runtime_execution_enabled=False,
    provider_execution_enabled=False, translation_execution_enabled=False,
    automatic_retry_authorized=False, automatic_fallback_authorized=False,
    output_replacement_authorized=False, output_write_authorized=False,
    resume_write_authorized=False, cache_write_authorized=False,
    production_integration_authorized=False,
)
_RESULT = ControlledRuntimePreparationFreezeValidationResult(
    True, len(_FROZEN_MODULES), len(_PUBLIC_API), len(_INVARIANTS), _ACTIVATION_GATE
)

def get_controlled_runtime_preparation_freeze_metadata() -> ControlledRuntimePreparationFreezeMetadata:
    """Return deterministic immutable Stage 5.4 freeze metadata."""
    return _METADATA

def validate_controlled_runtime_preparation_freeze() -> ControlledRuntimePreparationFreezeValidationResult:
    """Validate Stage 5 source, API, schema, scope, and offline boundaries."""
    try:
        root = Path(__file__).resolve().parents[2]
        raw = (root / _MANIFEST_RELATIVE_PATH).read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ControlledRuntimePreparationFreezeValidationError("Freeze manifest contains a BOM.")
        text = raw.decode("utf-8")
        manifest = json.loads(text)
        canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if text not in {canonical, canonical + "\n"}:
            raise ControlledRuntimePreparationFreezeValidationError("Freeze manifest is not canonical JSON.")
        _validate_manifest(manifest)
        _validate_public_api()
        _validate_sources(root, manifest)
        _validate_contracts()
        return _RESULT
    except ControlledRuntimePreparationFreezeValidationError:
        raise
    except Exception as error:
        raise ControlledRuntimePreparationFreezeValidationError(
            f"Controlled runtime preparation freeze validation failed: {error}"
        ) from error

def _validate_manifest(manifest: dict[str, Any]) -> None:
    expected = {
        "component": _COMPONENT_NAME, "stage": _FREEZE_VERSION,
        "freeze_version": _FREEZE_VERSION, "activation_gate": _ACTIVATION_GATE,
        "runtime_executions_added": 0, "provider_requests_added": 0,
        "network_requests_added": 0, "translation_executions_added": 0,
        "output_writes_added": 0, "resume_writes_added": 0, "cache_writes_added": 0,
        "retry_executions_added": 0, "fallback_executions_added": 0,
        "production_hooks_added": 0, "production_integration_authorized": False,
    }
    for name, value in expected.items():
        if manifest.get(name) != value:
            raise ControlledRuntimePreparationFreezeValidationError(f"Invalid manifest field: {name}.")
    schemas = {"submission": list(_SUBMISSION_SCHEMA), "adapter": list(_ADAPTER_SCHEMA),
               "execution_plan": list(_EXECUTION_PLAN_SCHEMA)}
    if manifest.get("schemas") != schemas:
        raise ControlledRuntimePreparationFreezeValidationError("Frozen schema inventory drifted.")
    if tuple(manifest.get("public_api", ())) != _PUBLIC_API:
        raise ControlledRuntimePreparationFreezeValidationError("Frozen public API inventory drifted.")
    if tuple(manifest.get("invariants", ())) != _INVARIANTS:
        raise ControlledRuntimePreparationFreezeValidationError("Frozen invariant inventory drifted.")
    tests = manifest.get("validation_tests")
    if not isinstance(tests, list) or not tests or len(tests) != len(set(tests)):
        raise ControlledRuntimePreparationFreezeValidationError("Validation test inventory is invalid.")

def _validate_public_api() -> None:
    import core.controlled_runtime_submission as submission
    import core.controlled_runtime_adapter as adapter
    import core.controlled_runtime_execution_plan as plan
    for module, expected in ((submission, _SUBMISSION_API), (adapter, _ADAPTER_API),
                             (plan, _EXECUTION_PLAN_API + _FREEZE_API)):
        exports = tuple(module.__all__)
        if exports != expected or len(exports) != len(set(exports)):
            raise ControlledRuntimePreparationFreezeValidationError(f"Public API drifted: {module.__name__}.")
        for name in exports:
            value = getattr(module, name, None)
            if not name or name.startswith("_") or value is None:
                raise ControlledRuntimePreparationFreezeValidationError(f"Invalid public API: {name}.")
            owner = getattr(value, "__module__", "")
            if owner and not owner.startswith(module.__name__):
                raise ControlledRuntimePreparationFreezeValidationError(f"Public API owner drifted: {name}.")
    if len(_PUBLIC_API) != len(set(_PUBLIC_API)):
        raise ControlledRuntimePreparationFreezeValidationError("Duplicate aggregate public API.")

def _validate_sources(root: Path, manifest: dict[str, Any]) -> None:
    entries = manifest.get("frozen_files")
    if not isinstance(entries, list):
        raise ControlledRuntimePreparationFreezeValidationError("Frozen source inventory missing.")
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise ControlledRuntimePreparationFreezeValidationError("Frozen source paths invalid or duplicated.")
    if tuple(paths) != _FROZEN_MODULES or paths != sorted(paths):
        raise ControlledRuntimePreparationFreezeValidationError("Frozen source inventory incomplete or unsorted.")
    discovered = tuple(sorted(
        path.relative_to(root).as_posix()
        for directory in ("controlled_runtime_submission", "controlled_runtime_adapter",
                          "controlled_runtime_execution_plan")
        for path in (root / "core" / directory).glob("*.py")
    ))
    if discovered != _FROZEN_MODULES:
        raise ControlledRuntimePreparationFreezeValidationError("Formal Stage 5 source inventory drifted.")
    for entry in entries:
        relative = entry["path"]
        pure = PurePosixPath(relative)
        expected_hash = entry.get("sha256")
        if (pure.is_absolute() or ".." in pure.parts
                or not relative.startswith("core/controlled_runtime_")
                or not relative.endswith(".py")):
            raise ControlledRuntimePreparationFreezeValidationError(f"Invalid frozen path: {relative}.")
        if not isinstance(expected_hash, str) or not _HEX_64.fullmatch(expected_hash):
            raise ControlledRuntimePreparationFreezeValidationError(f"Invalid source hash: {relative}.")
        source = root.joinpath(*pure.parts)
        if not source.is_file():
            raise ControlledRuntimePreparationFreezeValidationError(f"Missing frozen source: {relative}.")
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
            raise ControlledRuntimePreparationFreezeValidationError(f"Frozen source hash mismatch: {relative}.")

def _validate_contracts() -> None:
    from core.controlled_runtime_submission import models as sm, policy as sp
    from core.controlled_runtime_adapter import models as am, policy as ap
    from core.controlled_runtime_execution_plan import models as pm, policy as pp
    if ((sp.SCHEMA_NAME, sp.SCHEMA_VERSION) != _SUBMISSION_SCHEMA
            or sp.STRATEGY != "deterministic_controlled_runtime_submission_v1"
            or sp.ACTIVATION_GATE != "controlled_runtime_submission_prepared"):
        raise ControlledRuntimePreparationFreezeValidationError("Submission contract drifted.")
    if ((ap.SCHEMA_NAME, ap.SCHEMA_VERSION) != _ADAPTER_SCHEMA
            or ap.STRATEGY != "deterministic_offline_runtime_adapter_v1"
            or ap.ACTIVATION_GATE != "controlled_runtime_adapter_prepared"):
        raise ControlledRuntimePreparationFreezeValidationError("Adapter contract drifted.")
    if ((pp.SCHEMA_NAME, pp.SCHEMA_VERSION) != _EXECUTION_PLAN_SCHEMA
            or pp.STRATEGY != "deterministic_single_unit_execution_plan_v1"
            or pp.ACTIVATION_GATE != "controlled_runtime_execution_plan_prepared"):
        raise ControlledRuntimePreparationFreezeValidationError("Execution plan contract drifted.")
    model_types = (
        sm.RuntimeSubmissionSourceReference, sm.RuntimeSubmissionUnit,
        sm.RuntimeSubmissionFinding, sm.RuntimeSubmissionPackage,
        am.RuntimeAdapterSourceReference, am.RuntimeAdapterCapabilityProfile,
        am.RuntimeAdapterUnit, am.RuntimeAdapterFinding, am.RuntimeAdapterRequest,
        am.RuntimeAdapterPreparationResult, pm.ControlledRuntimeExecutionSourceReference,
        pm.ControlledRuntimeExecutionPolicy, pm.ControlledRuntimeExecutionStep,
        pm.ControlledRuntimeExecutionFinding, pm.ControlledRuntimeExecutionPlan,
        ControlledRuntimePreparationFreezeMetadata, ControlledRuntimePreparationFreezeValidationResult,
    )
    if any(not is_dataclass(model) or not model.__dataclass_params__.frozen for model in model_types):
        raise ControlledRuntimePreparationFreezeValidationError("Stage 5 model immutability drifted.")
    sd = sp.DEFAULT_POLICY
    if (sd.unit_status != "queued_for_controlled_submission"
            or sd.unit_runtime_attempt_count != 0 or sd.unit_provider_request_count != 0
            or sd.unit_translation_result_attached is not False
            or not all(sd.controlled_authorization_flags.values())
            or any(sd.prohibited_authorization_flags.values()) or any(sd.execution_state.values())):
        raise ControlledRuntimePreparationFreezeValidationError("Submission boundary drifted.")
    profile = ap.DEFAULT_CAPABILITY_PROFILE
    if (not profile.supports_controlled_submission or not profile.supports_partial_scope
            or not profile.supports_full_package_scope
            or any(getattr(profile, name) for name in ap.PROHIBITED_CAPABILITIES)):
        raise ControlledRuntimePreparationFreezeValidationError("Adapter capability boundary drifted.")
    policy = pp.DEFAULT_POLICY
    if (policy.execution_mode != "single_pass_sequential_controlled"
            or policy.maximum_units_per_execution != 1
            or policy.maximum_provider_requests_per_unit != 1
            or policy.maximum_total_provider_requests != 1
            or not policy.allow_partial_scope
            or any(getattr(policy, name) for name in pp.PROHIBITED_TRUE_FIELDS)):
        raise ControlledRuntimePreparationFreezeValidationError("Execution plan boundary drifted.")
    from core.controlled_runtime_submission import ControlledRuntimeSubmissionBuilder
    from core.controlled_runtime_adapter import ControlledRuntimeAdapter
    from core.controlled_runtime_execution_plan import ControlledRuntimeExecutionPlanner
    signatures = (
        (inspect.signature(ControlledRuntimeSubmissionBuilder.build),
         ("self", "package", "authorization_decision", "approval_record")),
        (inspect.signature(ControlledRuntimeAdapter.prepare), ("self", "submission_package")),
        (inspect.signature(ControlledRuntimeExecutionPlanner.plan),
         ("self", "adapter_preparation_result", "selected_adapter_unit_indices")),
    )
    if any(tuple(signature.parameters) != expected for signature, expected in signatures):
        raise ControlledRuntimePreparationFreezeValidationError("Stage 5 public API signature drifted.")