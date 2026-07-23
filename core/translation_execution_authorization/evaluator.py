from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict

from core.translation_execution_package import TranslationExecutionPackage
from core.translation_execution_package.policy import (
    STRATEGY as PACKAGE_STRATEGY,
    make_unit_id,
)

from .errors import (
    ExecutionAuthorizationConsistencyError,
    ExecutionAuthorizationPolicyError,
    InvalidExecutionAuthorizationInputError,
    InvalidExecutionPackageStateError,
)
from .models import (
    ExecutionAuthorizationDecision,
    ExecutionAuthorizationFinding,
    ExecutionAuthorizationPolicy,
)
from .policy import (
    ALLOW_FLAG_NAMES,
    DEFAULT_POLICY,
    DENIED_DECISION,
    EXECUTION_FLAG_NAMES,
    FINDING_MESSAGES,
    FINDING_ORDER,
    FINDING_SEVERITIES,
    HOLD_ACTION,
    MANUAL_REVIEW_ACTION,
    PACKAGE_STATUS_ACTIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STRATEGY,
)


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class _FindingCollector:
    def __init__(self) -> None:
        self._items: dict[str, ExecutionAuthorizationFinding] = {}

    def add(
        self,
        code: str,
        *,
        observed_value: str | int | float | bool | None = None,
        required_value: str | int | float | bool | None = None,
    ) -> None:
        self._items.setdefault(
            code,
            ExecutionAuthorizationFinding(
                code=code,
                severity=FINDING_SEVERITIES[code],
                message=FINDING_MESSAGES[code],
                observed_value=observed_value,
                required_value=required_value,
            ),
        )

    def ordered(self) -> tuple[ExecutionAuthorizationFinding, ...]:
        return tuple(
            sorted(self._items.values(), key=lambda item: FINDING_ORDER[item.code])
        )


class TranslationExecutionAuthorizationEvaluator:
    """Validate one Stage 4.1 package and emit a fail-closed denied decision."""

    def __init__(
        self, policy: ExecutionAuthorizationPolicy = DEFAULT_POLICY
    ) -> None:
        if not isinstance(policy, ExecutionAuthorizationPolicy):
            raise InvalidExecutionAuthorizationInputError(
                "policy must be an ExecutionAuthorizationPolicy"
            )
        self._validate_policy(policy)
        self._policy = policy

    def evaluate(
        self, package: TranslationExecutionPackage
    ) -> ExecutionAuthorizationDecision:
        if not isinstance(package, TranslationExecutionPackage):
            raise InvalidExecutionAuthorizationInputError(
                "package must be a TranslationExecutionPackage"
            )
        self._validate_package(package)

        findings = _FindingCollector()
        findings.add("EXPLICIT_AUTHORIZATION_REQUIRED")
        findings.add("PROVIDER_EXECUTION_NOT_AUTHORIZED")
        findings.add("TRANSLATION_EXECUTION_NOT_AUTHORIZED")
        findings.add("RUNTIME_SUBMISSION_NOT_AUTHORIZED")
        findings.add("AUTOMATIC_RETRY_NOT_AUTHORIZED")
        findings.add("AUTOMATIC_FALLBACK_NOT_AUTHORIZED")
        findings.add("OUTPUT_REPLACEMENT_NOT_AUTHORIZED")
        if package.status == "prepared_with_warnings":
            warning_codes = tuple(
                dict.fromkeys(
                    finding.code
                    for finding in package.findings
                    if finding.severity == "warning"
                )
            )
            findings.add(
                "MANUAL_REVIEW_REQUIRED",
                observed_value=(
                    ",".join(warning_codes)
                    if warning_codes
                    else "prepared_with_warnings"
                ),
                required_value="explicit_human_approval",
            )
        ordered_findings = findings.ordered()
        action = (
            MANUAL_REVIEW_ACTION
            if package.status == "prepared_with_warnings"
            else HOLD_ACTION
        )
        authorization_fingerprint = _authorization_fingerprint(
            package=package,
            policy=self._policy,
            action=action,
            findings=ordered_findings,
        )
        return ExecutionAuthorizationDecision(
            schema_name=SCHEMA_NAME,
            schema_version=SCHEMA_VERSION,
            strategy=STRATEGY,
            package_fingerprint=package.execution_package_fingerprint,
            package_status=package.status,
            package_action=package.action,
            package_activation_gate=package.activation_gate,
            policy_name=self._policy.policy_name,
            policy_version=self._policy.policy_version,
            authorized=False,
            decision=DENIED_DECISION,
            action=action,
            provider_execution_authorized=False,
            translation_execution_authorized=False,
            runtime_submission_authorized=False,
            automatic_retry_authorized=False,
            automatic_fallback_authorized=False,
            output_replacement_authorized=False,
            requires_human_approval=True,
            findings=ordered_findings,
            summary=(
                f"Execution authorization denied for {package.status} package; "
                "explicit human approval remains required."
            ),
            authorization_fingerprint=authorization_fingerprint,
        )

    @staticmethod
    def _validate_policy(policy: ExecutionAuthorizationPolicy) -> None:
        unsafe_fields = tuple(
            name
            for name in (*ALLOW_FLAG_NAMES, *EXECUTION_FLAG_NAMES)
            if getattr(policy, name) is not False
        )
        if policy.require_explicit_human_approval is not True:
            unsafe_fields += ("require_explicit_human_approval",)
        required_contract = (
            policy.required_package_schema_name
            == DEFAULT_POLICY.required_package_schema_name
            and policy.required_package_schema_version
            == DEFAULT_POLICY.required_package_schema_version
            and policy.required_package_activation_gate
            == DEFAULT_POLICY.required_package_activation_gate
        )
        if not required_contract:
            unsafe_fields += ("required_package_contract",)
        if unsafe_fields:
            finding = _finding(
                "POLICY_RELAXATION_REJECTED",
                observed_value=",".join(unsafe_fields),
                required_value="fail_closed",
            )
            raise ExecutionAuthorizationPolicyError(
                finding.message, finding=finding
            )

    def _validate_package(self, package: TranslationExecutionPackage) -> None:
        if package.schema_name != self._policy.required_package_schema_name:
            self._raise_state(
                "PACKAGE_SCHEMA_MISMATCH",
                package.schema_name,
                self._policy.required_package_schema_name,
            )
        if package.schema_version != self._policy.required_package_schema_version:
            self._raise_state(
                "PACKAGE_VERSION_MISMATCH",
                package.schema_version,
                self._policy.required_package_schema_version,
            )
        if package.strategy != PACKAGE_STRATEGY:
            self._raise_state(
                "PACKAGE_STRATEGY_MISMATCH", package.strategy, PACKAGE_STRATEGY
            )
        if package.activation_gate != self._policy.required_package_activation_gate:
            self._raise_state(
                "PACKAGE_ACTIVATION_GATE_MISMATCH",
                package.activation_gate,
                self._policy.required_package_activation_gate,
            )
        if package.status == "blocked":
            self._raise_state("BLOCKED_PACKAGE_REJECTED", package.status, "prepared")
        if package.status in {"manual_review", "manual_review_required"}:
            self._raise_state(
                "PACKAGE_STATUS_NOT_ELIGIBLE", package.status, "prepared"
            )
        if package.status not in {"prepared", "prepared_with_warnings"}:
            self._raise_state(
                "PACKAGE_STATUS_NOT_ELIGIBLE", package.status, "prepared"
            )
        expected_action = PACKAGE_STATUS_ACTIONS[package.status]
        if package.action != expected_action:
            self._raise_state(
                "PACKAGE_ACTION_MISMATCH", package.action, expected_action
            )
        if not _HEX_64.fullmatch(package.execution_package_fingerprint):
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_INVALID",
                package.execution_package_fingerprint,
                "lowercase_sha256",
            )
        if package.unit_count != len(package.units):
            self._raise_consistency(
                "PACKAGE_UNIT_COUNT_MISMATCH", package.unit_count, len(package.units)
            )
        source_text = package.reconstruct_source_text()
        if (
            not source_text
            or package.character_count != len(source_text)
            or package.covered_character_count != len(source_text)
            or sum(unit.character_count for unit in package.units) != len(source_text)
            or package.coverage_ratio != 1.0
            or hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            != package.source.source_content_fingerprint
        ):
            self._raise_consistency(
                "PACKAGE_CONTENT_MISMATCH",
                package.character_count,
                len(source_text),
            )
        expected_start = 0
        for index, unit in enumerate(package.units):
            if unit.source_character_start > expected_start:
                self._raise_consistency(
                    "PACKAGE_OFFSET_GAP", unit.source_character_start, expected_start
                )
            if unit.source_character_start < expected_start:
                self._raise_consistency(
                    "PACKAGE_OFFSET_OVERLAP",
                    unit.source_character_start,
                    expected_start,
                )
            if unit.source_character_end < unit.source_character_start:
                self._raise_consistency(
                    "PACKAGE_OFFSET_OVERLAP",
                    unit.source_character_end,
                    unit.source_character_start,
                )
            if unit.status != "prepared" or unit.attempt_count != 0:
                self._raise_state(
                    "PACKAGE_ALREADY_EXECUTED",
                    f"{unit.status}:{unit.attempt_count}",
                    "prepared:0",
                )
            if unit.provider_request_count != 0:
                self._raise_state(
                    "PACKAGE_PROVIDER_REQUEST_DETECTED",
                    unit.provider_request_count,
                    0,
                )
            if unit.translation_result_attached is not False:
                self._raise_state(
                    "PACKAGE_TRANSLATION_RESULT_DETECTED",
                    unit.translation_result_attached,
                    False,
                )
            if (
                unit.index != index
                or unit.chunk_index != index
                or unit.unit_id != make_unit_id(index, unit.source_chunk_fingerprint)
                or unit.text
                != source_text[
                    unit.source_character_start : unit.source_character_end
                ]
                or unit.character_count != len(unit.text)
                or unit.non_whitespace_character_count
                != sum(not character.isspace() for character in unit.text)
                or unit.source_chunk_fingerprint
                != hashlib.sha256(unit.text.encode("utf-8")).hexdigest()
                or unit.execution_unit_fingerprint != _unit_fingerprint(unit)
            ):
                self._raise_consistency(
                    "PACKAGE_CONTENT_MISMATCH", index, "canonical_execution_unit"
                )
            expected_start = unit.source_character_end
        if expected_start != len(source_text):
            self._raise_consistency(
                "PACKAGE_OFFSET_GAP", expected_start, len(source_text)
            )
        for name in EXECUTION_FLAG_NAMES:
            if getattr(package, name) is not False:
                self._raise_state(
                    "PACKAGE_AUTHORIZATION_FLAG_TAMPERED", name, False
                )
        if package.execution_package_fingerprint != _package_fingerprint(package):
            self._raise_consistency(
                "PACKAGE_FINGERPRINT_INVALID",
                package.execution_package_fingerprint,
                "canonical_package_fingerprint",
            )

    @staticmethod
    def _raise_state(
        code: str,
        observed_value: str | int | float | bool | None,
        required_value: str | int | float | bool | None,
    ) -> None:
        finding = _finding(code, observed_value, required_value)
        raise InvalidExecutionPackageStateError(finding.message, finding=finding)

    @staticmethod
    def _raise_consistency(
        code: str,
        observed_value: str | int | float | bool | None,
        required_value: str | int | float | bool | None,
    ) -> None:
        finding = _finding(code, observed_value, required_value)
        raise ExecutionAuthorizationConsistencyError(
            finding.message, finding=finding
        )


def _finding(
    code: str,
    observed_value: str | int | float | bool | None = None,
    required_value: str | int | float | bool | None = None,
) -> ExecutionAuthorizationFinding:
    return ExecutionAuthorizationFinding(
        code=code,
        severity=FINDING_SEVERITIES[code],
        message=FINDING_MESSAGES[code],
        observed_value=observed_value,
        required_value=required_value,
    )


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_payload(payload: object) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _unit_fingerprint(unit: object) -> str:
    payload = {
        "index": unit.index,
        "unit_id": unit.unit_id,
        "chunk_index": unit.chunk_index,
        "source_character_start": unit.source_character_start,
        "source_character_end": unit.source_character_end,
        "section_indices": list(unit.section_indices),
        "heading_text": unit.heading_text,
        "boundary_reason": unit.boundary_reason,
        "source_chunk_fingerprint": unit.source_chunk_fingerprint,
        "status": unit.status,
        "attempt_count": unit.attempt_count,
        "provider_request_count": unit.provider_request_count,
        "translation_result_attached": unit.translation_result_attached,
    }
    return _sha256_payload(payload)


def _package_fingerprint(package: TranslationExecutionPackage) -> str:
    payload = {
        "schema_name": package.schema_name,
        "schema_version": package.schema_version,
        "strategy": package.strategy,
        "activation_gate": package.activation_gate,
        "source": asdict(package.source),
        "unit_fingerprints": [
            unit.execution_unit_fingerprint for unit in package.units
        ],
        "status": package.status,
        "action": package.action,
        "findings": [asdict(finding) for finding in package.findings],
        "authorization_flags": {
            name: getattr(package, name) for name in EXECUTION_FLAG_NAMES
        },
        "unit_count": package.unit_count,
        "character_count": package.character_count,
        "covered_character_count": package.covered_character_count,
        "coverage_ratio": package.coverage_ratio,
    }
    return _sha256_payload(payload)


def _authorization_fingerprint(
    *,
    package: TranslationExecutionPackage,
    policy: ExecutionAuthorizationPolicy,
    action: str,
    findings: tuple[ExecutionAuthorizationFinding, ...],
) -> str:
    payload = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "strategy": STRATEGY,
        "package_fingerprint": package.execution_package_fingerprint,
        "package_status": package.status,
        "package_action": package.action,
        "package_activation_gate": package.activation_gate,
        "policy_name": policy.policy_name,
        "policy_version": policy.policy_version,
        "authorized": False,
        "decision": DENIED_DECISION,
        "action": action,
        "provider_execution_authorized": False,
        "translation_execution_authorized": False,
        "runtime_submission_authorized": False,
        "automatic_retry_authorized": False,
        "automatic_fallback_authorized": False,
        "output_replacement_authorized": False,
        "requires_human_approval": True,
        "finding_codes": [finding.code for finding in findings],
    }
    return _sha256_payload(payload)

