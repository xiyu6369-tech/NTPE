from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .entrypoint import verify_entrypoint
from .distribution import build_distribution_metadata
from .manifest import build_cli_packaging_manifest


@dataclass
class InstallVerification:
    ok: bool
    root: str
    checks: Dict[str, bool]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CLIInstaller:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or '.').resolve()

    def verify(self) -> InstallVerification:
        checks = {
            'cli_package': (self.root / 'cli').exists(),
            'cli_main': (self.root / 'cli' / 'main.py').exists(),
            'cli_module': (self.root / 'cli' / '__main__.py').exists(),
            'commands_package': (self.root / 'cli' / 'commands').exists(),
            'packaging_package': (self.root / 'cli' / 'packaging').exists(),
            'entrypoint': bool(verify_entrypoint(self.root).get('ok')),
        }
        errors = [name for name, ok in checks.items() if not ok]
        return InstallVerification(ok=not errors, root=str(self.root), checks=checks, errors=errors)

    def build_metadata(self) -> Dict[str, Any]:
        payload = build_distribution_metadata(self.root)
        payload['install'] = self.verify().to_dict()
        payload['manifest'] = build_cli_packaging_manifest()
        return payload
