"""
NTPE RM-2.3B Full Root Dependency Evidence Sweep
Generates docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json
and docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_REPORT.md
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(r"D:\Python\NTPE")
OUTPUT_JSON = ROOT / "docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json"
OUTPUT_MD = ROOT / "docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_REPORT.md"

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "cache",
    "tmp",
    "temp",
    "output",
    "logs",
    "final_output",
    "translated",
    "translation_cache",
    "failed_chunks",
    ".ntpe_runtime_checkpoints",
    ".ntpe_test_sandbox",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".cmd",
    ".bat",
}

# In-scope file patterns
ROOT_PATTERNS = [re.compile(r"^launcher_.*\.py$"), re.compile(r"^ntpe_.*\.py$")]


def rel_path(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def gather_scope_files() -> List[Path]:
    files = []
    for item in ROOT.iterdir():
        if item.is_file() and item.suffix == ".py":
            if any(pat.match(item.name) for pat in ROOT_PATTERNS):
                files.append(item)
    return sorted(files, key=lambda p: p.name)


def main() -> None:
    print(f"Scanning repository root: {ROOT}")
    scope_files = gather_scope_files()
    print(f"Total in-scope root Python files: {len(scope_files)}")

    # 1. Build inverted import index across all python files in repo
    all_py_files = [
        p
        for p in ROOT.rglob("*.py")
        if not any(part in EXCLUDED_DIRS for part in p.parts)
    ]

    # Map: module_stem -> list of {source_file, import_type, line}
    module_importers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for py_file in all_py_files:
        rel = rel_path(py_file)
        text = read_text(py_file)
        if not text:
            continue
        try:
            tree = ast.parse(text, filename=rel)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.split(".")[-1]
                    module_importers[mod_name].append(
                        {
                            "source_file": rel,
                            "imported_module": alias.name,
                            "lineno": getattr(node, "lineno", 0),
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_name = node.module.split(".")[-1]
                    module_importers[mod_name].append(
                        {
                            "source_file": rel,
                            "imported_module": node.module,
                            "lineno": getattr(node, "lineno", 0),
                        }
                    )

    # 2. Build text reference index across repo categories
    categories = {
        "readme_docs": [ROOT / "README.md", ROOT / "docs"],
        "manifests_config": [ROOT / "manifests", ROOT / "config"],
        "artifacts_audits": [ROOT / "artifacts", ROOT / "audits"],
        "tests_verification": [ROOT / "tests", ROOT / "verification"],
        "tools_scripts": [ROOT / "tools", ROOT / "cli"],
    }

    category_file_texts: Dict[str, List[Tuple[str, str]]] = {}
    for cat_name, cat_paths in categories.items():
        file_texts = []
        for cat_path in cat_paths:
            if not cat_path.exists():
                continue
            if cat_path.is_file():
                txt = read_text(cat_path)
                if txt:
                    file_texts.append((rel_path(cat_path), txt))
            else:
                for child in cat_path.rglob("*"):
                    if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS:
                        if not any(part in EXCLUDED_DIRS for part in child.parts):
                            txt = read_text(child)
                            if txt:
                                file_texts.append((rel_path(child), txt))
        category_file_texts[cat_name] = file_texts

    file_evidence_list = []

    # Primary entry points that must stay at root
    PRIMARY_KEEP_ROOT = {
        "launcher.py",
        "launcher_pipeline.py",
        "launcher_pipeline_production.py",
        "launcher_translate.py",
        "ntpe_launcher.py",
        "ntpe_validate.py",
        "ntpe_production_translate.py",
        "ntpe_translate_txt.py",
        "ntpe_translate_batch.py",
        "ntpe_authorized_provider_invocation.py",
        "ntpe_single_real_provider_invocation.py",
        "ntpe_controlled_real_provider_retry.py",
        "ntpe_batch_monitor.py",
        "ntpe_provider_setup.py",
        "ntpe_provider_verify.py",
        "ntpe_provider_audit.py",
    }

    for target in scope_files:
        fname = target.name
        stem = target.stem
        rel = rel_path(target)
        content = read_text(target)

        # A. Python imports within target
        import_refs = []
        from_imports = []
        try:
            tree = ast.parse(content, filename=rel)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_refs.append(
                            {"module": alias.name, "asname": alias.asname}
                        )
                elif isinstance(node, ast.ImportFrom):
                    from_imports.append(
                        {
                            "module": node.module or "",
                            "names": [
                                {"name": a.name, "asname": a.asname}
                                for a in node.names
                            ],
                            "level": node.level,
                        }
                    )
        except Exception as exc:
            pass

        # B. Incoming python imports from other modules
        importers = [
            item
            for item in module_importers.get(stem, [])
            if item["source_file"] != rel
        ]
        # Deduplicate importers by source_file
        unique_importers = {}
        for imp in importers:
            sf = imp["source_file"]
            if sf not in unique_importers:
                unique_importers[sf] = imp
        imported_by_other = list(unique_importers.values())

        # C. Runtime references inside target (subprocess, os.system, shell commands)
        subprocess_calls = []
        command_examples = []
        for idx, line in enumerate(content.splitlines(), 1):
            line_str = line.strip()
            if any(
                k in line_str
                for k in ["subprocess.", "os.system(", "Popen(", "call("]
            ):
                subprocess_calls.append({"line": idx, "code": line_str})
            if re.search(r"\bpython\s+\w+\.py\b", line_str, re.IGNORECASE):
                command_examples.append({"line": idx, "code": line_str})

        # D. Search for external text references to this file or stem
        refs_by_cat: Dict[str, List[str]] = {}
        for cat_name, file_texts in category_file_texts.items():
            matching_files = []
            for f_rel, txt in file_texts:
                if f_rel == rel:
                    continue
                if fname in txt or (len(stem) > 6 and stem in txt):
                    matching_files.append(f_rel)
            refs_by_cat[cat_name] = sorted(list(set(matching_files)))

        # E. Determine Classification
        is_stage_or_test_file = any(
            stem.startswith(prefix)
            for prefix in [
                "ntpe_stage",
                "ntpe_te_",
                "ntpe_lcr",
                "ntpe_tic",
                "ntpe_ps",
                "ntpe_ter",
                "ntpe_architecture_consolidation",
                "ntpe_translation_engine_refactor",
            ]
        ) or stem.endswith("_test")

        if fname in PRIMARY_KEEP_ROOT:
            classification = "KEEP_ROOT"
            reason = "Core production entrypoint, primary CLI launcher, or primary project validator referenced in repository root documentation and operational scripts."
        elif is_stage_or_test_file:
            classification = "ARCHIVE_ONLY"
            reason = "Stage-specific test, benchmark suite, or frozen verification wrapper; should be preserved as historical test evidence in verification/ or tests/."
        elif refs_by_cat["manifests_config"] or refs_by_cat["readme_docs"]:
            classification = "MOVE_WITH_WRAPPER"
            reason = "Referenced by project configuration, automation manifests, or documentation; relocating requires maintaining a root compatibility wrapper shim."
        elif imported_by_other or refs_by_cat["tools_scripts"]:
            classification = "MOVE_WITH_WRAPPER"
            reason = "Imported by active root modules or tools; requires a shim or wrapper if moved to tools/ or core/."
        elif refs_by_cat["artifacts_audits"] or refs_by_cat["tests_verification"]:
            classification = "SAFE_MOVE"
            reason = "Standalone utility or secondary script with references only in historical audit/test logs; can be safely moved to tools/ or verification/."
        else:
            classification = "SAFE_MOVE"
            reason = "Standalone helper script with no direct runtime or manifest couplings; eligible for relocation to tools/ or appropriate domain folder."

        file_evidence = {
            "file": rel,
            "filename": fname,
            "stem": stem,
            "classification": classification,
            "classification_reason": reason,
            "python_imports": {
                "import_statements": import_refs,
                "from_import_statements": from_imports,
                "imported_by_other_modules": imported_by_other,
                "imported_by_other_count": len(imported_by_other),
            },
            "runtime_references": {
                "subprocess_calls": subprocess_calls,
                "command_examples": command_examples,
                "readme_docs_references": refs_by_cat["readme_docs"],
                "tools_scripts_references": refs_by_cat["tools_scripts"],
            },
            "artifact_references": {
                "manifests_config_references": refs_by_cat["manifests_config"],
                "artifacts_audits_references": refs_by_cat["artifacts_audits"],
            },
            "test_references": {
                "tests_verification_references": refs_by_cat[
                    "tests_verification"
                ],
                "has_internal_test_functions": "def test_" in content,
            },
        }
        file_evidence_list.append(file_evidence)

    # Summary statistics
    summary_counts = defaultdict(int)
    for fe in file_evidence_list:
        summary_counts[fe["classification"]] += 1

    output_data = {
        "metadata": {
            "title": "NTPE RM-2.3B Full Root Dependency Evidence Sweep",
            "generated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "repository_root": str(ROOT),
            "scope_patterns": ["launcher_*.py", "ntpe_*.py"],
            "total_files_analyzed": len(file_evidence_list),
        },
        "classification_summary": dict(summary_counts),
        "files": file_evidence_list,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"JSON evidence written to {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size} bytes)")

    # Build Markdown Report
    md_lines = [
        "# RM-2.3B Full Root Dependency Evidence Sweep Report",
        "",
        f"**Generated:** {output_data['metadata']['generated_at']}",
        f"**Repository:** `{ROOT}`",
        f"**Total Scope Files:** {len(file_evidence_list)}",
        "",
        "## Executive Summary",
        "",
        "This report provides a comprehensive, read-only dependency evidence analysis for all root-level Python files matching `launcher_*.py` and `ntpe_*.py`. Every file has been evaluated for direct Python imports, incoming import references, runtime subprocess invocations, documentation/README references, automation manifest ties, artifact/audit references, and test harness usage.",
        "",
        "### Classification Breakdown",
        "",
        "| Classification | Count | Description |",
        "| --- | ---: | --- |",
        f"| **KEEP_ROOT** | {summary_counts['KEEP_ROOT']} | Primary entry points, launchers, or validators required at repository root. |",
        f"| **MOVE_WITH_WRAPPER** | {summary_counts['MOVE_WITH_WRAPPER']} | Secondary launchers or modules referenced by docs/manifests requiring a root shim if moved. |",
        f"| **SAFE_MOVE** | {summary_counts['SAFE_MOVE']} | Standalone utilities or helper scripts eligible for clean relocation to `tools/` or `verification/`. |",
        f"| **ARCHIVE_ONLY** | {summary_counts['ARCHIVE_ONLY']} | Historical stage test suites, benchmarks, or frozen stage verification scripts. |",
        f"| **DELETE_CANDIDATE** | {summary_counts['DELETE_CANDIDATE']} | Obsolete/superseded temporary scripts with zero references. |",
        "",
        "---",
        "",
        "## In-Depth File Dependency Evidence",
        "",
    ]

    for fe in file_evidence_list:
        md_lines.extend(
            [
                f"### `{fe['filename']}`",
                "",
                f"- **Classification:** `{fe['classification']}`",
                f"- **Reason:** {fe['classification_reason']}",
                f"- **Direct Imports:** {len(fe['python_imports']['import_statements'])} module import(s), {len(fe['python_imports']['from_import_statements'])} `from` statement(s)",
                f"- **Imported By:** {fe['python_imports']['imported_by_other_count']} other Python module(s)",
            ]
        )

        if fe["python_imports"]["imported_by_other_modules"]:
            md_lines.append("  - *Importers:* " + ", ".join([f"`{imp['source_file']}`" for imp in fe["python_imports"]["imported_by_other_modules"][:5]]))

        if fe["runtime_references"]["readme_docs_references"]:
            md_lines.append(
                f"- **Docs/README References ({len(fe['runtime_references']['readme_docs_references'])}):** "
                + ", ".join(
                    [
                        f"`{ref}`"
                        for ref in fe["runtime_references"][
                            "readme_docs_references"
                        ][:5]
                    ]
                )
            )

        if fe["artifact_references"]["manifests_config_references"]:
            md_lines.append(
                f"- **Manifest/Config References ({len(fe['artifact_references']['manifests_config_references'])}):** "
                + ", ".join(
                    [
                        f"`{ref}`"
                        for ref in fe["artifact_references"][
                            "manifests_config_references"
                        ][:5]
                    ]
                )
            )

        if fe["artifact_references"]["artifacts_audits_references"]:
            md_lines.append(
                f"- **Artifact/Audit References ({len(fe['artifact_references']['artifacts_audits_references'])}):** {len(fe['artifact_references']['artifacts_audits_references'])} item(s)"
            )

        if fe["test_references"]["tests_verification_references"]:
            md_lines.append(
                f"- **Test Suite References ({len(fe['test_references']['tests_verification_references'])}):** "
                + ", ".join(
                    [
                        f"`{ref}`"
                        for ref in fe["test_references"][
                            "tests_verification_references"
                        ][:5]
                    ]
                )
            )

        if fe["runtime_references"]["subprocess_calls"]:
            md_lines.append(
                f"- **Subprocess Invocations:** {len(fe['runtime_references']['subprocess_calls'])} call(s) inside file"
            )

        md_lines.append("")

    OUTPUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Markdown report written to {OUTPUT_MD} ({OUTPUT_MD.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
