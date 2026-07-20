from __future__ import annotations

import os
import sys
from pathlib import Path


_PROJECT_ROOT: Path | None = None


def activate_verification(verification_root: Path) -> Path:
    global _PROJECT_ROOT
    _PROJECT_ROOT = verification_root.resolve().parent
    project_root_text = str(_PROJECT_ROOT)
    if project_root_text not in sys.path:
        sys.path.insert(0, project_root_text)
    os.chdir(_PROJECT_ROOT)
    return _PROJECT_ROOT


def verification_project_root() -> Path:
    if _PROJECT_ROOT is None:
        raise RuntimeError("verification bootstrap has not been activated")
    return _PROJECT_ROOT
