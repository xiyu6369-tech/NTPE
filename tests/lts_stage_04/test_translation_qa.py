import json
from pathlib import Path

import lts.txt_translation_runtime as runtime
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    count_korean_characters,
    detect_repeated_lines,
    translate_txt,
)


def test_count_korean_characters_detects_hangul():
    assert count_korean_characters('鄭泰義는 창밖을 보았다。') >= 6
    assert count_korean_characters('鄭泰義望向窗外。') == 0


def test_analyze_translation_quality_flags_korean_residue_and_short_output(tmp_path):
    options = TxtTranslationOptions(
        input_path=tmp_path / 'in.txt',
        output_dir=tmp_path / 'out',
        min_length_ratio=0.5,
        max_korean_chars=1,
    )
    report = analyze_translation_quality('정태의는 창밖을 바라보았다. 그리고 오래 침묵했다.', '정태의', options)
    assert not report['passed']
    codes = {issue['code'] for issue in report['issues']}
    assert 'KOREAN_RESIDUE' in codes
    assert 'LENGTH_RATIO_TOO_LOW' in codes


def test_detect_repeated_lines_flags_duplicate_output():
    text = '同一句話。\n同一句話。\n同一句話。\n短\n短\n短\n'
    assert detect_repeated_lines(text, max_repeated_lines=2) == ['同一句話。']


def test_translate_txt_qa_warn_records_qa_without_failing(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'sample.txt'
    source.write_text('정태의는 창밖을 보았다. 그리고 오래 침묵했다.\n', encoding='utf-8')

    class FakeEngine:
        def __init__(self, root=None):
            self.root = root
        def translate_package(self, package, package_path=None):
            out = root / 'tmp_provider_output.txt'
            out.write_text('정태의\n', encoding='utf-8')
            return {'status': 'success', 'output_path': str(out)}

    monkeypatch.setattr(runtime, 'TranslationEngine', FakeEngine)
    result = translate_txt(
        TxtTranslationOptions(
            input_path=source,
            output_dir=root / 'out',
            qa_fail_policy='warn',
            max_korean_chars=0,
            min_length_ratio=0.8,
        ),
        root=root,
    )
    assert result['status'] == 'success'
    assert not result['records'][0]['qa']['passed']
    manifest = json.loads((root / 'out' / 'sample_translation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['qa']['fail_policy'] == 'warn'


def test_translate_txt_qa_fail_stops_chunk(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'sample.txt'
    source.write_text('정태의는 창밖을 보았다. 그리고 오래 침묵했다.\n', encoding='utf-8')

    class FakeEngine:
        def __init__(self, root=None):
            self.root = root
        def translate_package(self, package, package_path=None):
            out = root / 'tmp_provider_output.txt'
            out.write_text('정태의\n', encoding='utf-8')
            return {'status': 'success', 'output_path': str(out)}

    monkeypatch.setattr(runtime, 'TranslationEngine', FakeEngine)
    result = translate_txt(
        TxtTranslationOptions(
            input_path=source,
            output_dir=root / 'out',
            qa_fail_policy='fail',
            max_korean_chars=0,
            min_length_ratio=0.8,
        ),
        root=root,
    )
    assert result['status'] == 'failed'
    assert result['failed_chunk'] == 1
    state = json.loads((root / 'out' / 'sample_resume_state.json').read_text(encoding='utf-8'))
    assert state['chunks']['000001']['status'] == 'qa_failed'
