from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .quality_repair_pipeline import QualityRepairPipeline
from .quality_runtime_gate_admission import QualityRuntimeGateAdmission
from .quality_runtime_gate_decision import QualityRuntimeGateDecision


class QualityRuntimeGatePilot:
    version = "TE-v5.2"
    stage = "5.2.4"

    def __init__(self) -> None:
        self.admission = QualityRuntimeGateAdmission()
        self.repair = QualityRepairPipeline()
        self.decision = QualityRuntimeGateDecision()

    def run(
        self,
        request: Optional[Mapping[str, Any]],
        *,
        contract: Optional[Mapping[str, Any]],
        flag_state: Optional[Mapping[str, Any]],
        source_text: Optional[str],
        translated_text: Optional[str],
        locked_terms: Optional[Mapping[str, str]] = None,
        forbidden_variants: Optional[Mapping[str, list[str]]] = None,
        runtime_state: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        admission_result = self.admission.evaluate(
            request=request,
            contract=contract,
            flag_state=flag_state,
        )

        if not self.admission.is_admitted(admission_result):
            gate_decision = self.decision.decide(admission_result, {})
            return {
                "stage": self.stage,
                "status": "gate_blocked",
                "admission_result": admission_result,
                "repair_result": {},
                "gate_decision": gate_decision,
                "runtime_result_unchanged": True,
                "source_text_retained": False,
                "translated_text_retained": False,
            }

        repair_result = self.repair.run(
            source_text,
            translated_text,
            locked_terms=locked_terms,
            forbidden_variants=forbidden_variants,
            runtime_state=runtime_state,
            config=config,
        )
        gate_decision = self.decision.decide(admission_result, repair_result)

        return {
            "stage": self.stage,
            "status": f"gate_{gate_decision['decision']}",
            "admission_result": admission_result,
            "repair_result": repair_result,
            "gate_decision": gate_decision,
            "runtime_result_unchanged": True,
            "source_text_retained": False,
            "translated_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "stage", "status", "admission_result",
            "repair_result", "gate_decision",
            "runtime_result_unchanged",
            "source_text_retained", "translated_text_retained",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if not self.admission.validate_result(result.get("admission_result")):
            return False
        if not self.decision.validate_result(result.get("gate_decision")):
            return False
        if result.get("repair_result"):
            if not self.repair.validate_result(result.get("repair_result")):
                return False
        return (
            result.get("runtime_result_unchanged") is True
            and result.get("source_text_retained") is False
            and result.get("translated_text_retained") is False
        )
