from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


ENTRYPOINT_NAME = 'ntpe'
ENTRYPOINT_TARGET = 'cli.main:main'
MODULE_ENTRYPOINT = 'python -m cli'


def build_entrypoint_payload(root: Optional[Path] = None) -> Dict[str, Any]:
    root = Path(root or '.').resolve()
    return {
        'name': ENTRYPOINT_NAME,
        'target': ENTRYPOINT_TARGET,
        'module': MODULE_ENTRYPOINT,
        'root': str(root),
        'available': (root / 'cli' / 'main.py').exists(),
    }


def verify_entrypoint(root: Optional[Path] = None) -> Dict[str, Any]:
    payload = build_entrypoint_payload(root)
    payload['ok'] = bool(payload['available'] and payload['target'] == ENTRYPOINT_TARGET)
    payload['errors'] = [] if payload['ok'] else ['cli.main:main entrypoint is not available']
    return payload
