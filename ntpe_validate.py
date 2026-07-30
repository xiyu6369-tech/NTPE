# =====================================================
# NTPE 1.2 Professional
# Stage-10.7 Project Validator
# Root command: python ntpe_validate.py
# =====================================================

from __future__ import annotations

import argparse
import compileall
import importlib
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional

from tools.audit_project_layout import build_inventory

ROOT = Path(__file__).resolve().parent

REQUIRED_DIRS = [
    "core",
    "tests",
    "config",
    "docs",
    "tools",
]

REQUIRED_ENTRYPOINTS = [
    "launcher.py",
    "launcher_translate.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
]

REQUIRED_IMPORTS = [
    "core.translation_engine.translation_engine",
    "core.translation_runtime.runtime",
    "core.translation_session.session_manager",
    "core.translation_pipeline.pipeline_manager",
    "core.translation_resources.resource_manager",
    "core.translation_plugins.registry",
    "core.translation_plugins.marketplace",
]

OPTIONAL_IMPORTS = [
    "core.ai_provider.manager",
    "core.production_runtime.host",
    "core.prompt_builder.prompt_builder",
    "core.quality.semantic_qa",
]

EXCLUDE_DIR_NAMES = {
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
}

@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def iter_python_files() -> Iterable[Path]:
    for path in ROOT.rglob("*.py"):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        yield path


def clean_python_cache_artifacts() -> int:
    removed = 0
    for cache_dir in list(ROOT.rglob("__pycache__")):
        if ".git" in cache_dir.parts:
            continue
        for item in cache_dir.rglob("*"):
            if item.is_file():
                item.unlink(missing_ok=True)
                removed += 1
        try:
            cache_dir.rmdir()
            removed += 1
        except OSError:
            pass
    for pattern in ("*.pyc", "*.pyo"):
        for item in ROOT.rglob(pattern):
            if ".git" not in item.parts:
                item.unlink(missing_ok=True)
                removed += 1
    return removed


def add_root_to_path() -> None:
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def check_required_dirs() -> CheckResult:
    missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
    if missing:
        return CheckResult("Required directories", "FAIL", "Missing: " + ", ".join(missing))
    return CheckResult("Required directories", "PASS", f"{len(REQUIRED_DIRS)} directories found")


def check_entrypoints() -> CheckResult:
    missing = [f for f in REQUIRED_ENTRYPOINTS if not (ROOT / f).is_file()]
    if missing:
        return CheckResult("Legacy entrypoints", "FAIL", "Missing: " + ", ".join(missing))
    return CheckResult("Legacy entrypoints", "PASS", f"{len(REQUIRED_ENTRYPOINTS)} entrypoints found")


def check_required_imports() -> CheckResult:
    add_root_to_path()
    failed: List[str] = []
    for module in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - diagnostic output is intended
            failed.append(f"{module}: {exc.__class__.__name__}: {exc}")
    if failed:
        return CheckResult("Core imports", "FAIL", " | ".join(failed))
    return CheckResult("Core imports", "PASS", f"{len(REQUIRED_IMPORTS)} required imports OK")


def check_optional_imports() -> CheckResult:
    add_root_to_path()
    failed: List[str] = []
    passed = 0
    for module in OPTIONAL_IMPORTS:
        try:
            importlib.import_module(module)
            passed += 1
        except Exception as exc:
            failed.append(f"{module}: {exc.__class__.__name__}: {exc}")
    if failed:
        return CheckResult("Optional imports", "WARN", f"{passed} OK; warnings: " + " | ".join(failed))
    return CheckResult("Optional imports", "PASS", f"{passed} optional imports OK")


def check_py_compile() -> CheckResult:
    failed: List[str] = []
    total = 0
    with tempfile.TemporaryDirectory(prefix="ntpe_py_compile_") as cache_dir:
        cache_root = Path(cache_dir)
        for file in iter_python_files():
            total += 1
            try:
                cfile = cache_root / rel(file).replace("\\", "__").replace("/", "__")
                cfile = cfile.with_suffix(cfile.suffix + ".pyc")
                py_compile.compile(str(file), cfile=str(cfile), doraise=True)
            except py_compile.PyCompileError as exc:
                failed.append(f"{rel(file)}: {exc.msg}")
            except OSError as exc:
                failed.append(f"{rel(file)}: {exc.__class__.__name__}: {exc}")
    clean_python_cache_artifacts()
    if failed:
        return CheckResult("Python compile", "FAIL", f"{len(failed)} failed / {total} files: " + " | ".join(failed[:10]))
    return CheckResult("Python compile", "PASS", f"{total} Python files compile")


def check_cache_files() -> CheckResult:
    cache_items = []
    for pattern in ("__pycache__", "*.pyc", "*.pyo"):
        cache_items.extend(ROOT.rglob(pattern))
    cache_items = [p for p in cache_items if ".git" not in p.parts]
    if cache_items:
        return CheckResult("Python cache", "WARN", f"{len(cache_items)} cache items found; safe to clean")
    return CheckResult("Python cache", "PASS", "No Python cache artifacts found")


def check_test_inventory() -> CheckResult:
    tests_dir = ROOT / "tests"
    verification_dir = ROOT / "verification"
    if not tests_dir.exists():
        return CheckResult("Test inventory", "FAIL", "tests/ not found")
    test_files = set(tests_dir.rglob("test_*.py")) | set(tests_dir.rglob("*_test.py"))
    verification_files = set(verification_dir.rglob("test_*.py")) | set(verification_dir.rglob("*_test.py"))
    if not test_files:
        return CheckResult("Test inventory", "WARN", "No pytest-style test files found")
    return CheckResult(
        "Test inventory",
        "PASS",
        f"{len(test_files)} pytest tests; {len(verification_files)} relocated verification wrappers",
    )


def check_project_structure() -> CheckResult:
    inventory = build_inventory()
    unexpected = inventory["unexpected_root_files"] + inventory["unexpected_root_directories"]
    if unexpected:
        return CheckResult("Root Python layout", "FAIL", "Unexpected root items: " + ", ".join(unexpected[:20]))
    return CheckResult(
        "Root Python layout",
        "PASS",
        f'{inventory["root_python_files"]} root Python files; layout policy satisfied',
    )


def run_pytest() -> CheckResult:
    command = [sys.executable, "-m", "pytest", "-q"]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
        )
    except FileNotFoundError:
        return CheckResult("Pytest", "WARN", "pytest is not installed")
    except subprocess.TimeoutExpired:
        return CheckResult("Pytest", "FAIL", "pytest timed out after 300 seconds")

    output = completed.stdout.strip().splitlines()
    summary = output[-1] if output else "no output"
    if completed.returncode == 0:
        return CheckResult("Pytest", "PASS", summary)
    return CheckResult("Pytest", "FAIL", summary)


def run_validation(include_pytest: bool = False) -> List[CheckResult]:
    results = [
        check_required_dirs(),
        check_entrypoints(),
        check_required_imports(),
        check_optional_imports(),
        check_py_compile(),
        check_cache_files(),
        check_test_inventory(),
        check_project_structure(),
    ]
    if include_pytest:
        results.append(run_pytest())
    return results


def print_report(results: List[CheckResult], elapsed: float) -> None:
    width = max(len(r.name) for r in results) + 2
    print("====================================")
    print("NTPE Project Validation Report")
    print("====================================")
    print(f"Root: {ROOT}")
    print(f"Elapsed: {elapsed:.2f}s")
    print("------------------------------------")
    for result in results:
        print(f"{result.name:<{width}} {result.status:<5} {result.detail}")
    print("------------------------------------")
    failed = [r for r in results if r.status == "FAIL"]
    warnings = [r for r in results if r.status == "WARN"]
    if failed:
        print(f"FAILED: {len(failed)} failure(s), {len(warnings)} warning(s)")
    elif warnings:
        print(f"PASS WITH WARNINGS: {len(warnings)} warning(s)")
    else:
        print("ALL PASS")


def write_json_report(results: List[CheckResult], path: Path, elapsed: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "root": str(ROOT),
        "elapsed_seconds": elapsed,
        "summary": {
            "pass": sum(1 for r in results if r.status == "PASS"),
            "warn": sum(1 for r in results if r.status == "WARN"),
            "fail": sum(1 for r in results if r.status == "FAIL"),
        },
        "results": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="NTPE project health validator")
    parser.add_argument("--pytest", action="store_true", help="also run pytest -q")
    parser.add_argument("--json", dest="json_path", default="", help="write JSON report to path")
    args = parser.parse_args(argv)

    start = time.perf_counter()
    results = run_validation(include_pytest=args.pytest)
    elapsed = time.perf_counter() - start
    print_report(results, elapsed)

    if args.json_path:
        write_json_report(results, ROOT / args.json_path, elapsed)
        print(f"JSON report written: {args.json_path}")

    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
