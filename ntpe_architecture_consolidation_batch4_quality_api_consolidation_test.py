from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import runpy
import subprocess


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits/architecture_consolidation/batch4_quality"
GROUPS = {
    "stage11_modules": ("22beb3a54e3ef07e2d86d14d14e9d8115aca4f27db98c3ed19dea4ec8a9764b1", ["core/translation_quality_defects", "core/translation_quality_metrics", "core/translation_quality_review_artifacts", "core/translation_prompt_improvement_planner", "core/translation_quality_review_decision", "core/translation_quality_corpus_governance", "core/translation_quality_framework_integration", "core/translation_quality_corpus"]),
    "stage11_artifacts": ("2c12d000d1b0382bdbf82779f5249ac60ebf138a1463b917b92533c44bbd915d", ["artifacts/te_v71_stage111", "artifacts/te_v71_stage112", "artifacts/te_v71_stage113", "artifacts/te_v71_stage114", "artifacts/te_v71_stage115", "artifacts/te_v71_stage116", "artifacts/te_v71_stage117", "artifacts/te_v71_stage118"]),
    "stage11_manifests": ("f69fe483751344bacf52805123dd9b8e9a62baf317caf0c7e67d59c5cbde77b2", ["manifests/te_v710_stage111_translation_defect_classification_manifest.json", "manifests/te_v710_stage112_translation_quality_metrics_manifest.json", "manifests/te_v710_stage113_quality_review_artifacts_manifest.json", "manifests/te_v710_stage114_prompt_improvement_planner_manifest.json", "manifests/te_v710_stage115_review_decision_contract_manifest.json", "manifests/te_v710_stage116_golden_corpus_governance_manifest.json", "manifests/te_v710_stage117_quality_framework_integration_manifest.json", "manifests/te_v710_stage118_translation_quality_framework_freeze_manifest.json"]),
    "production": ("e33cd099619702b373488d9fd06ab6a96a1366f1d4cb89801ffbd30d0bb1ad01", ["launcher_translate.py", "ntpe_production_translate.py"]),
    "runtime": ("733235e9238fd04a4cd3473518fa3b71fd758a6b5e8e3ab060c48f01dded4aea", ["core/translation_runtime"]),
    "provider": ("52829739c49a18227c6647481c4dc87ae473281a9b42e0a9ab837237ab2a45d6", ["core/ai_provider"]),
    "prompt": ("5b0bc819f1f6fa6824751761e09a99a7bd6851c3c8070b5f87c0e7e5045f8c2b", ["core/prompt_compiler"]),
    "candidate": ("ec704fefd683b085e5086ae52bb6790a44881858584392ac844078afdcb5c98d", ["core/literary_prompt_quality_candidate_v72"]),
    "generated_translation": ("8e2466c4f6c592c647756a75657a9b3ea0c331493645bf39c31d96622ad4dc03", ["output", "translated", "final_output", "tests/literary/outputs"]),
}


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
    from ntpe.corpus import manage
    from ntpe.quality import assess, build_review_view
    from core.translation_quality_defects import TranslationDefect
    from core.translation_quality_framework_integration import QualityFrameworkIntegration

    paths = {
        "defects": ROOT / "artifacts/te_v71_stage111/TE_V71_STAGE111_TRANSLATION_DEFECTS.json",
        "metrics": ROOT / "artifacts/te_v71_stage112/TE_V71_STAGE112_QUALITY_METRICS.json",
        "review": ROOT / "artifacts/te_v71_stage113/TE_V71_STAGE113_REVIEW.json",
        "plans": ROOT / "artifacts/te_v71_stage114/TE_V71_STAGE114_PROMPT_IMPROVEMENT_PLAN.json",
        "decision": ROOT / "artifacts/te_v71_stage115/TE_V71_STAGE115_REVIEW_DECISION_CONTRACT.json",
        "corpus": ROOT / "quality_corpus/golden_review/te_v71_initial_defects.json",
        "governance": ROOT / "artifacts/te_v71_stage116/TE_V71_STAGE116_GOLDEN_CORPUS_GOVERNANCE.json",
    }
    before = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    before_count = sum(1 for base in (ROOT / "artifacts", ROOT / "quality_corpus") for path in base.rglob("*") if path.is_file())
    assessment = assess(defects=paths["defects"], metrics=paths["metrics"])
    review = build_review_view(review_artifact=paths["review"], improvement_plans=paths["plans"], human_decision=paths["decision"])
    corpus = manage(corpus=paths["corpus"], governance_record=paths["governance"])
    after = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    after_count = sum(1 for base in (ROOT / "artifacts", ROOT / "quality_corpus") for path in base.rglob("*") if path.is_file())
    benchmark = runpy.run_path(str(ROOT / "tests/performance/quality_api_facade_benchmark.py"))["run_benchmark"](iterations=300, warmup_iterations=30)
    checks: list[tuple[str, bool]] = []
    check = lambda name, condition: checks.append((name, bool(condition)))
    check("quality_assess_importable", callable(assess))
    check("quality_review_importable", callable(build_review_view))
    check("corpus_manage_importable", callable(manage))
    try:
        assessment.overall_score = 100.0  # type: ignore[misc]
        readonly = False
    except (FrozenInstanceError, AttributeError):
        readonly = True
    check("facade_read_only", readonly and not any(hasattr(corpus, name) for name in ("approve", "reject", "save")))
    check("legacy_apis_importable", TranslationDefect.__name__ == "TranslationDefect" and QualityFrameworkIntegration.__name__ == "QualityFrameworkIntegration")
    check("stage11_module_hashes", tree_digest(GROUPS["stage11_modules"][1]) == GROUPS["stage11_modules"][0])
    check("stage11_artifact_hashes", tree_digest(GROUPS["stage11_artifacts"][1]) == GROUPS["stage11_artifacts"][0])
    check("stage11_manifest_hashes", tree_digest(GROUPS["stage11_manifests"][1]) == GROUPS["stage11_manifests"][0])
    check("golden_corpus_hash", before["corpus"] == "4a06d256d900c8bb7706098fd79f2d53889d469e9b62516d81334ef34433f2cc")
    check("defect_count_parity", len(assessment.defects) == 6)
    check("metrics_score_parity", assessment.overall_score == 41.91)
    check("blocking_parity", assessment.blocking_defect_count == 1)
    check("insufficient_evidence_parity", assessment.insufficient_evidence_dimensions == ("dialogue", "terminology"))
    check("review_plan_status_parity", len(review.improvement_plans) == 6 and {row.implementation_status for row in review.improvement_plans} == {"planned_not_applied"})
    check("human_decision_parity", review.human_decision is not None and review.human_decision.decision.value == "accepted" and not review.decision_applied)
    check("corpus_count_parity", len(corpus.cases) == 6 and corpus.approved_case_count == corpus.approved_translation_count == 0)
    check("accepted_not_corpus_approval", not review.corpus_approval_granted)
    check("provider_request_delta_zero", benchmark["provider_requests_delta"] == 0)
    check("prompt_token_delta_zero", benchmark["prompt_tokens_delta"] == 0)
    check("disk_write_delta_zero", before == after and benchmark["disk_writes_delta"] == 0)
    check("artifact_count_delta_zero", before_count == after_count and benchmark["artifact_count_delta"] == 0)
    check("runtime_path_unchanged", tree_digest(GROUPS["runtime"][1]) == GROUPS["runtime"][0] and benchmark["runtime_stage_delta"] == 0)
    check("facade_benchmark_pass", benchmark["performance_gate_pass"] is True)
    check("production_code_unchanged", tree_digest(GROUPS["production"][1]) == GROUPS["production"][0])
    check("prompt_unchanged", tree_digest(GROUPS["prompt"][1]) == GROUPS["prompt"][0])
    check("provider_unchanged", tree_digest(GROUPS["provider"][1]) == GROUPS["provider"][0])
    check("candidate_unchanged", tree_digest(GROUPS["candidate"][1]) == GROUPS["candidate"][0])
    check("new_translation_not_generated", tree_digest(GROUPS["generated_translation"][1]) == GROUPS["generated_translation"][0])
    status = subprocess.run(["git", "status", "--porcelain", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8", "replace").lower()
    check("batch5_not_started", "batch5" not in status and "batch_5" not in status)

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks) or len(checks) < 29:
        return 1
    print("NTPE Architecture Consolidation Batch 4 Quality API Consolidation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

