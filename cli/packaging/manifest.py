from __future__ import annotations

from typing import Any, Dict


def build_cli_packaging_manifest() -> Dict[str, Any]:
    return {
        'component': 'cli.packaging',
        'version': '1.0-beta-stage-06.8',
        'entrypoints': ['ntpe', 'python -m cli'],
        'features': [
            'version-management',
            'entrypoint-verification',
            'distribution-metadata',
            'release-manifest',
            'install-verification',
            'windows-first-packaging',
        ],
        'compatible_with': [
            'foundation-v1.0',
            'beta-stage-01',
            'beta-stage-02',
            'beta-stage-03',
            'beta-stage-04',
            'beta-stage-05',
            'beta-stage-06.0',
            'beta-stage-06.1',
            'beta-stage-06.2',
            'beta-stage-06.3',
            'beta-stage-06.4',
            'beta-stage-06.5',
            'beta-stage-06.6',
            'beta-stage-06.7',
        ],
    }


def attach_cli_packaging_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload.setdefault('manifests', {})['cli_packaging'] = build_cli_packaging_manifest()
    return payload
