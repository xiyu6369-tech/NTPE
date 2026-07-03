from pathlib import Path

from lts.txt_translation_runtime import main


def test_launcher_dry_run_accepts_retry_options(tmp_path, monkeypatch):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'input.txt'
    source.write_text('정태의는 걸었다.\n', encoding='utf-8')
    monkeypatch.chdir(root)
    code = main([str(source), str(root / 'out'), '--dry-run', '--max-retries', '1', '--retry-base-seconds', '0'])
    assert code == 0
    assert (root / 'out' / 'input_resume_state.json').exists()
