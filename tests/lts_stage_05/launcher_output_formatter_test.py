import subprocess
import sys
from pathlib import Path


def test_stage05_launcher_dry_run_accepts_formatter_options(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / 'novel.txt'
    source.write_text('정태의는 창밖을 보았다.\n', encoding='utf-8')
    output = tmp_path / 'out'
    result = subprocess.run(
        [
            sys.executable,
            str(root / 'ntpe_translate_txt.py'),
            str(source),
            str(output),
            '--dry-run',
            '--no-output-formatter',
            '--no-taiwan-normalization',
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'status: success' in result.stdout
    assert (output / 'novel_translation_manifest.json').exists()
