import subprocess
import sys
from pathlib import Path


def test_launcher_dry_run(tmp_path):
    root = Path(__file__).resolve().parents[2]
    sample = tmp_path / "sample.txt"
    out = tmp_path / "out"
    sample.write_text("정태의는 창밖을 보았다.\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(root / "ntpe_translate_txt.py"), str(sample), str(out), "--dry-run"],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "status: success" in proc.stdout
    assert (out / "sample_translation_manifest.json").exists()
