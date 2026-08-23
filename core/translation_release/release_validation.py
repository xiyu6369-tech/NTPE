from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.translation_discipline.freeze_readiness import evaluate_freeze_readiness
from core.translation_evidence import build_translation_evidence_freeze
from core.translation_naturalness import build_translation_naturalness_freeze

from .te_v6_release import build_te_v6_release_contract
from core.production_runtime.manifest import get_te_v7_stage_path


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def validate_te_v6_release(
    project_root: str | Path = ".",
    *,
    write_reports: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    baseline = root / "tests/literary/outputs/TE-v5.5.3-AdaptivePromptFeedback"
    current = root / "tests/literary/outputs/TE-v6.0-Stage10.1-ProductionValidation"
    regression = _read_json(current / "Literary_Regression_Report.json")
    summary = dict(regression.get("summary") or {})
    production_ok = (
        regression.get("stage") == "TE-v6.0-Stage10.1-ProductionValidation"
        and regression.get("status") == "success"
        and summary == {"total": 1, "success": 1, "skipped": 0, "failed": 0,
                        "dry_run": False, "elapsed_seconds": summary.get("elapsed_seconds")}
    )
    readiness = evaluate_freeze_readiness(baseline, current, expected_chunks=5).to_dict()
    evidence = build_translation_evidence_freeze()
    naturalness = build_translation_naturalness_freeze()
    blockers = list(readiness["blockers"])
    if not production_ok:
        blockers.append("Stage 10.1 Golden Set production validation is not successful")
    if not evidence.frozen:
        blockers.append("Stage 11.6 evidence freeze is not frozen")
    if not naturalness.to_metadata().get("frozen"):
        blockers.append("Stage 12.5 naturalness freeze is not frozen")
    contract = build_te_v6_release_contract(production_validated=production_ok)
    payload = {
        "stage": "TE-v6.0-Final-Release-Freeze", "version": contract.version,
        "channel": contract.channel, "ready": not blockers, "blockers": blockers,
        "contract": contract.to_dict(),
        "production_validation": {"stage": regression.get("stage"), "status": regression.get("status"), "sets": summary},
        "freeze_readiness": readiness,
        "evidence_freeze": evidence.to_metadata(), "naturalness_freeze": naturalness.to_metadata(),
        "network_activity": {"provider_client_created": False, "http_requests": 0, "nvidia_api_calls": 0},
    }
    if write_reports:
        # Use canonical validation output directory under artifacts
        out = get_te_v7_stage_path(root, "te_v6_0_final_validation")
        out.mkdir(parents=True, exist_ok=True)
        (out / "TE_V6_0_FINAL_VALIDATION.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = ["# TE v6.0 Final Validation", "", f"- Ready: `{str(payload['ready']).lower()}`",
                 f"- Blockers: `{len(blockers)}`", f"- Production validation: `{regression.get('status')}`",
                 f"- Sets: `{summary.get('success', 0)} success / {summary.get('skipped', 0)} skipped / {summary.get('failed', 0)} failed / {summary.get('total', 0)} total`",
                 f"- Freeze readiness: `ready={str(readiness['ready']).lower()}`", "", "No Provider client, HTTP request, or NVIDIA API call was made by final validation."]
        (out / "TE_V6_0_FINAL_VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
