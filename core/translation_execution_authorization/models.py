from __future__ import annotations

import json
import re
from dataclasses import dataclass


AuthorizationFindingValue = str | int | float | bool | None
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ExecutionAuthorizationPolicy:
    policy_name: str
    policy_version: str
    required_package_schema_name: str
    required_package_schema_version: str
    required_package_activation_gate: str
    allow_prepared: bool
    allow_prepared_with_warnings: bool
    allow_manual_review: bool
    allow_blocked: bool
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    require_explicit_human_approval: bool


@dataclass(frozen=True)
class ExecutionAuthorizationFinding:
    code: str
    severity: str
    message: str
    observed_value: AuthorizationFindingValue = None
    required_value: AuthorizationFindingValue = None


@dataclass(frozen=True)
class ExecutionAuthorizationDecision:
    schema_name: str
    schema_version: str
    strategy: str
    package_fingerprint: str
    package_status: str
    package_action: str
    package_activation_gate: str
    policy_name: str
    policy_version: str
    authorized: bool
    decision: str
    action: str
    provider_execution_authorized: bool
    translation_execution_authorized: bool
    runtime_submission_authorized: bool
    automatic_retry_authorized: bool
    automatic_fallback_authorized: bool
    output_replacement_authorized: bool
    requires_human_approval: bool
    findings: tuple[ExecutionAuthorizationFinding, ...]
    summary: str
    authorization_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if not _HEX_64.fullmatch(self.package_fingerprint):
            raise ValueError("package_fingerprint must be lowercase SHA-256 hex")
        if not _HEX_64.fullmatch(self.authorization_fingerprint):
            raise ValueError("authorization_fingerprint must be lowercase SHA-256 hex")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "strategy": self.strategy,
            "package_fingerprint": self.package_fingerprint,
            "package_status": self.package_status,
            "package_action": self.package_action,
            "package_activation_gate": self.package_activation_gate,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "authorized": self.authorized,
            "decision": self.decision,
            "action": self.action,
            "provider_execution_authorized": self.provider_execution_authorized,
            "translation_execution_authorized": self.translation_execution_authorized,
            "runtime_submission_authorized": self.runtime_submission_authorized,
            "automatic_retry_authorized": self.automatic_retry_authorized,
            "automatic_fallback_authorized": self.automatic_fallback_authorized,
            "output_replacement_authorized": self.output_replacement_authorized,
            "requires_human_approval": self.requires_human_approval,
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
            "authorization_fingerprint": self.authorization_fingerprint,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

