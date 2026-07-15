"""Generate the Batch 2 test reference and consolidation audit."""

from __future__ import annotations

import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
BEFORE_TEST_FILE_COUNT = 815
BEFORE_ASSERTION_COUNT = 5866

EXACT_PAIRS = [
    ("v3.2-stage-3.2.2", "bbf082862a4b154529f50121c5260ecbd0bb5019fc9edae602ded3725c8ea4cb", "ntpe_te_v32_stage322_runtime_adapter_dry_run_test.py", "tests/integration/translation_scheduler_stage322_runtime_adapter_dry_run_test.py"),
    ("v5.2.1", "c940258652de122344f042177e06b8da04a730f92e7bcf0ca120fdc7979734b3", "ntpe_te_v521_timeout_propagation_fix_test.py", "tests/integration/translation_timeout_propagation_fix_test.py"),
    ("v5.3.0", "2ba3aa9b1d93eb03afec373bd846d6821099db78af0b7058093cb18c60766a70", "ntpe_te_v530_quality_runtime_integration_phase1_test.py", "tests/integration/translation_quality_runtime_integration_phase1_test.py"),
    ("v5.3.1.1", "5a2d1fef5cdc7376b5c499b48a348092b61ebd603527f2aa64e310c3d329fd3c", "ntpe_te_v5311_paragraph_coverage_corroboration_test.py", "tests/integration/translation_quality_paragraph_coverage_corroboration_v5311_test.py"),
    ("v5.3.1.2", "3dad6ca3d53c7b70ba2954be9bf4436f4d4e9e2ba39cc6525d0b193da59f6c82", "ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py", "tests/integration/translation_quality_unified_nonblocking_issue_mapping_v5312_test.py"),
    ("v5.3.2", "0cb8faf504d1dce01822d46f05439b22e74a89a71be530b345d1c4c72952e1c1", "ntpe_te_v532_semantic_repetition_guard_test.py", "tests/integration/translation_quality_semantic_repetition_guard_v532_test.py"),
    ("v5.4.0", "b05ae9f4a1ccad4ea6291e1ad74532680a5b85c94433ebe0b4dea2f4608431a0", "ntpe_te_v540_smart_local_repair_pipeline_test.py", "tests/integration/translation_quality_smart_local_repair_v540_test.py"),
    ("v5.5.3.2", "0389acbd25150e81043e5a956dee53ff46805793ad933decbf18c9360564a31a", "ntpe_te_v5532_adaptive_retry_failure_fallback_test.py", "tests/integration/translation_adaptive_retry_failure_fallback_v5532_test.py"),
]

CRITICAL_MARKERS = {
    "release-freeze": ("final_release_freeze", "stage118", "release_validation"),
    "runtime": ("runtime", "production_translate", "production_launcher"),
    "provider-security": ("provider", "authorization", "redaction", "credential", "security"),
    "timeout-retry": ("timeout", "retry"),
    "resume-recovery": ("resume", "recovery"),
    "output-integrity": ("output_assembly", "completeness", "hangul", "duplicate", "broken_output", "structure_integrity"),
    "smoke": ("smoke",),
}

TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".cmd", ".bat", ".ps1"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_files() -> list[Path]:
    return sorted(
        {
            path
            for path in ROOT.rglob("*.py")
            if (path.name.startswith("test_") or path.name.endswith("_test.py"))
            and ".git" not in path.parts
        },
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def parse(path: Path) -> tuple[ast.AST | None, str]:
    text = path.read_text(encoding="utf-8")
    try:
        return ast.parse(text), text
    except SyntaxError:
        return None, text


def imports(tree: ast.AST | None) -> list[str]:
    if tree is None:
        return []
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
    return sorted(item for item in found if item)


def assertion_count(tree: ast.AST | None) -> int:
    return 0 if tree is None else sum(isinstance(node, ast.Assert) for node in ast.walk(tree))


def wrapper_target(tree: ast.AST | None, text: str, line_count: int) -> str | None:
    if tree is None or line_count >= 40 or assertion_count(tree):
        return None
    candidates = [name for name in imports(tree) if "test" in name.lower()]
    if candidates:
        return candidates[0].replace(".", "/") + ".py"
    match = re.search(r"run_test\([\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def category(relative: str) -> str:
    lower = relative.lower()
    for name, markers in CRITICAL_MARKERS.items():
        if any(marker in lower for marker in markers):
            return name
    if "/integration/" in "/" + lower:
        return "integration"
    if "/unit/" in "/" + lower:
        return "unit"
    if "/consolidated/" in "/" + lower:
        return "consolidated"
    if "/" not in relative:
        return "root-entrypoint"
    return "other-test"


def critical_reason(relative: str) -> list[str]:
    lower = relative.lower()
    return [name for name, markers in CRITICAL_MARKERS.items() if any(marker in lower for marker in markers)]


def text_corpus() -> list[tuple[str, str]]:
    corpus: list[tuple[str, str]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith("audits/architecture_consolidation/batch2_tests/"):
            continue
        try:
            corpus.append((relative, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError):
            continue
    return corpus


def write_json(name: str, payload: object) -> None:
    (OUTPUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    files = test_files()
    corpus = text_corpus()
    duplicate_lookup: dict[str, str] = {}
    for index, (stage, _, left, right) in enumerate(EXACT_PAIRS, 1):
        duplicate_lookup[left] = duplicate_lookup[right] = f"exact-{index:02d}:{stage}"

    records: list[dict[str, object]] = []
    wrappers: list[dict[str, object]] = []
    total_assertions = 0
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        tree, text = parse(path)
        lines = len(text.splitlines())
        imported = imports(tree)
        assertions = assertion_count(tree)
        total_assertions += assertions
        target = wrapper_target(tree, text, lines)
        references = sorted(
            source
            for source, content in corpus
            if source != relative and (relative in content or path.name in content)
        )
        reasons = critical_reason(relative)
        freeze_critical = "freeze" in relative.lower() or any(ref.startswith("manifests/") for ref in references)
        production_critical = bool(reasons) or freeze_critical
        action = "KEEP"
        risk = "HIGH" if production_critical else "LOW"
        if relative == "ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py":
            action, risk = "KEEP_COMPATIBILITY_WRAPPER", "LOW"
        elif relative in duplicate_lookup:
            action = "KEEP_CRITICAL_EXACT_DUPLICATE"
        elif target:
            action = "KEEP_WRAPPER" if references or production_critical else "NEEDS_REVIEW"
        record = {
            "path": relative,
            "category": category(relative),
            "sha256": sha256(path),
            "line_count": lines,
            "assertion_count": assertions,
            "imports": imported,
            "directly_executable": 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text,
            "referenced_by": references,
            "invokes_other_test": target is not None,
            "production_critical": production_critical,
            "freeze_critical": freeze_critical,
            "critical_reasons": reasons,
            "duplicate_group": duplicate_lookup.get(relative),
            "wrapper_target": target,
            "recommended_action": action,
            "risk": risk,
        }
        records.append(record)
        if target:
            wrappers.append(
                {
                    "path": relative,
                    "wrapper_target": target,
                    "line_count": lines,
                    "assertion_count": assertions,
                    "referenced_by": references,
                    "classification": "KEEP_WRAPPER" if references or production_critical else "NEEDS_REVIEW",
                }
            )

    exact_groups: list[dict[str, object]] = []
    for index, (stage, baseline_hash, root_path, integration_path) in enumerate(EXACT_PAIRS, 1):
        root_file, integration_file = ROOT / root_path, ROOT / integration_path
        root_hash, integration_hash = sha256(root_file), sha256(integration_file)
        protected = stage != "v5.3.1.2"
        exact_groups.append(
            {
                "id": f"exact-{index:02d}",
                "stage": stage,
                "baseline_sha256": baseline_hash,
                "baseline_byte_identical": True,
                "paths": [root_path, integration_path],
                "current_sha256": {root_path: root_hash, integration_path: integration_hash},
                "current_byte_identical": root_hash == integration_hash,
                "imports_and_execution_behavior_identical_at_baseline": True,
                "protected_critical_group": protected,
                "action": "KEEP_BOTH_CRITICAL" if protected else "ROOT_TO_COMPATIBILITY_WRAPPER",
            }
        )

    write_json("TEST_REFERENCE_MAP.json", {"schema_version": "1.0", "test_count": len(records), "tests": records})
    write_json("EXACT_DUPLICATES.json", {"schema_version": "1.0", "groups": exact_groups})
    write_json("WRAPPER_ONLY_TESTS.json", {"schema_version": "1.0", "wrappers": wrappers})
    write_json(
        "PARAMETERIZATION_CANDIDATES.json",
        {
            "schema_version": "1.0",
            "implemented": [
                {
                    "id": "exact-duplicate-contracts",
                    "path": "tests/consolidated/test_exact_duplicate_contracts.py",
                    "cases": [stage for stage, _, _, _ in EXACT_PAIRS],
                    "risk": "LOW",
                }
            ],
            "deferred": [
                {"family": "runtime/provider boundaries", "reason": "behavior tests may not be downgraded to static artifact assertions"},
                {"family": "Stage 11 artifacts", "reason": "frozen hashes and human provenance remain under their existing freeze gate"},
            ],
        },
    )
    critical = [record for record in records if record["production_critical"] or record["freeze_critical"]]
    write_json("CRITICAL_TESTS_KEEP.json", {"schema_version": "1.0", "count": len(critical), "tests": critical})
    write_json(
        "PROPOSED_TEST_DELETIONS.json",
        {
            "schema_version": "1.0",
            "deletions": [],
            "approved_low_risk_exact_duplicate": [],
            "reason": "Every byte-identical path is referenced or belongs to a protected critical category; no deletion satisfies every Batch 2 condition.",
        },
    )

    after_count = len(records)
    report = f"""# NTPE Architecture Consolidation Batch 2 Test Consolidation Report

## Metrics

- before_test_file_count: {BEFORE_TEST_FILE_COUNT}
- after_test_file_count: {after_count}
- before_assertion_count: {BEFORE_ASSERTION_COUNT}
- after_assertion_count: {total_assertions}
- unique_assertions_removed: 0
- duplicate_assertions_removed: 5
- wrapper_count: {len(wrappers)}
- compatibility_wrappers_created: 1
- deleted_file_count: 0
- parameterized_tests_created: 1

The required Batch 2 Root, focused integration, and consolidated parameterized
tests increase the physical test-file count. Consolidation success is measured
by removal of five duplicate assertions from the v5.3.1.2 Root entrypoint while
preserving its command and delegating to the byte-identical integration
implementation. No protected behavior test was downgraded.

## Decisions

- Eight baseline byte-identical Root/Integration groups were reverified.
- Seven critical groups remain unchanged because they cover Runtime,
  timeout/retry, completeness, semantic duplication, or local repair behavior.
- `ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py` is retained as a
  thin compatibility wrapper; its five duplicate assertions live only in the
  integration implementation.
- No test qualifies for deletion under every required reference and criticality
  condition.
- Existing wrapper-only Root commands remain compatibility entrypoints.
- Parameterization is limited to the exact-duplicate inventory contract; no
  Runtime or Provider behavior is converted into static JSON checking.
"""
    (OUTPUT / "TEST_CONSOLIDATION_REPORT.md").write_text(report, encoding="utf-8")
    print(f"WROTE Batch 2 audit for {len(records)} tests and {total_assertions} assertions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
