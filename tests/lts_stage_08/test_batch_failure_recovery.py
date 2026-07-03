import json
from pathlib import Path

import lts.batch_translation_runtime as batch
from lts.batch_translation_runtime import BatchTranslationOptions, parse_args, translate_batch


def test_continue_on_failure_records_failed_manifest_and_keeps_processing(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    input_dir = root / 'input'
    output_dir = root / 'output'
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    (input_dir / '001.txt').write_text('첫 번째 파일', encoding='utf-8')
    (input_dir / '002.txt').write_text('두 번째 파일', encoding='utf-8')
    (input_dir / '003.txt').write_text('세 번째 파일', encoding='utf-8')

    def fake_translate_txt(options, root=None):
        name = Path(options.input_path).name
        if name == '002.txt':
            return {'status': 'failed', 'input': str(options.input_path), 'error': 'provider failed', 'chunk_total': 1}
        final = Path(options.output_dir) / f"{Path(options.input_path).stem}_zh.txt"
        final.write_text('翻譯完成。', encoding='utf-8')
        return {'status': 'success', 'input': str(options.input_path), 'output': str(final), 'chunk_total': 1, 'records': [{'status': 'success', 'attempt': 1, 'qa_attempt': 1, 'qa': {'issues': []}}]}

    monkeypatch.setattr(batch, 'translate_txt', fake_translate_txt)
    result = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir, continue_on_failure=True, progress=False), root=root)
    assert result['status'] == 'partial_success'
    assert result['version'] == '1.1-lts-stage-08'
    assert result['summary']['completed_files'] == 3
    assert result['summary']['success'] == 2
    assert result['summary']['failed'] == 1
    failure_manifest = Path(result['failure_manifest'])
    assert failure_manifest.exists()
    manifest = json.loads(failure_manifest.read_text(encoding='utf-8'))
    assert manifest['failed_count'] == 1
    assert manifest['failed_files'][0]['input'].endswith('002.txt')


def test_failed_only_uses_failure_manifest(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    input_dir = root / 'input'
    output_dir = root / 'output'
    report_dir = output_dir / 'reports'
    input_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    (input_dir / '001.txt').write_text('첫 번째 파일', encoding='utf-8')
    (input_dir / '002.txt').write_text('두 번째 파일', encoding='utf-8')
    manifest = report_dir / 'Batch_Failure_Manifest.json'
    manifest.write_text(json.dumps({'failed_files': [{'input': str(input_dir / '002.txt')}]}, ensure_ascii=False), encoding='utf-8')
    calls = []

    def fake_translate_txt(options, root=None):
        calls.append(Path(options.input_path).name)
        final = Path(options.output_dir) / f"{Path(options.input_path).stem}_zh.txt"
        final.write_text('補譯完成。', encoding='utf-8')
        return {'status': 'success', 'input': str(options.input_path), 'output': str(final), 'chunk_total': 1, 'records': []}

    monkeypatch.setattr(batch, 'translate_txt', fake_translate_txt)
    result = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir, failed_only=True, progress=False), root=root)
    assert calls == ['002.txt']
    assert result['status'] == 'success'
    assert result['summary']['total_files'] == 1
    assert result['summary']['failed_only'] is True


def test_stage08_parse_args_recovery_flags():
    options = parse_args(['input', 'output', '--continue-on-failure', '--failed-only', '--failed-manifest', 'reports/failed.json'])
    assert options.continue_on_failure is True
    assert options.failed_only is True
    assert options.failed_manifest == Path('reports/failed.json')
