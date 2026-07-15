from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits/architecture_consolidation/batch5a1_parity"
STATUSES = ("PARITY_PROVEN", "PARITY_PARTIAL", "PARITY_FAILED", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
REQUIRED = (
    "BATCH5A1_REPLACEMENT_PARITY_AUDIT.md", "BATCH5A1_REPLACEMENT_PARITY_AUDIT.json",
    "LEGACY_REPLACEMENT_MAP.json", "PUBLIC_SYMBOL_PARITY.json", "BEHAVIOR_PARITY.json",
    "SIDE_EFFECT_PARITY.json", "EXCEPTION_PARITY.json", "REPLACEMENT_PERFORMANCE_REPORT.json",
    "QUALITY_IMPACT_PARITY.json", "EXTERNAL_COMPATIBILITY_PARITY.json", "COMPATIBILITY_WRAPPER_DESIGN.json",
    "BATCH5B_PARITY_BASED_PLAN.json", "BATCH5B_PARITY_BASED_PLAN.md",
) + tuple(f"{status}.json" for status in STATUSES)
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
    mapping = load("LEGACY_REPLACEMENT_MAP.json")
    check("three_domains_mapped", mapping["count"] == 3 and {row["domain"] for row in mapping["items"]} == {"context", "narrative", "voice"})
    check("each_domain_has_replacement", all(row["replacement_module"] == "core.literary" for row in mapping["items"]))
    symbols = load("PUBLIC_SYMBOL_PARITY.json")
    check("public_symbols_audited", symbols["scan_status"] == "COMPLETE" and symbols["count"] >= 12)
    behavior = load("BEHAVIOR_PARITY.json")
    check("behavior_fixtures_complete", behavior["domain_count"] == 3 and behavior["case_count"] == 30)
    check("normal_behavior_characterized", all(row["normal_behavior_parity"] is False for row in behavior["items"]))
    check("edge_behavior_characterized", all(row["edge_behavior_parity"] is False for row in behavior["items"]))
    check("exception_parity_complete", load("EXCEPTION_PARITY.json")["scan_status"] == "COMPLETE" and len(load("EXCEPTION_PARITY.json")["items"]) == 3)
    check("mutation_parity_complete", all(row["mutation_parity"] for row in behavior["items"]))
    check("side_effect_parity_complete", load("SIDE_EFFECT_PARITY.json")["scan_status"] == "COMPLETE")
    performance = load("REPLACEMENT_PERFORMANCE_REPORT.json")
    check("performance_benchmark_complete", performance["performance_gate_pass"] is True and all(row["iterations"] >= 300 and row["warmup_iterations"] >= 30 for row in performance["items"]))
    check("quality_impact_complete", load("QUALITY_IMPACT_PARITY.json")["scan_status"] == "COMPLETE")
    check("external_compatibility_complete", all(row["risk"] == "HIGH" and row["legacy_import_path_must_remain"] for row in load("EXTERNAL_COMPATIBILITY_PARITY.json")["items"]))
    check("wrapper_feasibility_complete", load("COMPATIBILITY_WRAPPER_DESIGN.json")["scan_status"] == "COMPLETE")
    partitions = {status: load(f"{status}.json") for status in STATUSES}
    check("one_status_per_domain", sum(row["count"] for row in partitions.values()) == 3 and sum(len(row["items"]) for row in partitions.values()) == 3)
    proven = partitions["PARITY_PROVEN"]["items"]
    check("parity_proven_hard_conditions", all(symbols["coverage_percent"] == 100.0 and performance["performance_gate_pass"] for _ in proven))
    plan = load("BATCH5B_PARITY_BASED_PLAN.json")
    check("batch5b_limit", plan["item_count"] <= plan["item_limit"] <= 2)
    check("batch5b_proven_only", all(item.get("status") == "PARITY_PROVEN" for item in plan["items"]))
    check("batch5b_excludes_deferred_domains", not {"runtime", "workflow", "prompt_builder", "quality"}.intersection(item.get("domain") for item in plan["items"]))
    check("batch5b_not_started", plan["batch5b_started"] is False)
    summary = load("BATCH5A1_REPLACEMENT_PARITY_AUDIT.json")
    check("domain_statuses", summary["context_parity_status"] == "PARITY_FAILED" and summary["narrative_parity_status"] == summary["voice_parity_status"] == "PARITY_PARTIAL")
    check("production_legacy_replacement_unchanged", not summary["production_code_modified"] and not summary["legacy_modules_modified"] and not summary["replacement_modules_modified"])
    check("provider_not_executed", summary["provider_executed"] is False)
    check("new_translation_not_generated", summary["new_translation_generated"] is False)
    for name, (expected, paths) in GROUPS.items():
        check(f"frozen_hash_{name}", tree_digest(paths) == expected)
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks) or len(checks) < 26:
        return 1
    print("NTPE Architecture Consolidation Batch 5A.1 Replacement Parity ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
