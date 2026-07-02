from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cli.manifest import build_cli_manifest
from cli.packaging import (
    CLIInstaller,
    ReleaseBuilder,
    attach_cli_packaging_manifest,
    build_cli_packaging_manifest,
    build_distribution_metadata,
    build_entrypoint_payload,
    build_release_manifest,
    build_version_payload,
    verify_entrypoint,
)


def result(name: str, ok: bool) -> None:
    print(f"{name:<35} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(name)


def make_project(tmp: Path) -> Path:
    root = tmp / 'project'
    (root / 'cli' / 'commands').mkdir(parents=True)
    (root / 'cli' / 'packaging').mkdir(parents=True)
    (root / 'cli' / 'main.py').write_text('def main(argv=None):\n    return 0\n', encoding='utf-8')
    (root / 'cli' / '__main__.py').write_text('from .main import main\nraise SystemExit(main())\n', encoding='utf-8')
    (root / 'cli' / '__init__.py').write_text('', encoding='utf-8')
    (root / 'VERSION').write_text('1.0.0-beta-test', encoding='utf-8')
    return root


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = make_project(tmp)

        version = build_version_payload(root)
        result('Version Manager', version['version'] == '1.0.0-beta-test')

        entrypoint = build_entrypoint_payload(root)
        result('CLI Entrypoint', entrypoint['name'] == 'ntpe' and entrypoint['target'] == 'cli.main:main')

        verified = verify_entrypoint(root)
        result('Entrypoint Verification', verified['ok'] is True)

        metadata = build_distribution_metadata(root)
        result('Package Metadata', metadata['name'] == 'ntpe' and metadata['entrypoints']['ntpe'] == 'cli.main:main')

        installer = CLIInstaller(root)
        install = installer.verify().to_dict()
        result('Installer', install['ok'] is True and install['checks']['cli_main'] is True)

        distribution = installer.build_metadata()
        result('Distribution', distribution['install']['ok'] is True and distribution['manifest']['component'] == 'cli.packaging')

        manifest = build_cli_packaging_manifest()
        result('Release Manifest', manifest['version'] == '1.0-beta-stage-06.8')

        attached = attach_cli_packaging_manifest({'ok': True})
        result('Manifest Helper', 'cli_packaging' in attached['manifests'])

        release = build_release_manifest(root)
        result('Release Builder', release['install_verification']['ok'] is True and release['package'] == 'ntpe')

        report_path = tmp / 'release' / 'ntpe_cli_release.json'
        written = ReleaseBuilder(root).write_json(report_path)
        loaded = json.loads(report_path.read_text(encoding='utf-8'))
        result('Release JSON', loaded['version'] == written['version'])

        current_cli_manifest = build_cli_manifest()
        result('CLI Manifest', 'cli_packaging' in current_cli_manifest['capabilities'])

        result('Install Verification', CLIInstaller(ROOT).verify().to_dict()['checks']['cli_package'] is True)
        result('Acceptance Packaging', verified['target'] == 'cli.main:main' and metadata['python_requires'].startswith('>='))
        result('Backward Compatible', current_cli_manifest['backward_compatible'] is True)

    print('PASS')


if __name__ == '__main__':
    main()
