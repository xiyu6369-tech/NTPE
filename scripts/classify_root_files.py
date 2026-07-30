#!/usr/bin/env python3
"""
RM-4.2B: Root .py File Classification Scanner
================================================
Scans all root .py files and classifies them as:
  KEEP_ROOT, MOVE_WITH_WRAPPER, SAFE_MOVE, ARCHIVE_ONLY.

NO FILES ARE MOVED, DELETED, OR RENAMED.
NO PROVIDER OR NETWORK REQUESTS ARE MADE.
"""

import os
import json
import ast
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(ROOT))

PRODUCTION_ENTRIES = {
    "ntpe_validate.py",
    "ntpe_production_translate.py",
    "ntpe_batch_monitor.py",
    "ntpe_launcher.py",
}


def get_imports(filepath: Path):
    """Extract import module names from a .py file using AST."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
        return imports
    except SyntaxError:
        return ["<SYNTAX_ERROR>"]


def main():
    root_py = sorted([f for f in ROOT.glob("*.py") if f.is_file()],
                      key=lambda x: x.name)
    results = {}
    categories = defaultdict(list)

    for fpath in root_py:
        fname = fpath.name
        imports = get_imports(fpath)
        top_imports = set(imports)
        root_imports = set()

        for imp in top_imports:
            candidate = ROOT / (imp + ".py")
            if candidate.exists() and candidate.is_file():
                root_imports.add(candidate.name)

        is_production_entry = fname in PRODUCTION_ENTRIES
        is_launcher = fname.startswith("launcher_") or fname == "launcher.py"
        is_test = fname.endswith("_test.py")
        has_provider = "provider" in fname.lower() and not is_test

        classification = "UNKNOWN"
        rationale = []

        # Classification rules
        if is_production_entry:
            classification = "KEEP_ROOT"
            rationale.append("Listed in production entry policy; core governance anchor")
        elif fname == "launcher_pipeline.py" or fname == "launcher_pipeline_production.py":
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Pipeline launcher; needs RM-3.2 wrapper")
        elif fname == "launcher_translate.py":
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Imports ntpe_production_translate — needs wrapper")
        elif fname in ("ntpe_translate_batch.py", "ntpe_translate_txt.py"):
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Translation helper — potential production reference")
        elif fname == "ntpe_literary_regression.py":
            classification = "ARCHIVE_ONLY"
            rationale.append("Legacy literary regression tool — no active pipeline ref")
        elif fname == "ntpe_literary_evaluation.py":
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Literary evaluation tool — could move to tools/")
        elif fname == "ntpe_plugin_marketplace.py":
            classification = "ARCHIVE_ONLY"
            rationale.append("Plugin marketplace prototype — no active consumer")
        elif fname == "ntpe_long_run_recovery.py":
            classification = "ARCHIVE_ONLY"
            rationale.append("Legacy long-run recovery — not in active pipeline")
        elif fname == "ntpe_lcr_batch107_real_provider_validation.py":
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Contains real provider validation — needs authorization hook")
        elif has_provider and not is_test:
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Provider tool — may need controlled authorization + wrapper")
        elif is_launcher and not is_production_entry:
            classification = "MOVE_WITH_WRAPPER"
            rationale.append("Launcher tool — may need compatibility wrapper")
        elif is_test:
            classification = "SAFE_MOVE"
            rationale.append("Test file — no runtime/production dependency")
        else:
            classification = "SAFE_MOVE"
            rationale.append("No identified production or manifest dependency")

        record = {
            "file": fname,
            "category": classification,
            "imports": sorted(list(top_imports)),
            "root_imports": sorted(list(root_imports)),
            "rationale": rationale,
        }
        results[fname] = record
        categories[classification].append(fname)

    # Summary
    summary = {
        "KEEP_ROOT": len(categories["KEEP_ROOT"]),
        "MOVE_WITH_WRAPPER": len(categories["MOVE_WITH_WRAPPER"]),
        "SAFE_MOVE": len(categories["SAFE_MOVE"]),
        "ARCHIVE_ONLY": len(categories["ARCHIVE_ONLY"]),
        "UNKNOWN": len(categories["UNKNOWN"]),
        "total": len(results),
    }

    print("=" * 50)
    print("RM-4.2B Classification Summary")
    print("=" * 50)
    for cat, count in sorted(summary.items()):
        print(f"  {cat}: {count}")

    print("\n\n--- KEEP_ROOT ---")
    for name in sorted(categories["KEEP_ROOT"]):
        print(f"  {name}")

    print("\n--- MOVE_WITH_WRAPPER ---")
    for name in sorted(categories["MOVE_WITH_WRAPPER"]):
        rec = results[name]
        print(f"  {name}")
        print(f"    -> {rec['rationale']}")

    print("\n--- SAFE_MOVE ---")
    for name in sorted(categories["SAFE_MOVE"]):
        print(f"  {name}")

    print("\n--- ARCHIVE_ONLY ---")
    for name in sorted(categories["ARCHIVE_ONLY"]):
        rec = results[name]
        print(f"  {name} -> {rec['rationale']}")

    # Write JSON
    output = {
        "summary": summary,
        "files": results,
        "categories": {k: sorted(v) for k, v in categories.items()},
    }
    out_path = ROOT / "docs" / "governance" / "migration" / "RM_4_2B_CLASSIFICATION_DATA.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON written to: {out_path}")


if __name__ == "__main__":
    main()