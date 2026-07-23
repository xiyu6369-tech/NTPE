from __future__ import annotations

import json
import re
from dataclasses import dataclass


ApprovalFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExplicitHumanApprovalRequest:
    approval_type: str
    approved_package_fingerprint: str
    approved_authorization_fingerprint: str
    approved_unit_indices: tuple[int, ...]
    approve_provider_execution: bool
    approve_translation_execution: bool
    approve_runtime_submission: bool
    approve_automatic_retry: bool
    approve_automatic_fallback: bool
    approve_output_replacement: bool
    approval_statement: str
    approval_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.approved_unit_indices, tuple):
            raise TypeError("approved_unit_indices must be a tuple")


@dataclass(frozen=True)
class ExecutionApprovalFinding:
    code: str
    severity: str
    message: str
    observed_value: ApprovalFindingValue = None
    required_value: ApprovalFindingValue = None


@dataclass(frozen=True)
class ExecutionApprovalRecord:
    schema_name: str
    schema_version: str
    strategy: str
    activation_gate: str
    package_fingerprint: str
    authorization_fingerprint: str
    approval_type: str
    approved_unit_indices: tuple[int, ...]
    approved_unit_count: int
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    approved: bool
    decision: str
    action: str
    approval_statement_fingerprint: str
    approval_reference: str
    findings: tuple[ExecutionApprovalFinding, ...]
    summary: str
    approval_record_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.approved_unit_indices, tuple):
            raise TypeError("approved_unit_indices must be a tuple")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if self.approved_unit_count != len(self.approved_unit_indices):
            raise ValueError("approved_unit_count must equal approved scope length")
        for name, value in (
            ("package_fingerprint", self.package_fingerprint),
            ("authorization_fingerprint", self.authorization_fingerprint),
            ("approval_statement_fingerprint", self.approval_statement_fingerprint),
            ("approval_record_fingerprint", self.approval_record_fingerprint),
        ):
            if not _HEX_64.fullmatch(value):
                raise ValueError(f"{name} must be lowercase SHA-256 hex")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "strategy": self.strategy,
            "activation_gate": self.activation_gate,
            "package_fingerprint": self.package_fingerprint,
            "authorization_fingerprint": self.authorization_fingerprint,
            "approval_type": self.approval_type,
            "approved_unit_indices": list(self.approved_unit_indices),
            "approved_unit_count": self.approved_unit_count,
            "provider_execution_authorized": self.provider_execution_authorized,
            "translation_execution_authorized": self.translation_execution_authorized,
            "runtime_submission_authorized": self.runtime_submission_authorized,
            "automatic_retry_authorized": self.automatic_retry_authorized,
            "automatic_fallback_authorized": self.automatic_fallback_authorized,
            "output_replacement_authorized": self.output_replacement_authorized,
            "approved": self.approved,
            "decision": self.decision,
            "action": self.action,
            "approval_statement_fingerprint": self.approval_statement_fingerprint,
            "approval_reference": self.approval_reference,
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "message": finding.message,
                    "observed_value": finding.observed_value,
                    "required_value": finding.required_value,
                }
                for finding in self.findings
            ],
            "summary": self.summary,
            "approval_record_fingerprint": self.approval_record_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
