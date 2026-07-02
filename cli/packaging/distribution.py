from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .version import read_cli_version
from .entrypoint import ENTRYPOINT_NAME, ENTRYPOINT_TARGET


@dataclass
class DistributionMetadata:
    name: str = 'ntpe'
    version: str = '1.0.0-beta'
    description: str = 'Novel Translation Professional Engine CLI'
    python_requires: str = '>=3.10'
    entrypoints: Dict[str, str] = field(default_factory=lambda: {ENTRYPOINT_NAME: ENTRYPOINT_TARGET})
    packages: List[str] = field(default_factory=lambda: ['cli', 'core', 'translation', 'benchmark'])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_distribution_metadata(root: Optional[Path] = None) -> Dict[str, Any]:
    version = read_cli_version(root)
    metadata = DistributionMetadata(version=version.version)
    payload = metadata.to_dict()
    payload['root'] = str(Path(root or '.').resolve())
    payload['stage'] = version.stage
    return payload
