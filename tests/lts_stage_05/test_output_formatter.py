import json

import lts.txt_translation_runtime as runtime
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    clean_provider_output,
    format_translation_output,
    normalize_punctuation_for_zh_tw,
    normalize_taiwan_traditional,
    translate_txt,
)


def test_clean_provider_output_removes_common_preamble():
    assert clean_provider_output('以下是翻譯：\n你好。') == '你好。'
    assert clean_provider_output('譯文：\n你好。') == '你好。'


def test_normalize_punctuation_for_zh_tw():
    text = '他說,"你好!" 她問: "真的嗎?"'
    fixed = normalize_punctuation_for_zh_tw(text)
    assert '，' in fixed
    assert '！' in fixed
    assert '：' in fixed
    assert '？' in fixed
    assert '「你好！」' in fixed


def test_normalize_taiwan_traditional_common_terms():
    text = '这里是台湾,他说门后没有声音。'
    fixed = normalize_taiwan_traditional(text)
    assert '這裡' in fixed
    assert '台灣' in fixed
    assert '他說' in fixed
    assert '門後' in fixed
    assert '沒有聲音' in fixed


def test_format_translation_output_can_be_disabled(tmp_path):
    options = TxtTranslationOptions(
        input_path=tmp_path / 'in.txt',
        output_dir=tmp_path / 'out',
        output_formatter_enabled=False,
    )
    assert format_translation_output('他说: "你好!"', options) == '他说: "你好!"'


def test_translate_txt_applies_formatter_and_manifest(monkeypatch, tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'sample.txt'
    source.write_text('정태의는 말했다.\n', encoding='utf-8')

    class FakeEngine:
        def __init__(self, root=None):
            self.root = root
        def translate_package(self, package, package_path=None):
            out = root / 'provider_output.txt'
            out.write_text('以下是翻譯：\n他说: "你好!"\n', encoding='utf-8')
            return {'status': 'success', 'output_path': str(out)}

    monkeypatch.setattr(runtime, 'TranslationEngine', FakeEngine)
    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / 'out', qa_fail_policy='warn'),
        root=root,
    )
    assert result['status'] == 'success'
    final_text = (root / 'out' / 'sample_zh.txt').read_text(encoding='utf-8')
    assert '他說： 「你好！」' in final_text or '他說：「你好！」' in final_text
    manifest = json.loads((root / 'out' / 'sample_translation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['formatter']['enabled'] is True
    assert manifest['formatter']['taiwan_traditional_normalization'] is True
