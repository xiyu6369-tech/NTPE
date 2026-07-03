import json
from pathlib import Path

import lts.batch_translation_runtime as batch
from lts.batch_translation_runtime import (
    BatchProgressSnapshot,
    BatchTranslationOptions,
    estimate_remaining_seconds,
    format_duration,
    format_progress_line,
    summarize_txt_result,
    translate_batch,
)


def test_format_duration_and_eta_helpers():
    assert format_duration(0) == '00:00:00'
    assert format_duration(3661) == '01:01:01'
    assert estimate_remaining_seconds(2, 4, 10) == 10
    assert estimate_remaining_seconds(4, 4, 10) == 0.0
    assert estimate_remaining_seconds(0, 4, 10) is None


def test_format_progress_line_includes_core_metrics():
    snapshot = BatchProgressSnapshot(
        index=2,
        total=10,
        status='success',
        input_name='chapter02.txt',
        success=2,
        skipped=1,
        failed=0,
        elapsed_seconds=65,
        eta_seconds=140,
    )
    line = format_progress_line(snapshot)
    assert '[3/10 30.00%]' in line
    assert 'success: chapter02.txt' in line
    assert 'elapsed=00:01:05' in line
    assert 'eta=00:02:20' in line


def test_summarize_txt_result_collects_retry_and_qa_metrics():
    result = {
        'records': [
            {'status': 'success', 'attempt': 2, 'qa_attempt': 1, 'qa': {'issues': []}},
            {'status': 'success', 'attempt': 1, 'qa_attempt': 3, 'qa': {'issues': [{'code': 'KOREAN_RESIDUE'}]}},
            {'status': 'skipped', 'attempt': 0, 'qa_attempt': 0},
        ]
    }
    metrics = summarize_txt_result(result)
    assert metrics['provider_attempts'] == 3
    assert metrics['provider_retry_count'] == 0
    assert metrics['qa_retry_count'] == 2
    assert metrics['qa_issue_count'] == 1
    assert metrics['korean_residue_issues'] == 1
    assert metrics['skipped_chunks'] == 1


def test_translate_batch_writes_stage07_progress_and_summary(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    input_dir = root / 'input'
    output_dir = root / 'output'
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    (input_dir / '001.txt').write_text('첫 번째 파일', encoding='utf-8')
    (input_dir / '002.txt').write_text('두 번째 파일', encoding='utf-8')

    def fake_translate_txt(options, root=None):
        final = Path(options.output_dir) / f"{Path(options.input_path).stem}_zh.txt"
        final.write_text('翻譯完成。', encoding='utf-8')
        return {
            'status': 'success',
            'input': str(options.input_path),
            'output': str(final),
            'chunk_total': 2,
            'resume_state': str(final.with_suffix('.json')),
            'records': [
                {'status': 'success', 'attempt': 2, 'qa_attempt': 1, 'qa': {'issues': []}},
                {'status': 'success', 'attempt': 1, 'qa_attempt': 2, 'qa': {'issues': [{'code': 'KOREAN_RESIDUE'}]}},
            ],
        }

    monkeypatch.setattr(batch, 'translate_txt', fake_translate_txt)
    result = translate_batch(BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir, progress=False), root=root)
    assert result['version'] == '1.1-lts-stage-07'
    assert result['summary']['completed_files'] == 2
    assert result['summary']['success_rate_percent'] == 100.0
    assert result['summary']['provider_attempts'] == 6
    assert result['summary']['qa_retry_count'] == 2
    assert result['summary']['korean_residue_issues'] == 2
    assert result['progress_log']
    report = json.loads((output_dir / 'reports' / 'Batch_Translation_Report.json').read_text(encoding='utf-8'))
    assert report['summary']['elapsed_hms'].count(':') == 2
    md = (output_dir / 'reports' / 'Batch_Translation_Report.md').read_text(encoding='utf-8')
    assert 'Stage-07 Batch Progress / Summary Report' in md
    assert 'Progress Log' in md
