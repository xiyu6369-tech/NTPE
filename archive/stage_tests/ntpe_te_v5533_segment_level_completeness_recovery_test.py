from __future__ import annotations

import tempfile
from pathlib import Path

from core.translation_quality_v5.segment_recovery import (
    completeness_issue_codes,
    should_use_segment_recovery,
    split_recovery_segments,
)
from lts.txt_translation_runtime import TxtTranslationOptions, build_prompt_package, translate_completeness_segments


class FakeEngine:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.calls: list[str] = []

    def translate_package(self, package: dict, package_path: Path | None = None) -> dict:
        source = package["source"]["chunk_text"]
        self.calls.append(source)
        path = self.output_dir / f"{package['package_id']}.txt"
        path.write_text("譯文：" + source.strip(), encoding="utf-8")
        return {"status": "success", "output_path": str(path)}


def _qa_report() -> dict:
    issue = {
        "code": "PARAGRAPH_OMISSION_SUSPECTED",
        "severity": "high",
        "retry_required": True,
        "message": "疑似漏段",
    }
    return {
        "passed": False,
        "issues": [issue],
        "unified_quality_report": {"merged_issues": [issue]},
    }


def main() -> int:
    source = (
        "第一段包含完整的事件與人物動作。第一段還有第二句，用來測試安全分段。\n\n"
        "第二段包含一段對話與回應。第二段還有後續敘事，不能被省略。\n\n"
        "第三段交代場景轉換與人物反應。第三段最後補上一句結尾。\n"
    ) * 5
    segments = split_recovery_segments(source)
    assert len(segments) >= 2
    assert "".join(part.strip() for part in segments).replace("\n", "") == source.strip().replace("\n", "")
    assert completeness_issue_codes(_qa_report()) == ("PARAGRAPH_OMISSION_SUSPECTED",)
    assert should_use_segment_recovery(_qa_report(), source)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "prompt_packages" / "txt_runtime").mkdir(parents=True)
        out = root / "output"
        chunks = out / "sample_chunks"
        chunks.mkdir(parents=True)
        options = TxtTranslationOptions(
            input_path=Path("sample.txt"),
            output_dir=out,
            chunk_size=600,
            provider_attempts=1,
            qa_attempts=2,
        )
        parent = build_prompt_package(
            options=options,
            chunk_text=source,
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={},
            previous_context="",
        )
        engine = FakeEngine(root)
        result = translate_completeness_segments(
            engine=engine,
            options=options,
            root_path=root,
            stage_dir=root / "prompt_packages" / "txt_runtime",
            chunk_out_dir=chunks,
            input_path=Path("sample.txt"),
            chunk_text=source,
            chunk_index=1,
            chunk_total=1,
            locked_dictionary={},
            previous_context="",
            qa_report=_qa_report(),
            parent_package=parent,
        )
        assert result["status"] == "success"
        assert len(engine.calls) == len(segments)
        combined = Path(result["output_path"]).read_text(encoding="utf-8")
        assert combined.count("譯文：") == len(segments)
        meta = parent["prompt_runtime"]["segment_completeness_recovery"]
        assert meta["version"] == "5.5.3.3"
        assert meta["segment_count"] == len(segments)

    print("TE v5.5.3.3 Segment-Level Completeness Recovery Test")
    print("====================================================")
    print("Completeness issue routes to segment recovery PASS")
    print("Source order and coverage preserved             PASS")
    print("Smaller provider requests generated             PASS")
    print("Combined recovery candidate saved               PASS")
    print("Recovery metadata recorded                      PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
