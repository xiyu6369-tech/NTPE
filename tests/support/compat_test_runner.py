"""Minimal runner for retained Root compatibility test commands."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import runpy


ROOT = Path(__file__).resolve().parents[2]


def run_test(relative_path: str) -> None:
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.name.endswith("_test.py"):
        raise ValueError(f"unsafe compatibility test path: {relative_path}")
    target = ROOT.joinpath(*relative.parts).resolve(strict=True)
    target.relative_to(ROOT)
    runpy.run_path(str(target), run_name="__main__")
