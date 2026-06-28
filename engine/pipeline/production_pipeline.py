from __future__ import annotations

from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine

from .project_manager import ProjectManager
from .session import PipelineSession
from .chunk_engine import ChunkEngine
from .merger import ChunkMerger
from .utils import append_log, now_iso, save_json


class ProductionPipeline:
    """
    NTPE v0.9.0 Production Pipeline

    目標：
    - 讀取 profiles/passion_profile.json
    - 掃描 output/*_normalized.txt
    - 依段落切 chunk
    - 每個 chunk 產生 Prompt Package
    - 呼叫 Translation Engine 翻譯
    - 保存 Session
    - 合併每本 final_output/*_zh.txt

    注意：
    - v0.9.0 先做基本生產流程。
    - Resume / QA Retry 在 v0.9.1 / v0.9.2 強化。
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.project_manager = ProjectManager(self.root)
        self.log_path = self.root / "logs" / "production_pipeline.log"

    def run(self) -> dict:
        started_at = now_iso()
        translated_count = 0
        chunk_count = 0
        final_outputs: list[str] = []

        try:
            append_log(self.log_path, "Production Pipeline started")

            profile = self.project_manager.load_profile()
            session = self.project_manager.create_session(profile)
            session.set_status("running")
            session.set_stage("scan_files")

            files = self.project_manager.scan_normalized_files(profile)
            if not files:
                session.set_status("failed")
                return {
                    "status": "failed",
                    "session_id": session.session_id,
                    "error": "找不到 normalized TXT。請先執行 Document Normalizer。",
                }

            chunking = profile["chunking"]
            chunk_engine = ChunkEngine(
                chunk_size=chunking.get("chunk_size", 3000),
                max_chunk_size=chunking.get("max_chunk_size", 4200),
            )

            prompt_builder = PromptBuilder(root=self.root)
            translation_engine = TranslationEngine(root=self.root)
            merger = ChunkMerger(root=self.root)

            append_log(self.log_path, f"Files found: {len(files)}")

            for file_index, file_path in enumerate(files, start=1):
                session.set_stage(f"file:{file_path.name}")
                append_log(self.log_path, f"Processing file {file_index}/{len(files)}: {file_path.name}")

                text = file_path.read_text(encoding="utf-8-sig")
                chunks = chunk_engine.split(text)
                chunk_count += len(chunks)

                file_chunk_outputs: list[Path] = []

                file_record = {
                    "file": file_path.name,
                    "chunk_count": len(chunks),
                    "chunks": [],
                    "status": "running",
                }

                for chunk in chunks:
                    append_log(self.log_path, f"{file_path.name} chunk {chunk.index}/{len(chunks)}")

                    package = prompt_builder.build(
                        chunk_text=chunk.text,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        chunk_total=len(chunks),
                        session_id=session.session_id,
                    )

                    package_path = self.root / "prompt_packages" / f"{file_path.stem}_chunk_{chunk.index:06d}.json"
                    save_json(package_path, package)

                    result = translation_engine.translate_package(package, package_path=package_path)

                    chunk_record = {
                        "chunk_index": chunk.index,
                        "char_count": chunk.char_count,
                        "package_path": str(package_path),
                        "translation_status": result.get("status"),
                        "output_path": result.get("output_path", ""),
                        "qa": result.get("qa", {}),
                    }

                    file_record["chunks"].append(chunk_record)
                    session.data["updated_at"] = now_iso()
                    session.save()

                    if result.get("status") != "success":
                        file_record["status"] = "failed"
                        session.data.setdefault("files", []).append(file_record)
                        session.set_status("failed")
                        return {
                            "status": "failed",
                            "session_id": session.session_id,
                            "file": file_path.name,
                            "chunk": chunk.index,
                            "error": result.get("error", "translation failed"),
                            "file_count": len(files),
                            "chunk_count": chunk_count,
                            "translated_count": translated_count,
                            "final_outputs": final_outputs,
                        }

                    translated_count += 1
                    if result.get("output_path"):
                        file_chunk_outputs.append(Path(result["output_path"]))

                final_path = merger.merge_file(file_path.stem, file_chunk_outputs)
                final_outputs.append(str(final_path))

                file_record["status"] = "success"
                file_record["final_output"] = str(final_path)
                session.data.setdefault("files", []).append(file_record)
                session.save()

                append_log(self.log_path, f"File completed: {file_path.name} -> {final_path}")

            session.set_status("success")
            append_log(self.log_path, "Production Pipeline completed")

            return {
                "status": "success",
                "session_id": session.session_id,
                "started_at": started_at,
                "ended_at": now_iso(),
                "file_count": len(files),
                "chunk_count": chunk_count,
                "translated_count": translated_count,
                "final_outputs": final_outputs,
                "session_path": str(session.path),
            }

        except Exception as e:
            append_log(self.log_path, f"Production Pipeline fatal error: {e}")
            return {
                "status": "failed",
                "started_at": started_at,
                "ended_at": now_iso(),
                "file_count": 0,
                "chunk_count": chunk_count,
                "translated_count": translated_count,
                "final_outputs": final_outputs,
                "error": str(e),
            }
