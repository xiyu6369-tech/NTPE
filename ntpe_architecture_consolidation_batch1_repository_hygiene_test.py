from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from tools.package_audit import PackageError as AuditPackageError
from tools.package_audit import build_audit_package, load_manifest, sha256_file
from tools.package_source import build_source_package, is_source_path


ROOT = Path(__file__).resolve().parent

FROZEN_GROUPS = {
    "production_runtime": (
        "2fbd99851ac1da5f3ada6283110d51634d762b01bf608c432f4b8deaa4920143",
        [
            "launcher_translate.py",
            "ntpe_production_translate.py",
            "core/translation_runtime",
            "core/ai_provider",
            "core/literary",
            "core/prompt_compiler",
            "core/translation_reliability",
            "core/translation_naturalness",
            "core/translation_quality_v5",
            "core/translation_discipline",
            "core/translation_resources",
            "core/translation_engine",
            "core/adaptive_context",
            "lts",
        ],
    ),
    "stage11_quality_framework": (
        "22beb3a54e3ef07e2d86d14d14e9d8115aca4f27db98c3ed19dea4ec8a9764b1",
        [
            "core/translation_quality_defects",
            "core/translation_quality_metrics",
            "core/translation_quality_review_artifacts",
            "core/translation_prompt_improvement_planner",
            "core/translation_quality_review_decision",
            "core/translation_quality_corpus_governance",
            "core/translation_quality_framework_integration",
            "core/translation_quality_corpus",
        ],
    ),
    "v72_candidate": (
        "ec704fefd683b085e5086ae52bb6790a44881858584392ac844078afdcb5c98d",
        ["core/literary_prompt_quality_candidate_v72"],
    ),
    "provider_evidence": (
        "ef8c56295fad9fb574cc8c6fd15d5f6ec187ee088533a2ba5b24e3bb1622d644",
        [
            "artifacts/te_v7_stage10101",
            "artifacts/te_v72_stage1221",
            "artifacts/te_v72_stage1222",
            "artifacts/te_v72_stage1223",
        ],
    ),
    "generated_translation_evidence": (
        "8e2466c4f6c592c647756a75657a9b3ea0c331493645bf39c31d96622ad4dc03",
        ["output", "translated", "final_output", "tests/literary/outputs"],
    ),
}


def tree_digest(paths: list[str]) -> str:
    files: list[Path] = []
    for relative in paths:
        candidate = ROOT / relative
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                path
                for path in candidate.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def expect_audit_failure(root: Path, manifest_data: object) -> bool:
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    try:
        load_manifest(root, manifest)
    except AuditPackageError:
        return True
    return False


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def check(name: str, condition: bool) -> None:
        checks.append((name, bool(condition)))

    check("legacy_ntpe_zip_absent", not (ROOT / "NTPE.zip").exists())
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "NTPE.zip"], cwd=ROOT, check=False
    ).returncode == 0
    check("legacy_ntpe_zip_gitignored", ignored)

    delivery = (ROOT / "docs/architecture/NTPE_DELIVERY_PACKAGE_POLICY.md").read_text(encoding="utf-8")
    retention = (ROOT / "docs/architecture/NTPE_ARTIFACT_RETENTION_POLICY.md").read_text(encoding="utf-8")
    check("delivery_policy_present", all(term in delivery for term in ("Source Package", "Audit Package", "Full Repository Backup")))
    check(
        "source_policy_defaults_to_tracked_only",
        "Git tracked files only" in delivery
        and "git ls-files --cached" in delivery
        and "--include-untracked" in delivery,
    )
    check("retention_policy_present", all(term in retention for term in ("Active", "Audit", "Rebuildable", "Delete-eligible")))
    check("no_full_backup_tool", not (ROOT / "tools/package_backup.py").exists())

    forbidden_source = [
        ".git/config",
        "artifacts/provider_response.json",
        "tests/literary/outputs/generated.txt",
        "cache/item.bin",
        ".env",
        "config/config.json",
        "resume_state.json",
        "nested.zip",
    ]
    check("source_excludes_git", not is_source_path(forbidden_source[0]))
    check("source_excludes_provider_evidence", not is_source_path(forbidden_source[1]))
    check("source_excludes_generated_outputs", not is_source_path(forbidden_source[2]))
    check("source_excludes_other_zip", not is_source_path(forbidden_source[-1]))
    check("source_excludes_cache_and_private_data", all(not is_source_path(path) for path in forbidden_source[3:-1]))
    check("source_includes_supported_code", is_source_path("core/example.py") and is_source_path("docs/architecture/繁體中文.md"))

    with tempfile.TemporaryDirectory(prefix="ntpe_batch1_") as temporary:
        sandbox = Path(temporary)
        (sandbox / "core").mkdir()
        (sandbox / "docs/architecture").mkdir(parents=True)
        (sandbox / "core/tracked.py").write_text("TRACKED = True\n", encoding="utf-8")
        (sandbox / "docs/architecture/繁體中文.md").write_text("測試\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=sandbox, check=True)
        subprocess.run(
            ["git", "add", "--", "core/tracked.py", "docs/architecture/繁體中文.md"],
            cwd=sandbox,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=NTPE Test",
                "-c",
                "user.email=ntpe-test@example.invalid",
                "commit",
                "-qm",
                "tracked source fixture",
            ],
            cwd=sandbox,
            check=True,
        )
        git_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=sandbox, check=True, text=True, capture_output=True
        ).stdout.strip()
        (sandbox / "core/local_experiment.py").write_text("LOCAL = True\n", encoding="utf-8")

        source_result = build_source_package(sandbox, sandbox / "source.zip")
        with zipfile.ZipFile(sandbox / "source.zip") as archive:
            default_inventory = archive.namelist()
        rebuilt_result = build_source_package(sandbox, sandbox / "source-rebuilt.zip")
        with zipfile.ZipFile(sandbox / "source-rebuilt.zip") as archive:
            rebuilt_inventory = archive.namelist()
        opt_in_result = build_source_package(
            sandbox, sandbox / "source-opt-in.zip", include_untracked=True
        )
        with zipfile.ZipFile(sandbox / "source-opt-in.zip") as archive:
            opt_in_inventory = archive.namelist()

        check("source_default_excludes_allowlisted_untracked", "core/local_experiment.py" not in default_inventory)
        check("source_default_includes_tracked", "core/tracked.py" in default_inventory)
        check("source_same_head_rebuilds_same_inventory", default_inventory == rebuilt_inventory and source_result["git_head"] == rebuilt_result["git_head"])
        check("source_report_preserves_git_head", source_result["git_head"] == git_head)
        check("source_report_marks_tracked_only", source_result["tracked_only"] is True and source_result["include_untracked"] is False)
        check("source_untracked_requires_explicit_opt_in", "core/local_experiment.py" in opt_in_inventory and opt_in_result["include_untracked"] is True and opt_in_result["tracked_only"] is False)
        check("source_zip_integrity_and_unicode", all(source_result[key] == "PASS" for key in ("integrity", "path_separator_validation", "unicode_round_trip")))

        check("audit_requires_explicit_allowlist", expect_audit_failure(sandbox, {"schema_version": "1.0", "files": []}))
        check(
            "audit_rejects_traversal",
            expect_audit_failure(sandbox, {"schema_version": "1.0", "files": [{"path": "../escape", "sha256": "0" * 64}]}),
        )
        digest = sha256_file(sandbox / "core/tracked.py")
        check(
            "audit_rejects_duplicates",
            expect_audit_failure(
                sandbox,
                {"schema_version": "1.0", "files": [{"path": "core/tracked.py", "sha256": digest}, {"path": "CORE/TRACKED.PY", "sha256": digest}]},
            ),
        )
        secret_value = "OPENAI_API_KEY=" + "sk-" + ("a" * 24)
        (sandbox / "secret.txt").write_text(secret_value, encoding="utf-8")
        check(
            "audit_rejects_secret_content",
            expect_audit_failure(sandbox, {"schema_version": "1.0", "files": [{"path": "secret.txt", "sha256": sha256_file(sandbox / "secret.txt")}]}),
        )
        manifest_data = {
            "schema_version": "1.0",
            "files": [
                {"path": "core/tracked.py", "sha256": digest},
                {"path": "docs/architecture/繁體中文.md", "sha256": sha256_file(sandbox / "docs/architecture/繁體中文.md")},
            ],
        }
        manifest = sandbox / "audit-manifest.json"
        manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
        audit_result = build_audit_package(sandbox, manifest, sandbox / "audit.zip")
        check("audit_zip_manifest_sha_and_unicode", all(audit_result[key] == "PASS" for key in ("manifest_validation", "integrity", "path_separator_validation", "unicode_round_trip")))

    for name, (expected, paths) in FROZEN_GROUPS.items():
        check(f"frozen_hash_{name}", tree_digest(paths) == expected)
    check("provider_not_executed", tree_digest(FROZEN_GROUPS["provider_evidence"][1]) == FROZEN_GROUPS["provider_evidence"][0])
    check("new_translation_not_generated", tree_digest(FROZEN_GROUPS["generated_translation_evidence"][1]) == FROZEN_GROUPS["generated_translation_evidence"][0])

    deleted = subprocess.run(
        ["git", "ls-files", "--deleted"], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()
    check("no_tracked_deletions", not deleted)
    status = subprocess.run(
        ["git", "status", "--porcelain", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout.decode("utf-8", "replace").lower()
    check("batch4_not_started", "batch4" not in status and "batch_4" not in status)

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in checks):
        return 1
    print(f"NTPE Architecture Consolidation Batch 1 Repository Hygiene ALL PASS ({len(checks)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
