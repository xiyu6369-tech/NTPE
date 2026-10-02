"""Result-open abstraction (S9-05 §15).

Platform file-opening is centralized here so UI tests can inject a fake opener
and never launch a real OS application.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Protocol


class ResultOpener(Protocol):
    def open_path(self, path: str | Path) -> bool:
        """Open the output artifact with the OS default application."""
        ...

    def reveal_folder(self, path: str | Path) -> bool:
        """Reveal the artifact (or its folder) in the OS file manager."""
        ...


class SystemResultOpener:
    """Real OS-backed opener. Returns False on any failure; never raises."""

    def open_path(self, path: str | Path) -> bool:
        target = Path(path)
        if not target.is_file():
            return False
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(target))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return True
        except Exception:
            return False

    def reveal_folder(self, path: str | Path) -> bool:
        target = Path(path)
        folder = target if target.is_dir() else target.parent
        if not folder.is_dir():
            return False
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            return True
        except Exception:
            return False
