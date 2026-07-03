import json

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    apply_locked_dictionary,
    collect_matched_locked_terms,
    load_glossary_text,
    load_locked_dictionary,
    translate_txt,
    update_character_memory,
)


def test_load_glossary_text_supports_multiple_delimiters(tmp_path):
    glossary = tmp_path / 'glossary.txt'
    glossary.write_text('정태의=鄭泰義\n일라이 -> 伊萊\n카일 → 凱爾\n# comment\n', encoding='utf-8')
    assert load_glossary_text(glossary) == {
        '정태의': '鄭泰義',
        '일라이': '伊萊',
        '카일': '凱爾',
    }


def test_apply_locked_dictionary_removes_source_residue():
    text = '정태의望向窗外，일라이站在門口。'
    fixed = apply_locked_dictionary(text, {'정태의': '鄭泰義', '일라이': '伊萊'})
    assert fixed == '鄭泰義望向窗外，伊萊站在門口。'


def test_load_locked_dictionary_merges_custom_glossary_and_memory(tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    (root / 'character_override.json').write_text('{"정태의":"鄭泰義"}', encoding='utf-8')
    (root / 'custom_glossary.txt').write_text('일라이=伊萊\n', encoding='utf-8')
    memory = root / 'memory' / 'character_memory_lts.json'
    memory.parent.mkdir()
    memory.write_text(json.dumps({'characters': {'카일': '凱爾'}}, ensure_ascii=False), encoding='utf-8')
    options = TxtTranslationOptions(input_path=root / 'in.txt', output_dir=root / 'out', glossary_path=root / 'custom_glossary.txt')
    locked = load_locked_dictionary(root, options)
    assert locked['정태의'] == '鄭泰義'
    assert locked['일라이'] == '伊萊'
    assert locked['카일'] == '凱爾'


def test_update_character_memory_persists_matched_terms(tmp_path):
    path = tmp_path / 'memory' / 'characters.json'
    update_character_memory(path, {'정태의': '鄭泰義'})
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['version'] == '1.1-lts-stage-03'
    assert data['characters']['정태의'] == '鄭泰義'


def test_translate_txt_dry_run_records_glossary_metadata(tmp_path):
    root = tmp_path / 'NTPE'
    root.mkdir()
    source = root / 'sample.txt'
    source.write_text('정태의는 일라이를 보았다.\n', encoding='utf-8')
    glossary = root / 'glossary.txt'
    glossary.write_text('정태의=鄭泰義\n일라이=伊萊\n', encoding='utf-8')
    result = translate_txt(TxtTranslationOptions(input_path=source, output_dir=root / 'out', dry_run=True), root=root)
    assert result['status'] == 'success'
    manifest = json.loads((root / 'out' / 'sample_translation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['glossary']['matched_terms'] == 2
    package = json.loads((root / 'prompt_packages' / 'txt_runtime' / 'sample_chunk_000001.json').read_text(encoding='utf-8'))
    assert package['knowledge']['locked_dictionary'] == {'정태의': '鄭泰義', '일라이': '伊萊'}


def test_collect_matched_locked_terms_only_records_used_terms():
    matched = collect_matched_locked_terms(['정태의는 창밖을 보았다.'], {'정태의': '鄭泰義', '일라이': '伊萊'})
    assert matched == {'정태의': '鄭泰義'}
