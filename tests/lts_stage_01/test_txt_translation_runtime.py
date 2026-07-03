from pathlib import Path

from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    build_prompt_package,
    read_text_auto,
    split_text,
    translate_txt,
)


def test_split_text_preserves_content():
    text = "첫 문장입니다.\n\n두 번째 문장입니다.\n\n세 번째 문장입니다."
    chunks = split_text(text, chunk_size=300)
    assert len(chunks) == 1
    assert "첫 문장" in chunks[0]
    assert "세 번째" in chunks[0]


def test_build_prompt_package_contains_locked_name(tmp_path):
    options = TxtTranslationOptions(input_path=tmp_path / "sample.txt", output_dir=tmp_path / "out")
    package = build_prompt_package(
        options=options,
        chunk_text="정태의는 창밖을 보았다.",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={"정태의": "鄭泰義"},
    )
    assert package["session"]["chunk_index"] == 1
    assert package["knowledge"]["locked_dictionary"] == {"정태의": "鄭泰義"}
    assert "정태의 → 鄭泰義" in package["prompt"]["user_prompt"]


def test_read_text_auto_cp949(tmp_path):
    path = tmp_path / "ko.txt"
    path.write_bytes("정태의".encode("cp949"))
    assert read_text_auto(path).strip() == "정태의"


def test_translate_txt_dry_run(tmp_path):
    root = tmp_path / "NTPE"
    root.mkdir()
    source = root / "input.txt"
    source.write_text("일라이가 방 안으로 들어왔다.\n정태의는 그를 바라보았다.\n", encoding="utf-8")
    (root / "character_override.json").write_text('{"정태의":"鄭泰義","일라이":"伊萊"}', encoding="utf-8")
    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / "out", dry_run=True),
        root=root,
    )
    assert result["status"] == "success"
    assert result["chunk_total"] == 1
    manifest = root / "out" / "input_translation_manifest.json"
    assert manifest.exists()
    package = root / "prompt_packages" / "txt_runtime" / "input_chunk_000001.json"
    assert package.exists()
