import subprocess
import sys
from pathlib import Path


def test_stage04_launcher_dry_run_accepts_qa_options(tmp_path):
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
            '--qa-fail-policy',
            'warn',
            '--max-korean-chars',
            '0',
            '--min-length-ratio',
            '0.2',
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert 'status: success' in result.stdout
    assert (output / 'novel_translation_manifest.json').exists()
