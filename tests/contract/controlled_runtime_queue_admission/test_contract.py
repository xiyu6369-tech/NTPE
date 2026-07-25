import ast
import inspect
from dataclasses import fields
from pathlib import Path

import core.controlled_runtime_queue_admission as public
from core.controlled_runtime_queue_admission.models import (
    ControlledRuntimeQueueAdmissionRequest,
    ControlledRuntimeQueueAdmissionResult,
    ControlledRuntimeQueueRecord,
    ControlledRuntimeQueueRecordVerificationResult,
)
from core.controlled_runtime_queue_admission.policy import (
    ADMISSION_CLASS,
    ADMISSION_INTENT,
    BOUNDARY_KIND,
    PRIORITY_CLASS,
    QUEUE_RECORD_SCHEMA_NAME,
    QUEUE_RECORD_SCHEMA_VERSION,
    REASON_CODES,
    REGISTRY_SCHEMA_NAME,
    REGISTRY_SCHEMA_VERSION,
    REQUEST_SCHEMA_NAME,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_NAME,
    RESULT_SCHEMA_VERSION,
    VERIFICATION_SCHEMA_NAME,
    VERIFICATION_SCHEMA_VERSION,
)
from core.controlled_runtime_queue_admission.registry import _UNIQUE_COLUMNS


EXPECTED_API = [
    "ControlledRuntimeQueueAdmissionRequest",
    "ControlledRuntimeQueueRecord",
    "ControlledRuntimeQueueAdmissionResult",
    "ControlledRuntimeQueueRecordVerificationResult",
    "ControlledRuntimeQueueAdmissionPolicy",
    "ControlledRuntimeQueueRegistry",
    "ControlledRuntimeQueueAdmitter",
    "verify_controlled_runtime_queue_record",
    "ControlledRuntimeQueueAdmissionError",
    "ControlledRuntimeQueueAdmissionPathError",
    "ControlledRuntimeQueueAdmissionSchemaError",
    "ControlledRuntimeQueueAdmissionIntegrityError",
    "ControlledRuntimeQueueAdmissionPolicyError",
    "ControlledRuntimeQueueAlreadyAdmittedError",
    "ControlledRuntimeQueueAdmissionConflictError",
    "ControlledRuntimeQueueAdmissionCommitError",
    "ControlledRuntimeQueueAdmissionVerificationError",
]


def test_exact_public_api_has_no_runtime_execution_interfaces():
    assert public.__all__ == EXPECTED_API
    forbidden = ("scheduler", "executor", "provider", "translator", "worker")
    assert not any(
        token in name.lower() for token in forbidden for name in public.__all__
    )


def test_exact_schema_names_versions_and_policy_constants():
    assert (REQUEST_SCHEMA_NAME, REQUEST_SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_queue_admission_request", "1.0"
    )
    assert (QUEUE_RECORD_SCHEMA_NAME, QUEUE_RECORD_SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_queue_record", "1.0"
    )
    assert (RESULT_SCHEMA_NAME, RESULT_SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_queue_admission_result", "1.0"
    )
    assert (VERIFICATION_SCHEMA_NAME, VERIFICATION_SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_queue_record_verification_result", "1.0"
    )
    assert (REGISTRY_SCHEMA_NAME, REGISTRY_SCHEMA_VERSION) == (
        "ntpe.controlled_runtime_queue_registry", "1.0"
    )
    assert BOUNDARY_KIND == "controlled_offline_acceptance_boundary"
    assert ADMISSION_CLASS == "controlled_runtime_single_unit"
    assert PRIORITY_CLASS == "controlled_default"
    assert ADMISSION_INTENT == (
        "admit_exactly_one_consumed_and_verified_controlled_runtime_"
        "queue_admission_record_into_the_durable_controlled_runtime_queue"
    )


def test_exact_reason_code_set_is_unique_and_closed():
    assert REASON_CODES == (
        "INVALID_SCHEMA", "INVALID_IDENTITY", "FINGERPRINT_MISMATCH",
        "UPSTREAM_VERIFICATION_FAILED", "UPSTREAM_RESULT_INVALID",
        "REPLAY_ONLY_AUTHORITY", "UPSTREAM_STATE_MISMATCH", "BINDING_MISMATCH",
        "INVALID_UNIT_SCOPE", "INVALID_INTENT", "INVALID_ADMISSION_CLASS",
        "INVALID_PRIORITY_CLASS", "INVALID_ORDERING_KEY", "CLAIM_NOT_COMMITTED",
        "CLAIM_READBACK_NOT_VERIFIED", "CLAIM_NOT_ORIGINAL_SUCCESS",
        "RECORD_NOT_CONSUMED", "QUEUE_ALREADY_ADMITTED",
        "QUEUE_RECORD_ALREADY_CREATED", "SCHEDULING_ALREADY_STARTED",
        "EXECUTION_ALREADY_STARTED", "ACTIVE_CAPABILITY_DETECTED",
        "CHAIN_MISMATCH", "CANONICAL_PAYLOAD_MISMATCH",
        "PERSISTENCE_NOT_PROVEN", "READBACK_NOT_PROVEN", "ALREADY_ADMITTED",
        "CONFLICT", "REGISTRY_ERROR", "INVARIANT_VIOLATION",
    )
    assert len(REASON_CODES) == len(set(REASON_CODES))


def test_exact_model_fields_and_state_invariants():
    request_fields = tuple(item.name for item in fields(ControlledRuntimeQueueAdmissionRequest))
    assert request_fields == (
        "stage613_claim_id", "stage613_claim_fingerprint",
        "stage613_consumption_request_id", "stage613_consumption_request_fingerprint",
        "stage612_record_id", "stage612_record_fingerprint",
        "stage612_preparation_request_id", "stage612_request_fingerprint",
        "stage611_claim_id", "stage611_claim_fingerprint",
        "stage610_authorization_id", "stage610_decision_fingerprint",
        "stage610_authorization_request_id", "stage610_request_fingerprint",
        "stage69_consumption_claim_id", "stage69_claim_fingerprint",
        "stage68_scheduling_envelope_id", "stage68_envelope_fingerprint",
        "stage67_consumption_claim_id", "stage67_claim_fingerprint",
        "stage66_scheduling_authorization_id", "stage66_decision_fingerprint",
        "runtime_boundary_id", "runtime_boundary_kind", "selected_adapter_index",
        "capability_state_fingerprint", "admission_class", "priority_class",
        "ordering_key", "unit_scope", "upstream_chain", "admission_intent",
        "schema_name", "schema_version", "admission_request_id",
        "request_fingerprint",
    )
    record_fields = tuple(item.name for item in fields(ControlledRuntimeQueueRecord))
    assert all(name in record_fields for name in request_fields[:30])
    for required in (
        "queue_admission_performed", "queue_record_created",
        "queue_record_consumed", "queue_record_reusable",
        "runtime_execution_scheduled", "execution_started", "canonical_chain",
        "queue_record_id", "queue_record_fingerprint",
    ):
        assert required in record_fields
    result_fields = tuple(item.name for item in fields(ControlledRuntimeQueueAdmissionResult))
    verification_fields = tuple(
        item.name for item in fields(ControlledRuntimeQueueRecordVerificationResult)
    )
    assert "runtime_schedule_count" in result_fields
    assert "provider_execution_count" in result_fields
    assert verification_fields[:4] == (
        "valid", "schema_verified", "identity_verified", "fingerprint_verified"
    )


def test_durable_uniqueness_covers_all_required_identities():
    assert _UNIQUE_COLUMNS == frozenset((
        ("admission_request_id",), ("request_fingerprint",),
        ("queue_record_id",), ("queue_record_fingerprint",),
        ("stage613_claim_id",), ("stage613_claim_fingerprint",),
        ("stage612_record_id",), ("stage612_record_fingerprint",),
    ))


def test_sqlite_is_confined_to_registry_and_forbidden_imports_are_absent():
    root = Path(inspect.getfile(public)).parent
    imports = {}
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
        imports[path.name] = tuple(names)
    sqlite_files = tuple(
        name for name, names in imports.items() if "sqlite3" in names
    )
    assert sqlite_files == ("registry.py",)
    forbidden_prefixes = (
        "core.translation_scheduler", "core.production_runtime",
        "core.workflow", "core.ai_provider", "core.translation_runtime",
        "requests", "httpx", "subprocess", "asyncio", "threading",
        "concurrent.futures",
    )
    assert not any(
        imported.startswith(prefix)
        for names in imports.values()
        for imported in names
        for prefix in forbidden_prefixes
    )


def test_authentic_stage613_public_api_and_official_verifier_are_reused():
    root = Path(inspect.getfile(public)).parent
    policy = (root / "policy.py").read_text(encoding="utf-8")
    verification = (root / "verification.py").read_text(encoding="utf-8")
    assert "core.controlled_runtime_queue_admission_record_consumption" in policy
    assert "verify_controlled_runtime_queue_admission_record_consumption(" in policy
    assert "core.controlled_runtime_queue_admission_record_consumption" in verification
    assert "uuid" not in "\n".join(
        path.read_text(encoding="utf-8").lower() for path in root.glob("*.py")
    )
