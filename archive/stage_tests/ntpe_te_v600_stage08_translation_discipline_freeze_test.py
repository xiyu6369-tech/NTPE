from __future__ import annotations

import json
from pathlib import Path

from core.translation_discipline import (
    DISCIPLINE_AUDIT_VERSION,
    DISCIPLINE_FREEZE_VERSION,
    DISCIPLINE_FROZEN_STAGES,
    LOCAL_REPAIR_FRAMEWORK_VERSION,
    POLICY_VERSION,
    QUALITY_ENFORCEMENT_VERSION,
    RETRY_DECISION_ENGINE_VERSION,
    RUNTIME_ORCHESTRATOR_VERSION,
    AdaptiveLocalRepairFramework,
    AdaptiveRetryDecisionEngine,
    DisciplineAuditTrail,
    DisciplineQualityEnforcer,
    TranslationDisciplineEngine,
    TranslationDisciplineRuntimeOrchestrator,
    build_translation_discipline_freeze,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<55} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("NTPE TE v6.0 Stage 08 Translation Discipline Freeze")
    print("=" * 72)
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v600_stage08_translation_discipline_freeze_manifest.json"
    check("Freeze manifest exists", manifest_path.exists())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    freeze = build_translation_discipline_freeze()
    check("Freeze enabled", manifest["frozen"] is True and freeze.frozen is True)
    check("Freeze version correct", manifest["version"] == DISCIPLINE_FREEZE_VERSION)
    check("Frozen stage inventory complete", tuple(manifest["stages"]) == DISCIPLINE_FROZEN_STAGES)
    check("Policy layer import", TranslationDisciplineEngine is not None and POLICY_VERSION)
    check("Quality enforcement import", DisciplineQualityEnforcer is not None and QUALITY_ENFORCEMENT_VERSION)
    check("Local repair import", AdaptiveLocalRepairFramework is not None and LOCAL_REPAIR_FRAMEWORK_VERSION)
    check("Retry decision import", AdaptiveRetryDecisionEngine is not None and RETRY_DECISION_ENGINE_VERSION)
    check("Runtime orchestrator import", TranslationDisciplineRuntimeOrchestrator is not None and RUNTIME_ORCHESTRATOR_VERSION)
    check("Audit trail import", DisciplineAuditTrail is not None and DISCIPLINE_AUDIT_VERSION)
    compatibility = manifest["compatibility"]
    check("Provider behavior unchanged", compatibility["provider_calls_added"] == 0)
    check("Prompt contract unchanged", compatibility["prompt_text_changed"] is False and compatibility["prompt_token_profile_changed"] is False)
    check("Quality contract unchanged", compatibility["quality_score_changed"] is False and compatibility["quality_decision_changed"] is False)
    check("Runtime resilience unchanged", compatibility["timeout_changed"] is False and compatibility["retry_policy_changed"] is False and compatibility["resume_changed"] is False)
    check("NVIDIA RPM ceiling preserved", compatibility["nvidia_rpm_ceiling"] == 40)
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
