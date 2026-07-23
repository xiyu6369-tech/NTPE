from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


SCHEMA_NAME = "ntpe.translation_execution_package"
SCHEMA_VERSION = "1.0"
STRATEGY = "deterministic_offline_execution_package_v1"
ACTIVATION_GATE = "translation_execution_package_prepared"
REQUIRED_ACTIVATION_GATES = (
    "book_intake_layer_frozen",
    "book_preparation_pipeline_frozen",
)

ALLOWED_PREPARATION_STATES = ("ready", "ready_with_warnings")
STATUS_ACTIONS = MappingProxyType(
    {
        "prepared": "hold_for_execution_authorization",
        "prepared_with_warnings": "hold_for_execution_authorization",
        "blocked": "reject",
    }
)
PREPARATION_STATUS_MAP = MappingProxyType(
    {
        "ready": "prepared",
        "ready_with_warnings": "prepared_with_warnings",
    }
)
REJECTED_PREPARATION_ACTIONS = MappingProxyType(
    {"manual_review": "manual_review", "blocked": "reject"}
)

UNIT_STATUS = "prepared"
UNIT_ATTEMPT_COUNT = 0
UNIT_PROVIDER_REQUEST_COUNT = 0
UNIT_TRANSLATION_RESULT_ATTACHED = False

AUTHORIZATION_FLAGS = MappingProxyType(
    {
        "provider_execution_authorized": False,
        "translation_execution_authorized": False,
        "runtime_submission_authorized": False,
        "automatic_retry_authorized": False,
        "automatic_fallback_authorized": False,
        "output_replacement_authorized": False,
    }
)

FINDING_CODES = (
    "PREPARATION_WARNING_PROPAGATED",
    "PREPARATION_MANUAL_REVIEW_REJECTED",
    "PREPARATION_BLOCKED_REJECTED",
    "EMPTY_EXECUTION_PACKAGE",
    "UNIT_COUNT_MISMATCH",
    "UNIT_INDEX_MISMATCH",
    "UNIT_OFFSET_GAP",
    "UNIT_OFFSET_OVERLAP",
    "UNIT_TEXT_MISMATCH",
    "UNIT_SECTION_REFERENCE_MISMATCH",
    "SOURCE_FINGERPRINT_MISMATCH",
    "MANIFEST_FINGERPRINT_MISMATCH",
    "SEGMENTATION_FINGERPRINT_MISMATCH",
    "CHUNK_PLAN_FINGERPRINT_MISMATCH",
    "PREPARATION_FINGERPRINT_MISMATCH",
    "CHUNK_FINGERPRINT_MISMATCH",
    "RECONSTRUCTION_MISMATCH",
    "EXECUTION_NOT_AUTHORIZED",
)
FINDING_SEVERITIES = MappingProxyType(
    {
        "PREPARATION_WARNING_PROPAGATED": "warning",
        "PREPARATION_MANUAL_REVIEW_REJECTED": "blocking",
        "PREPARATION_BLOCKED_REJECTED": "blocking",
        "EMPTY_EXECUTION_PACKAGE": "blocking",
        "UNIT_COUNT_MISMATCH": "blocking",
        "UNIT_INDEX_MISMATCH": "blocking",
        "UNIT_OFFSET_GAP": "blocking",
        "UNIT_OFFSET_OVERLAP": "blocking",
        "UNIT_TEXT_MISMATCH": "blocking",
        "UNIT_SECTION_REFERENCE_MISMATCH": "blocking",
        "SOURCE_FINGERPRINT_MISMATCH": "blocking",
        "MANIFEST_FINGERPRINT_MISMATCH": "blocking",
        "SEGMENTATION_FINGERPRINT_MISMATCH": "blocking",
        "CHUNK_PLAN_FINGERPRINT_MISMATCH": "blocking",
        "PREPARATION_FINGERPRINT_MISMATCH": "blocking",
        "CHUNK_FINGERPRINT_MISMATCH": "blocking",
        "RECONSTRUCTION_MISMATCH": "blocking",
        "EXECUTION_NOT_AUTHORIZED": "info",
    }
)
FINDING_MESSAGES = MappingProxyType(
    {
        "PREPARATION_WARNING_PROPAGATED": "Preparation warnings were propagated without automatic approval.",
        "PREPARATION_MANUAL_REVIEW_REJECTED": "Preparation requires manual review and cannot produce execution units.",
        "PREPARATION_BLOCKED_REJECTED": "Blocked preparation cannot produce an execution package.",
        "EMPTY_EXECUTION_PACKAGE": "A ready preparation cannot produce an empty execution package.",
        "UNIT_COUNT_MISMATCH": "Execution unit count does not match the frozen chunk plan.",
        "UNIT_INDEX_MISMATCH": "Execution unit ordering does not match the frozen chunk plan.",
        "UNIT_OFFSET_GAP": "Execution unit offsets contain a gap.",
        "UNIT_OFFSET_OVERLAP": "Execution unit offsets overlap.",
        "UNIT_TEXT_MISMATCH": "Execution unit text does not match its source slice.",
        "UNIT_SECTION_REFERENCE_MISMATCH": "Execution unit section references do not match the frozen segmentation.",
        "SOURCE_FINGERPRINT_MISMATCH": "Source content fingerprints are inconsistent across frozen stages.",
        "MANIFEST_FINGERPRINT_MISMATCH": "Preparation manifest fingerprint does not match its frozen manifest.",
        "SEGMENTATION_FINGERPRINT_MISMATCH": "Preparation segmentation fingerprint does not match its frozen segmentation.",
        "CHUNK_PLAN_FINGERPRINT_MISMATCH": "Preparation chunk plan fingerprint does not match its frozen chunk plan.",
        "PREPARATION_FINGERPRINT_MISMATCH": "Preparation fingerprint does not match its canonical frozen payload.",
        "CHUNK_FINGERPRINT_MISMATCH": "A source chunk fingerprint does not match its exact text.",
        "RECONSTRUCTION_MISMATCH": "Execution units do not reconstruct the prepared source exactly.",
        "EXECUTION_NOT_AUTHORIZED": "The package is prepared but execution remains explicitly unauthorized.",
    }
)
FINDING_ORDER = MappingProxyType(
    {code: index for index, code in enumerate(FINDING_CODES)}
)

UNIT_FINGERPRINT_FIELDS = (
    "index",
    "unit_id",
    "chunk_index",
    "source_character_start",
    "source_character_end",
    "section_indices",
    "heading_text",
    "boundary_reason",
    "source_chunk_fingerprint",
    "status",
    "attempt_count",
    "provider_request_count",
    "translation_result_attached",
)
PACKAGE_FINGERPRINT_FIELDS = (
    "schema_name",
    "schema_version",
    "strategy",
    "activation_gate",
    "source",
    "unit_fingerprints",
    "status",
    "action",
    "findings",
    "authorization_flags",
    "unit_count",
    "character_count",
    "covered_character_count",
    "coverage_ratio",
)


@dataclass(frozen=True)
class ExecutionPackagePolicy:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    required_activation_gates: tuple[str, ...]
    allowed_preparation_states: tuple[str, ...]
    preparation_status_map: Mapping[str, str]
    status_actions: Mapping[str, str]
    rejected_preparation_actions: Mapping[str, str]
    unit_status: str
    unit_attempt_count: int
    unit_provider_request_count: int
    unit_translation_result_attached: bool
    authorization_flags: Mapping[str, bool]
    finding_codes: tuple[str, ...]
    finding_severities: Mapping[str, str]
    finding_messages: Mapping[str, str]
    finding_order: Mapping[str, int]
    unit_fingerprint_fields: tuple[str, ...]
    package_fingerprint_fields: tuple[str, ...]
    unit_id_prefix_length: int


DEFAULT_POLICY = ExecutionPackagePolicy(
    schema_name=SCHEMA_NAME,
    schema_version=SCHEMA_VERSION,
    strategy=STRATEGY,
    activation_gate=ACTIVATION_GATE,
    required_activation_gates=REQUIRED_ACTIVATION_GATES,
    allowed_preparation_states=ALLOWED_PREPARATION_STATES,
    preparation_status_map=PREPARATION_STATUS_MAP,
    status_actions=STATUS_ACTIONS,
    rejected_preparation_actions=REJECTED_PREPARATION_ACTIONS,
    unit_status=UNIT_STATUS,
    unit_attempt_count=UNIT_ATTEMPT_COUNT,
    unit_provider_request_count=UNIT_PROVIDER_REQUEST_COUNT,
    unit_translation_result_attached=UNIT_TRANSLATION_RESULT_ATTACHED,
    authorization_flags=AUTHORIZATION_FLAGS,
    finding_codes=FINDING_CODES,
    finding_severities=FINDING_SEVERITIES,
    finding_messages=FINDING_MESSAGES,
    finding_order=FINDING_ORDER,
    unit_fingerprint_fields=UNIT_FINGERPRINT_FIELDS,
    package_fingerprint_fields=PACKAGE_FINGERPRINT_FIELDS,
    unit_id_prefix_length=12,
)


def make_unit_id(index: int, source_chunk_fingerprint: str) -> str:
    return f"unit-{index + 1:06d}-{source_chunk_fingerprint[:DEFAULT_POLICY.unit_id_prefix_length]}"

