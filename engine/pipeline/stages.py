from __future__ import annotations

from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine

from .stage_result import StageResult
from .utils import now_iso, save_json


class PipelineStages:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def stage_prepare_demo_chunk(self, session, profile: dict) -> StageResult:
        stage = "prepare_demo_chunk"
        started = now_iso()

        try:
            sample_path = self.root / "examples" / "prompt_builder_sample_chunk.txt"
            if not sample_path.exists():
                sample_path.parent.mkdir(parents=True, exist_ok=True)
                sample_path.write_text(
                    "일라이가 방 안으로 들어왔다.\n정태의는 그를 바라보았다.\n",
                    encoding="utf-8",
                )

            text = sample_path.read_text(encoding="utf-8")

            data = {
                "file_name": sample_path.name,
                "path": str(sample_path),
                "char_count": len(text),
                "chunk_text": text,
            }

            return StageResult.success(stage, started, "demo chunk ready", data=data)

        except Exception as e:
            return StageResult.failed(stage, started, str(e))

    def stage_build_prompt_package(self, session, profile: dict, chunk_data: dict) -> StageResult:
        stage = "build_prompt_package"
        started = now_iso()

        try:
            builder = PromptBuilder(root=self.root)
            package = builder.build(
                chunk_text=chunk_data["chunk_text"],
                file_name=chunk_data["file_name"],
                chunk_index=1,
                chunk_total=1,
                session_id=session.session_id,
            )

            output_path = self.root / "prompt_packages" / f"{session.session_id}_chunk_000001.json"
            save_json(output_path, package)

            data = {
                "package_path": str(output_path),
                "package_id": package["package_id"],
                "character_matches": len(package["knowledge"]["character_matches"]),
                "glossary_matches": len(package["knowledge"]["glossary_matches"]),
            }

            return StageResult.success(stage, started, "prompt package built", data=data)

        except Exception as e:
            return StageResult.failed(stage, started, str(e))

    def stage_translate_package(self, session, profile: dict, package_path: str) -> StageResult:
        stage = "translate_package"
        started = now_iso()

        try:
            engine = TranslationEngine(root=self.root)
            result = engine.translate_package_file(package_path)

            if result["status"] != "success":
                return StageResult.failed(stage, started, result.get("error", ""), data=result)

            warnings = []
            qa = result.get("qa", {})
            for issue in qa.get("issues", []):
                warnings.append(issue.get("message", str(issue)))

            return StageResult.success(
                stage,
                started,
                "translation finished",
                data=result,
                warnings=warnings,
            )

        except Exception as e:
            return StageResult.failed(stage, started, str(e))
