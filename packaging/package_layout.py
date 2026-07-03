"""Release package layout helpers for NTPE Stage-14.1."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

from .package_errors import PackageLayoutError


DEFAULT_RELEASE_DIRECTORIES = (
    "full",
    "increment",
    "portable",
    "wheel",
    "source",
    "reports",
    "manifests",
)


@dataclass
class PackageLayout:
    """Declarative release output layout."""

    root: Path
    directories: Iterable[str] = field(default_factory=lambda: DEFAULT_RELEASE_DIRECTORIES)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def paths(self) -> Dict[str, Path]:
        return {name: self.root / name for name in self.directories}

    def create(self) -> Dict[str, str]:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            for path in self.paths().values():
                path.mkdir(parents=True, exist_ok=True)
                (path / ".gitkeep").touch(exist_ok=True)
        except OSError as exc:
            raise PackageLayoutError(str(exc)) from exc
        return {name: str(path) for name, path in self.paths().items()}

    def validate(self) -> Dict[str, object]:
        missing: List[str] = [name for name, path in self.paths().items() if not path.exists()]
        return {
            "valid": not missing,
            "root": str(self.root),
            "directories": list(self.paths().keys()),
            "missing": missing,
        }
