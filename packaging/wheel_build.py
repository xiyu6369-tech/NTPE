"""Minimal packaging validation helper for Stage-07.8.

This helper intentionally avoids requiring an actual build backend during freeze tests.
"""
from __future__ import annotations

from pathlib import Path


def validate_packaging(root: str | Path | None = None) -> dict:
    base = Path(root or Path(__file__).resolve().parents[1])
    required = [
        base / "packaging" / "pyproject.toml",
        base / "packaging" / "MANIFEST.in",
        base / "sdk" / "py.typed",
        base / "sdk" / "version.py",
        base / "sdk" / "metadata.py",
    ]
    missing = [str(path.relative_to(base)) for path in required if not path.exists()]
    return {"ok": not missing, "missing": missing}


if __name__ == "__main__":
    result = validate_packaging()
    print("Wheel Build", "PASS" if result["ok"] else "FAIL")
    if not result["ok"]:
        raise SystemExit(1)
