from __future__ import annotations

import json
from pathlib import Path

from core.translation_evidence import (
    ALIGNMENT_ENGINE_VERSION,
    EVIDENCE_ENGINE_VERSION,
    EVIDENCE_FREEZE_VERSION,
    EVIDENCE_FROZEN_STAGES,
    TranslationEvidenceFreeze,
    build_alignment_evidence,
    build_source_translation_alignment,
    build_translation_evidence,
    build_translation_evidence_freeze,
)
from core.translation_discipline import (
    EVIDENCE_AUDIT_VERSION,
    EVIDENCE_RETRY_INTEGRATION_VERSION,
    TARGETED_MERGE_VALIDATION_VERSION,
    build_evidence_audit_trail,
    integrate_alignment_evidence_for_retry,
    validate_targeted_merge,
)


def check(name: str, condition: bool) -> None:
    print(f"{name:<58} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main() -> int:
    print("NTPE TE v6.0 Stage 11.6 Translation Evidence Freeze")
    print("=" * 76)
    root = Path(__file__).resolve().parent
    manifest_path = root / "manifests" / "te_v611_stage116_translation_evidence_freeze_manifest.json"
    check("Freeze manifest exists", manifest_path.exists())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    freeze = build_translation_evidence_freeze()
    check("Freeze object exported", isinstance(freeze, TranslationEvidenceFreeze))
    check("Freeze version correct", freeze.version == EVIDENCE_FREEZE_VERSION == manifest["version"])
    check("Frozen stage inventory complete", freeze.stages == EVIDENCE_FROZEN_STAGES == tuple(manifest["stages"]))
    check("Evidence engine API import", bool(EVIDENCE_ENGINE_VERSION) and callable(build_translation_evidence))
    check("Alignment API import", bool(ALIGNMENT_ENGINE_VERSION) and callable(build_source_translation_alignment) and callable(build_alignment_evidence))
    check("Evidence-to-retry API import", bool(EVIDENCE_RETRY_INTEGRATION_VERSION) and callable(integrate_alignment_evidence_for_retry))
    check("Targeted merge validation API import", bool(TARGETED_MERGE_VALIDATION_VERSION) and callable(validate_targeted_merge))
    check("Evidence audit API import", bool(EVIDENCE_AUDIT_VERSION) and callable(build_evidence_audit_trail))
    compatibility = manifest["compatibility"]
    check("Provider and prompt contracts unchanged", compatibility["provider_calls_added"] == 0 and not compatibility["prompt_text_changed"] and not compatibility["prompt_token_profile_changed"])
    check("Quality and retry contracts unchanged", not compatibility["quality_score_changed"] and not compatibility["quality_decision_changed"] and not compatibility["retry_tier_changed"] and not compatibility["provider_budget_changed"])
    check("Runtime resilience unchanged", not compatibility["timeout_changed"] and not compatibility["resume_changed"])
    check("Fail-closed policy frozen", compatibility["fail_closed"] is True)
    check("NVIDIA RPM ceiling preserved", compatibility["nvidia_rpm_ceiling"] == 40)
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
