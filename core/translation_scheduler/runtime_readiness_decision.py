from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .runtime_readiness_evidence_collector import RuntimeReadinessEvidenceCollector
from .runtime_readiness_gate_contract import RuntimeReadinessGateContract
from .runtime_readiness_gate_evaluator import RuntimeReadinessGateEvaluator


class RuntimeReadinessDecision:
    """Combine supplied readiness evidence into a non-executing decision."""

    stage = "3.7.4"
    forbidden_raw_keys = frozenset({"source_text", "text", "chunks"})

    def decide(
        self,
        contract: Mapping[str, Any] | None = None,
        evidence_inputs: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contract_data = (
            dict(contract)
            if isinstance(contract, Mapping)
            else RuntimeReadinessGateContract().build_contract()
        )
        collector = RuntimeReadinessEvidenceCollector()
        evaluator = RuntimeReadinessGateEvaluator()

        try:
            evidence = collector.collect(evidence_inputs)
            evidence_summary = collector.summarize(evidence)
            state = {
                "freezes": evidence["collected_freezes"],
                "checks": evidence["collected_checks"],
                "mode": "mock_only",
            }
            readiness_report = evaluator.evaluate(contract_data, state)
            unsafe_conditions = list(readiness_report["unsafe_conditions"])
        except Exception as exc:  # Safe rejection for malformed Mapping implementations.
            evidence = collector.collect()
            evidence_summary = collector.summarize(evidence)
            readiness_report = evaluator.evaluate(contract_data, None)
            unsafe_conditions = list(readiness_report["unsafe_conditions"])
            unsafe_conditions.append(f"decision_processing_error:{type(exc).__name__}")

        missing_requirements = self._unique(
            list(evidence_summary["missing_sections"])
            + list(readiness_report["missing_freezes"])
            + list(readiness_report["missing_checks"])
        )
        approved = bool(
            readiness_report.get("ready") is True
            and evidence_summary.get("complete") is True
            and not missing_requirements
            and not unsafe_conditions
        )

        return {
            "approved": approved,
            "decision": "approved_for_mock_only" if approved else "rejected",
            "stage": self.stage,
            "readiness_report": readiness_report,
            "evidence_summary": evidence_summary,
            "missing_requirements": missing_requirements,
            "unsafe_conditions": unsafe_conditions,
            "next_allowed_mode": "mock_only",
            "real_runtime_allowed": False,
            "execution_allowed": False,
            "metadata": {
                "decision": "runtime_readiness_decision",
                "stage": self.stage,
                "evidence_source": "supplied_mapping",
                "runtime_touch_mode": "none",
                "provider_touch_mode": "none",
                "launcher_touch_mode": "none",
            },
        }

    def is_approved(self, decision: Mapping[str, Any] | None) -> bool:
        return bool(
            decision
            and decision.get("approved") is True
            and decision.get("decision") == "approved_for_mock_only"
            and decision.get("next_allowed_mode") == "mock_only"
            and decision.get("real_runtime_allowed") is False
            and decision.get("execution_allowed") is False
        )

    def validate_decision(self, decision: Mapping[str, Any] | None) -> dict[str, Any]:
        data = dict(decision) if isinstance(decision, Mapping) else {}
        errors: list[str] = []
        required = {
            "approved",
            "decision",
            "stage",
            "readiness_report",
            "evidence_summary",
            "missing_requirements",
            "unsafe_conditions",
            "next_allowed_mode",
            "real_runtime_allowed",
            "execution_allowed",
            "metadata",
        }
        for key in sorted(required - data.keys()):
            errors.append(f"missing {key}")
        if data.get("stage") != self.stage:
            errors.append("stage must be 3.7.4")
        if data.get("next_allowed_mode") != "mock_only":
            errors.append("next_allowed_mode must be mock_only")
        if data.get("real_runtime_allowed") is not False:
            errors.append("real_runtime_allowed must be false")
        if data.get("execution_allowed") is not False:
            errors.append("execution_allowed must be false")
        if not isinstance(data.get("readiness_report"), Mapping):
            errors.append("readiness_report mapping is required")
        if not isinstance(data.get("evidence_summary"), Mapping):
            errors.append("evidence_summary mapping is required")
        if not isinstance(data.get("metadata"), Mapping):
            errors.append("metadata mapping is required")
        for key in ("missing_requirements", "unsafe_conditions"):
            if not self._is_sequence(data.get(key)):
                errors.append(f"{key} list is required")

        approved = data.get("approved")
        status = data.get("decision")
        if approved is True and status != "approved_for_mock_only":
            errors.append("approved decision must be approved_for_mock_only")
        if status == "rejected" and approved is not False:
            errors.append("rejected decision must set approved false")
        if status not in {"approved_for_mock_only", "rejected"}:
            errors.append("decision must be approved_for_mock_only or rejected")
        if self._find_forbidden_paths(data):
            errors.append("decision contains forbidden raw fields")

        return {"valid": not errors, "errors": errors}

    def _find_forbidden_paths(self, value: Any) -> list[str]:
        found: list[str] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in self.forbidden_raw_keys:
                    found.append(str(key))
                found.extend(self._find_forbidden_paths(item))
        elif self._is_sequence(value):
            for item in value:
                found.extend(self._find_forbidden_paths(item))
        return found

    @staticmethod
    def _unique(items: list[Any]) -> list[Any]:
        result: list[Any] = []
        for item in items:
            if item not in result:
                result.append(item)
        return result

    @staticmethod
    def _is_sequence(value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


__all__ = ["RuntimeReadinessDecision"]
