from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .distribution import build_distribution_metadata
from .installer import CLIInstaller
from .manifest import build_cli_packaging_manifest
from .version import read_cli_version


@dataclass
class ReleaseBuilder:
    root: Path
    channel: str = 'beta'
    artifacts: List[str] = field(default_factory=lambda: ['source-zip', 'wheel-metadata', 'cli-entrypoint'])

    def build(self) -> Dict[str, Any]:
        version = read_cli_version(self.root)
        installer = CLIInstaller(self.root)
        return {
            'name': 'NTPE CLI',
            'package': 'ntpe',
            'version': version.version,
            'stage': version.stage,
            'channel': self.channel,
            'artifacts': list(self.artifacts),
            'distribution': build_distribution_metadata(self.root),
            'install_verification': installer.verify().to_dict(),
            'manifest': build_cli_packaging_manifest(),
        }

    def write_json(self, path: Path) -> Dict[str, Any]:
        payload = self.build()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return payload


def build_release_manifest(root: Optional[Path] = None, channel: str = 'beta') -> Dict[str, Any]:
    return ReleaseBuilder(Path(root or '.').resolve(), channel=channel).build()
