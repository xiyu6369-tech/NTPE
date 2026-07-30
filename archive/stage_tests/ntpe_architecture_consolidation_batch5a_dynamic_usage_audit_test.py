from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits/architecture_consolidation/batch5a_usage"
CLASSES = ("SAFE_DELETE", "KEEP_COMPATIBILITY", "MERGE", "ARCHIVE", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
REQUIRED = (
    "BATCH5A_DYNAMIC_USAGE_AUDIT.md", "BATCH5A_DYNAMIC_USAGE_AUDIT.json",
    "PRODUCTION_ENTRYPOINT_MAP.json", "DYNAMIC_IMPORT_REPORT.json", "REGISTRY_USAGE_REPORT.json",
    "SERIALIZED_REFERENCE_REPORT.json", "CONFIGURATION_REFERENCE_REPORT.json",
    "EXTERNAL_COMPATIBILITY_RISK.json", "REPLACEMENT_PARITY_REPORT.json",
    "QUALITY_PERFORMANCE_IMPACT_REPORT.json", "BATCH5B_SAFE_SIMPLIFICATION_PLAN.json",
    "BATCH5B_SAFE_SIMPLIFICATION_PLAN.md",
) + tuple(f"{name}.json" for name in CLASSES)
GROUPS = {
    "production": ("e33cd099619702b373488d9fd06ab6a96a1366f1d4cb89801ffbd30d0bb1ad01", ["launcher_translate.py", "ntpe_production_translate.py"]),
    "runtime": ("733235e9238fd04a4cd3473518fa3b71fd758a6b5e8e3ab060c48f01dded4aea", ["core/translation_runtime"]),
    "provider": ("52829739c49a18227c6647481c4dc87ae473281a9b42e0a9ab837237ab2a45d6", ["core/ai_provider"]),
    "prompt": ("5b0bc819f1f6fa6824751761e09a99a7bd6851c3c8070b5f87c0e7e5045f8c2b", ["core/prompt_compiler"]),
    "stage11": ("22beb3a54e3ef07e2d86d14d14e9d8115aca4f27db98c3ed19dea4ec8a9764b1", ["core/translation_quality_defects", "core/translation_quality_metrics", "core/translation_quality_review_artifacts", "core/translation_prompt_improvement_planner", "core/translation_quality_review_decision", "core/translation_quality_corpus_governance", "core/translation_quality_framework_integration", "core/translation_quality_corpus"]),
    "candidate": ("ec704fefd683b085e5086ae52bb6790a44881858584392ac844078afdcb5c98d", ["core/literary_prompt_quality_candidate_v72"]),
    "provider_evidence": ("ef8c56295fad9fb574cc8c6fd15d5f6ec187ee088533a2ba5b24e3bb1622d644", ["artifacts/te_v7_stage10101", "artifacts/te_v72_stage1221", "artifacts/te_v72_stage1222", "artifacts/te_v72_stage1223"]),
    "generated_translation": ("8e2466c4f6c592c647756a75657a9b3ea0c331493645bf39c31d96622ad4dc03", ["output", "translated", "final_output", "tests/literary/outputs"]),
}
HIGH_RISK = {"core/chunker.py", "core/glossary.py", "core/translator.py", "core/prompt_engine.py", "core/formatter.py", "core/exceptions.py", "core/character_memory_engine.py"}


def load(name: str) -> dict:
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def tree_digest(paths: list[str]) -> str:
    files: list[Path] = []
    for relative in paths:
        path = ROOT / relative
        files.extend([path] if path.is_file() else [item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> int:
    checks: list[tuple[str, bool]] = []
    check = lambda name, value: checks.append((name, bool(value)))
    check("audit_inventory_complete", all((AUDIT / name).is_file() for name in REQUIRED))
    payloads = {name: load(f"{name}.json") for name in CLASSES}
    items = [item for name in CLASSES for item in payloads[name]["items"]]
    paths = [item["module_path"] for item in items]
    check("candidate_inventory_72_unique", len(paths) == len(set(paths)) == 72)
    check("classification_partition_complete", all(payloads[name]["count"] == len(payloads[name]["items"]) for name in CLASSES))
    safe = payloads["SAFE_DELETE"]["items"]
    check("safe_delete_hard_conditions", all(item["active_repository_reference_count"] == 0 and item["external_compatibility_risk"] == "LOW" and item["replacement_parity"]["behavior_parity"] == "proven" for item in safe))
    check("high_risk_not_safe_delete", not HIGH_RISK.intersection(item["module_path"] for item in safe))
    for report in ("DYNAMIC_IMPORT_REPORT.json", "REGISTRY_USAGE_REPORT.json", "SERIALIZED_REFERENCE_REPORT.json", "CONFIGURATION_REFERENCE_REPORT.json", "EXTERNAL_COMPATIBILITY_RISK.json", "REPLACEMENT_PARITY_REPORT.json", "QUALITY_PERFORMANCE_IMPACT_REPORT.json"):
        check(f"{report}_complete", load(report).get("scan_status") == "COMPLETE")
    check("dynamic_fail_closed_evidence", load("DYNAMIC_IMPORT_REPORT.json")["unresolved_count"] > 0)
    check("registry_inventory_present", load("REGISTRY_USAGE_REPORT.json")["count"] > 0)
    check("serialized_inventory_72", load("SERIALIZED_REFERENCE_REPORT.json")["count"] == 72)
    check("external_risk_inventory_72", load("EXTERNAL_COMPATIBILITY_RISK.json")["count"] == 72)
    check("replacement_parity_inventory_72", load("REPLACEMENT_PARITY_REPORT.json")["count"] == 72)
    check("quality_performance_inventory_72", load("QUALITY_PERFORMANCE_IMPACT_REPORT.json")["count"] == 72)
    plan = load("BATCH5B_SAFE_SIMPLIFICATION_PLAN.json")
    check("batch5b_item_limit", plan["item_count"] <= plan["item_limit"] <= 5)
    check("batch5b_excludes_high_risk", not HIGH_RISK.intersection(item.get("path") for item in plan["items"]))
    check("batch5b_not_started", plan["batch5b_started"] is False)
    summary = load("BATCH5A_DYNAMIC_USAGE_AUDIT.json")
    check("provider_not_executed_flag", summary["provider_executed"] is False)
    check("production_not_modified_flag", summary["production_modified"] is False)
    check("new_translation_not_generated_flag", summary["new_translation_generated"] is False)
    for name, (expected, paths_) in GROUPS.items():
        check(f"frozen_hash_{name}", tree_digest(paths_) == expected)
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks) or len(checks) < 29:
        return 1
    print("NTPE Architecture Consolidation Batch 5A Dynamic Usage Audit ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
