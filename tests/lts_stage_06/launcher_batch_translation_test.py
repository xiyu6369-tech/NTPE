import subprocess
import sys
from pathlib import Path


def test_stage06_launcher_dry_run_batch(tmp_path):
    root = Path(__file__).resolve().parents[2]
    input_dir = tmp_path / 'input'
    output_dir = tmp_path / 'output'
    input_dir.mkdir()
    (input_dir / 'chapter2.txt').write_text('정태의는 창밖을 보았다.\n', encoding='utf-8')
    (input_dir / 'chapter1.txt').write_text('일라이는 조용히 웃었다.\n', encoding='utf-8')
    result = subprocess.run(
        [
            sys.executable,
            str(root / 'ntpe_translate_batch.py'),
            str(input_dir),
            str(output_dir),
            '--dry-run',
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'status: success' in result.stdout
    assert '2 success' in result.stdout
    assert (output_dir / 'reports' / 'Batch_Translation_Report.json').exists()
