from __future__ import annotations

from typing import Any, Dict, MutableMapping


def build_cli_manifest() -> Dict[str, Any]:
    return {
        'name': 'NTPE CLI',
        'stage': 'NTPE 1.0 Beta Stage-06.9 CLI Freeze',
        'version': '0.6.9',
        'status': 'frozen',
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
            'cli_freeze',
            'compatibility_manifest',
            'regression_suite',
            'acceptance_cli',
        ],
        'frozen_contracts': [
            'command_names',
            'command_options',
            'exit_codes',
            'json_output_schema',
            'text_output_format',
            'help_output_contract',
        ],
        'foundation_compatibility': 'foundation-v1.0 frozen compatible',
        'cli_baseline': 'beta-1.0-cli',
        'backward_compatible': True,
    }


def attach_cli_manifest(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    payload.setdefault('manifests', {})['cli'] = build_cli_manifest()
    try:
        from cli.freeze.manifest import attach_cli_freeze_manifest
        attach_cli_freeze_manifest(payload)
    except Exception:
        # Keep the core manifest available even if freeze modules are not imported yet.
        pass
    return payload
