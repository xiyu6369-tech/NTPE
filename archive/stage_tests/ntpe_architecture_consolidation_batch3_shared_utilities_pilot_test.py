from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audits/architecture_consolidation/batch3_shared"
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
        files.extend([path] if path.is_file() else [item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _shared_import_roots() -> set[str]:
    roots: set[str] = set()
    for path in (ROOT / "core/shared/evidence").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from core.shared.evidence import canonical_json_bytes, normalize_project_relative_path, require_sha256_hex, resolve_project_relative_path, sha256_bytes

    checks: list[tuple[str, bool]] = []
    check = lambda name, condition: checks.append((name, bool(condition)))
    required = ["SHARED_UTILITY_INVENTORY.json", "MIGRATION_MAP.json", "BEHAVIOR_PARITY_REPORT.json", "DEPENDENCY_REPORT.json", "VALIDATION_REPORT.txt", "CONSOLIDATION_REPORT.md"]
    check("shared_utility_importable", sha256_bytes(b"x") == hashlib.sha256(b"x").hexdigest())
    check("shared_standard_library_only", _shared_import_roots() <= {"__future__", "hashlib", "json", "ntpath", "os", "pathlib", "re", "tempfile"})
    check("canonical_json_deterministic", canonical_json_bytes({"b": 2, "a": "繁體"}) == canonical_json_bytes({"a": "繁體", "b": 2}))
    check("sha256_contract", require_sha256_hex(hashlib.sha256(b"contract").hexdigest()).islower())
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "evidence").mkdir()
        path_ok = normalize_project_relative_path(r"evidence\result.json") == "evidence/result.json" and resolve_project_relative_path(root, "evidence", allow_directory=True) == root / "evidence"
        try:
            resolve_project_relative_path(root, "../escape")
            path_ok = False
        except ValueError:
            pass
    check("path_containment", path_ok)
    source = (ROOT / "tools/package_source.py").read_text(encoding="utf-8")
    audit = (ROOT / "tools/package_audit.py").read_text(encoding="utf-8")
    check("source_packager_uses_shared", "from core.shared.evidence import" in source and "sha256_file(output)" in source)
    check("audit_packager_uses_shared", "from core.shared.evidence import" in audit and "require_sha256_hex" in audit)
    help_results = [subprocess.run([sys.executable, str(ROOT / path), "--help"], cwd=ROOT, text=True, capture_output=True, check=False) for path in ("tools/package_source.py", "tools/package_audit.py")]
    check("cli_compatible", all(result.returncode == 0 and "--root" in result.stdout and "--output" in result.stdout for result in help_results))
    check("package_report_schemas_compatible", all(key in source for key in ("tracked_only", "include_untracked", "unicode_round_trip")) and all(key in audit for key in ("manifest_validation", "integrity", "unicode_round_trip")))
    check("git_tracked_only_unchanged", 'arguments = ["ls-files", "-z", "--cached"]' in source)
    check("git_head_fail_closed", 'rev-parse", "--verify", "HEAD' in source and "Git HEAD is missing or invalid" in source)
    check("audit_allowlist_unchanged", "non-empty explicit files allowlist" in audit and 'set(entry) != {"path", "sha256"}' in audit)
    check("secret_protection_unchanged", "SECRET_PATTERNS" in audit and "secret-like content detected" in audit)
    check("traversal_protection_unchanged", "require_path_within_root" in source and "require_path_within_root" in audit)
    for name in ("production", "runtime", "provider", "prompt", "stage11", "candidate"):
        expected, paths = FROZEN_GROUPS[name]
        check(f"frozen_hash_{name}", tree_digest(paths) == expected)
    check("provider_not_executed", tree_digest(FROZEN_GROUPS["provider_evidence"][1]) == FROZEN_GROUPS["provider_evidence"][0])
    check("new_translation_not_generated", tree_digest(FROZEN_GROUPS["generated_translation"][1]) == FROZEN_GROUPS["generated_translation"][0])
    check("batch4_not_started", not any("batch4" in path.as_posix().lower() or "batch_4" in path.as_posix().lower() for path in ROOT.rglob("*")))
    check("migration_evidence_complete", all((AUDIT / name).is_file() for name in required))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks) or len(checks) < 23:
        return 1
    print("NTPE Architecture Consolidation Batch 3 Shared Utilities Pilot ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
