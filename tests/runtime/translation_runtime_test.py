from pathlib import Path

from core.translation_runtime import TranslationRuntime, read_text_auto, split_text, format_translation_output


def test_runtime_facade_and_helpers(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    runtime = TranslationRuntime(root=root)
    assert runtime.version == "1.2-professional-stage-03"
    assert runtime.engine.root == root

    sample = tmp_path / "sample.txt"
    sample.write_bytes("第一段\n\n第二段".encode("utf-8-sig"))
    text = read_text_auto(sample)
    assert "第一段" in text
    assert split_text(text, 300)
    assert format_translation_output('他说, "你好"!') == "他說， 「你好」！"


def test_package_missing_is_compatible():
    root = Path(__file__).resolve().parents[2]
    runtime = TranslationRuntime(root=root)
    result = runtime.translate_package_file(root / "prompt_packages" / "__missing__.json")
    assert result["status"] == "failed"
    assert "不存在" in result["error"]
