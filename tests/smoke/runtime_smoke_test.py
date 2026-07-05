from pathlib import Path

from core.translation_runtime import TranslationRuntime
from lts.txt_translation_runtime import TxtTranslationOptions
from lts.batch_translation_runtime import BatchTranslationOptions


def test_txt_runtime_dry_run_smoke(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / "novel.txt"
    source.write_text("정태의는 문 앞에 섰다.\n\n그는 잠시 숨을 골랐다.\n", encoding="utf-8")
    output = tmp_path / "out"
    options = TxtTranslationOptions(input_path=source, output_dir=output, dry_run=True, chunk_size=300, qa_enabled=False)
    result = TranslationRuntime(root=root).translate_txt(options)
    assert result["status"] == "success"
    assert result["chunk_total"] >= 1
    assert Path(output / "novel_translation_manifest.json").exists()


def test_batch_runtime_dry_run_smoke(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "001.txt").write_text("정태의는 문 앞에 섰다.\n", encoding="utf-8")
    output_dir = tmp_path / "output"
    options = BatchTranslationOptions(input_dir=input_dir, output_dir=output_dir, dry_run=True, chunk_size=300, qa_enabled=False, progress=False)
    result = TranslationRuntime(root=root).translate_batch(options)
    assert result["status"] == "success"
    assert result["summary"]["total_files"] == 1
    assert result["summary"]["success"] == 1
