#!/usr/bin/env python3
"""Quick check: what do production entries import from root?"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ENTRIES = [
    "ntpe_validate.py",
    "ntpe_production_translate.py",
    "ntpe_batch_monitor.py",
    "ntpe_launcher.py",
]

for entry in ENTRIES:
    fpath = ROOT / entry
    if not fpath.exists():
        print(f"{entry} NOT FOUND")
        continue
    src = fpath.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        root_imports = []
        for imp in imports:
            candidate = ROOT / (imp + ".py")
            if candidate.exists():
                root_imports.append(imp)
        print(f"\n--- {entry} ---")
        print(f"  All imports: {sorted(imports)}")
        print(f"  Root .py imports: {root_imports}")
    except SyntaxError as e:
        print(f"{entry}: SyntaxError {e}")