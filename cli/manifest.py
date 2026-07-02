from __future__ import annotations

from typing import Any, Dict, MutableMapping


def build_cli_manifest() -> Dict[str, Any]:
    return {
        'name': 'NTPE CLI',
        'stage': 'NTPE 1.0 Beta Stage-06.8',
        'version': '0.6.8',
        'status': 'beta',
        'commands': [
            'version', 'doctor', 'translate', 'project', 'benchmark',
            'quality', 'session', 'config', 'plugin',
        ],
        'capabilities': [
            'cli_context',
            'cli_result',
            'command_registry',
            'argparse_parser',
            'version_command',
            'doctor_command',
            'module_entrypoint',
            'translate_command',
            'project_command',
            'benchmark_command',
            'quality_command',
            'session_command',
            'config_command',
            'plugin_command',
            'cli_packaging',
            'entrypoint_verification',
            'distribution_metadata',
            'release_manifest',
            'install_verification',
        ],
        'foundation_compatibility': 'foundation-v1.0 frozen compatible',
        'backward_compatible': True,
    }


def attach_cli_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault('manifests', {})['cli'] = build_cli_manifest()
    return payload
