import json
from pathlib import Path

import lts.txt_translation_runtime as runtime
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    is_retryable_error,
    retry_delay_seconds,
    translate_package_with_retry,
    translate_txt,
)


def test_retryable_error_detection():
    assert is_retryable_error('NVIDIA API error 503: Service Unavailable')
    assert is_retryable_error('ResourceExhausted: Worker local total request limit reached')
    assert is_retryable_error('429 Too Many Requests')
    assert not is_retryable_error('invalid prompt package')


def test_retry_delay_seconds_exponential():
    assert retry_delay_seconds(1, 2) == 2
    assert retry_delay_seconds(2, 2) == 4
    assert retry_delay_seconds(3, 2) == 8


def test_translate_package_with_retry_retries_then_success(monkeypatch, tmp_path):
    calls = []

    class FakeEngine:
        def translate_package(self, package, package_path=None):
            calls.append(package['package_id'])
            if len(calls) == 1:
                return {'status': 'failed', 'error': 'NVIDIA API error 503: Service Unavailable'}
            return {'status': 'success', 'output_path': str(tmp_path / 'out.txt')}

    (tmp_path / 'out.txt').write_text('譯文\n', encoding='utf-8')
    monkeypatch.setattr(runtime.time, 'sleep', lambda _seconds: None)
    options = TxtTranslationOptions(input_path=tmp_path / 'in.txt', output_dir=tmp_path, max_retries=2, retry_base_seconds=0)
    result = translate_package_with_retry(FakeEngine(), {'package_id': 'p1'}, tmp_path / 'p1.json', options)
    assert result['status'] == 'success'
    assert result['attempt'] == 2
    assert len(calls) == 2


def test_translate_txt_resume_state_skips_completed_chunk(tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'sample.txt'
    source.write_text('정태의는 창밖을 보았다.\n', encoding='utf-8')
    output_dir = root / 'out'
    chunk_dir = output_dir / 'sample_chunks'
    chunk_dir.mkdir(parents=True)
    existing = chunk_dir / 'sample_chunk_000001_zh.txt'
    existing.write_text('鄭泰義望向窗外。\n', encoding='utf-8')

    # First run creates package/state in dry-run mode.
    translate_txt(TxtTranslationOptions(input_path=source, output_dir=output_dir, dry_run=True), root=root)
    package = json.loads((root / 'prompt_packages' / 'txt_runtime' / 'sample_chunk_000001.json').read_text(encoding='utf-8'))
    state_path = output_dir / 'sample_resume_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state['chunks']['000001'] = {
        'status': 'success',
        'source_hash': package['source']['source_hash'],
        'output_path': str(existing),
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')

    result = translate_txt(TxtTranslationOptions(input_path=source, output_dir=output_dir, dry_run=False), root=root)
    assert result['status'] == 'success'
    assert result['records'][0]['status'] == 'skipped'
    assert (output_dir / 'sample_zh.txt').read_text(encoding='utf-8').strip() == '鄭泰義望向窗外。'
