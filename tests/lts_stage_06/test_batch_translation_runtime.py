import json
from pathlib import Path

import lts.batch_translation_runtime as batch
from lts.batch_translation_runtime import (
    BatchTranslationOptions,
    get_output_path_for_input,
    natural_sort_key,
    scan_txt_files,
    translate_batch,
)


def test_natural_sort_key_orders_numbered_files(tmp_path):
    files = [Path('chapter10.txt'), Path('chapter2.txt'), Path('chapter1.txt')]
    ordered = sorted(files, key=natural_sort_key)
    assert [p.name for p in ordered] == ['chapter1.txt', 'chapter2.txt', 'chapter10.txt']


def test_scan_txt_files_non_recursive_and_recursive(tmp_path):
    input_dir = tmp_path / 'input'
    nested = input_dir / 'nested'
    nested.mkdir(parents=True)
    (input_dir / '002.txt').write_text('b', encoding='utf-8')
    (input_dir / '001.txt').write_text('a', encoding='utf-8')
    (nested / '003.txt').write_text('c', encoding='utf-8')
    (input_dir / 'ignore.md').write_text('x', encoding='utf-8')
    assert [p.name for p in scan_txt_files(input_dir)] == ['001.txt', '002.txt']
    assert [p.name for p in scan_txt_files(input_dir, recursive=True)] == ['001.txt', '002.txt', '003.txt']


def test_get_output_path_preserves_subfolder(tmp_path):
    input_dir = tmp_path / 'input'
    source = input_dir / 'vol1' / '001.txt'
    output = tmp_path / 'output'
    assert get_output_path_for_input(source, input_dir, output) == output / 'vol1' / '001_zh.txt'


def test_translate_batch_skips_completed_and_writes_report(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    input_dir = root / 'input'
    output_dir = root / 'output'
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    (input_dir / '001.txt').write_text('이미 완료된 파일', encoding='utf-8')
    (input_dir / '002.txt').write_text('번역할 파일', encoding='utf-8')
    (output_dir / '001_zh.txt').write_text('已完成。', encoding='utf-8')

    def fake_translate_txt(options, root=None):
        final = Path(options.output_dir) / f"{Path(options.input_path).stem}_zh.txt"
        final.write_text('翻譯完成。', encoding='utf-8')
        return {'status': 'success', 'input': str(options.input_path), 'output': str(final), 'chunk_total': 2, 'resume_state': str(final.with_suffix('.json'))}

    monkeypatch.setattr(batch, 'translate_txt', fake_translate_txt)
    result = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir), root=root)
    assert result['status'] == 'success'
    assert result['summary']['total_files'] == 2
    assert result['summary']['skipped'] == 1
    assert result['summary']['success'] == 1
    assert result['summary']['total_chunks'] == 2
    report = json.loads((output_dir / 'reports' / 'Batch_Translation_Report.json').read_text(encoding='utf-8'))
    assert report['summary']['success'] == 1
    assert (output_dir / 'reports' / 'Batch_Translation_Report.md').exists()


def test_translate_batch_stops_on_failed_file(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    input_dir = root / 'input'
    output_dir = root / 'output'
    input_dir.mkdir(parents=True)
    (input_dir / '001.txt').write_text('실패할 파일', encoding='utf-8')

    def fake_translate_txt(options, root=None):
        return {'status': 'failed', 'input': str(options.input_path), 'error': 'provider failed', 'chunk_total': 1}

    monkeypatch.setattr(batch, 'translate_txt', fake_translate_txt)
    result = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir), root=root)
    assert result['status'] == 'failed'
    assert result['summary']['failed'] == 1
    assert result['files'][0]['error'] == 'provider failed'
