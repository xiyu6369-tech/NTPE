from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits/architecture_consolidation/batch2_tests"

FROZEN_GROUPS = {
    "production": ("e33cd099619702b373488d9fd06ab6a96a1366f1d4cb89801ffbd30d0bb1ad01", ["launcher_translate.py", "ntpe_production_translate.py"]),
    "runtime": ("733235e9238fd04a4cd3473518fa3b71fd758a6b5e8e3ab060c48f01dded4aea", ["core/translation_runtime"]),
    "provider": ("52829739c49a18227c6647481c4dc87ae473281a9b42e0a9ab837237ab2a45d6", ["core/ai_provider"]),
    "prompt": ("5b0bc819f1f6fa6824751761e09a99a7bd6851c3c8070b5f87c0e7e5045f8c2b", ["core/prompt_compiler"]),
    "stage11": ("22beb3a54e3ef07e2d86d14d14e9d8115aca4f27db98c3ed19dea4ec8a9764b1", ["core/translation_quality_defects", "core/translation_quality_metrics", "core/translation_quality_review_artifacts", "core/translation_prompt_improvement_planner", "core/translation_quality_review_decision", "core/translation_quality_corpus_governance", "core/translation_quality_framework_integration", "core/translation_quality_corpus"]),
    "candidate": ("ec704fefd683b085e5086ae52bb6790a44881858584392ac844078afdcb5c98d", ["core/literary_prompt_quality_candidate_v72"]),
    "provider_evidence": ("ef8c56295fad9fb574cc8c6fd15d5f6ec187ee088533a2ba5b24e3bb1622d644", ["artifacts/te_v7_stage10101", "artifacts/te_v72_stage1221", "artifacts/te_v72_stage1222", "artifacts/te_v72_stage1223"]),
    "generated_translation": ("8e2466c4f6c592c647756a75657a9b3ea0c331493645bf39c31d96622ad4dc03", ["output", "translated", "final_output", "tests/literary/outputs"]),
}


def tree_digest(paths: list[str]) -> str:
    files: list[Path] = []
    for relative in paths:
        path = ROOT / relative
        files.extend(
            [path]
            if path.is_file()
            else [
                item
                for item in path.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            ]
        )
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def load(name: str) -> object:
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def dangling_test_references() -> list[str]:
    paths = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.py")}
    names = {Path(path).name for path in paths}
    pattern = re.compile(r"([A-Za-z0-9_./-]*(?:_test|test_[A-Za-z0-9_.-]*)\.py)")
    missing: set[str] = set()
    for base in (ROOT / "manifests", ROOT / "docs/releases"):
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            for reference in pattern.findall(text):
                reference = reference.lstrip("./")
                if reference not in paths and Path(reference).name not in names:
                    missing.add(reference)
    return sorted(missing)


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, condition: bool) -> None:
        checks.append((name, bool(condition)))

    required_audits = ["TEST_REFERENCE_MAP.json", "EXACT_DUPLICATES.json", "WRAPPER_ONLY_TESTS.json", "PARAMETERIZATION_CANDIDATES.json", "CRITICAL_TESTS_KEEP.json", "PROPOSED_TEST_DELETIONS.json", "TEST_CONSOLIDATION_REPORT.md"]
    check("required_reference_audits_exist", all((AUDIT / name).is_file() for name in required_audits))
    deletions = load("PROPOSED_TEST_DELETIONS.json")
    exact = load("EXACT_DUPLICATES.json")
    check("all_deletions_have_reference_audit", all(item.get("reference_audited") is True for item in deletions["deletions"]))
    check("all_deletions_are_exact_duplicates", all(item.get("classification") == "approved_low_risk_exact_duplicate" for item in deletions["deletions"]))
    check("eight_baseline_exact_duplicate_groups", len(exact["groups"]) == 8 and all(group["baseline_byte_identical"] for group in exact["groups"]))
    report = (AUDIT / "TEST_CONSOLIDATION_REPORT.md").read_text(encoding="utf-8")
    check("unique_assertions_removed_zero", "unique_assertions_removed: 0" in report)

    critical = load("CRITICAL_TESTS_KEEP.json")["tests"]
    critical_paths = {item["path"] for item in critical}
    check("critical_tests_exist", all((ROOT / path).is_file() for path in critical_paths))
    check("te_v6_freeze_exists", (ROOT / "ntpe_te_v600_final_release_freeze_test.py").is_file())
    check("stage118_freeze_exists", (ROOT / "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py").is_file())
    check("provider_security_exists", (ROOT / "ntpe_stage14_6_provider_security_test.py").is_file())
    check("runtime_tests_retained", any("runtime" in path.lower() for path in critical_paths))
    check("resume_recovery_tests_retained", any(any(term in path.lower() for term in ("resume", "recovery")) for path in critical_paths))
    check("output_integrity_tests_retained", any(any(term in path.lower() for term in ("output", "completeness", "hangul", "duplicate")) for path in critical_paths))

    wrapper = ROOT / "ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py"
    wrapper_tree = ast.parse(wrapper.read_text(encoding="utf-8"))
    check("wrapper_under_40_lines", len(wrapper.read_text(encoding="utf-8").splitlines()) < 40)
    check("wrapper_has_no_assertions", not any(isinstance(node, ast.Assert) for node in ast.walk(wrapper_tree)))
    wrapper_result = subprocess.run([sys.executable, str(wrapper)], cwd=ROOT, text=True, capture_output=True, check=False)
    check("compatibility_wrapper_directly_executable", wrapper_result.returncode == 0 and "ALL PASS" in wrapper_result.stdout)

    consolidated = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/consolidated/test_exact_duplicate_contracts.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    check("parameterized_stages_identifiable", consolidated.returncode == 0 and "8 passed" in consolidated.stdout)
    check("manifest_release_references_not_dangling", not dangling_test_references())

    for name, (expected, paths) in FROZEN_GROUPS.items():
        check(f"frozen_hash_{name}", tree_digest(paths) == expected)
    check("provider_not_executed", tree_digest(FROZEN_GROUPS["provider_evidence"][1]) == FROZEN_GROUPS["provider_evidence"][0])
    check("new_translation_not_generated", tree_digest(FROZEN_GROUPS["generated_translation"][1]) == FROZEN_GROUPS["generated_translation"][0])
    status = subprocess.run(["git", "status", "--porcelain", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.decode("utf-8", "replace").lower()
    check("batch3_not_started", "batch3" not in status and "batch_3" not in status)

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks):
        return 1
    print("NTPE Architecture Consolidation Batch 2 Test Consolidation ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
