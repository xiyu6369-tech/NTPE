from __future__ import annotations

import time
from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine

from .project_manager import ProjectManager
from .session import PipelineSession
from .chunk_engine import ChunkEngine
from .merger import ChunkMerger
from .utils import append_log, now_iso, save_json, load_json


class RecoveryPipeline:
    """
    NTPE v0.9.1.1 Transactional Recovery Patch

    修正 v0.9.1：
    - 失敗 chunk 不再等整輪結束才寫入。
    - 每個 chunk 失敗時立即寫入 failed_chunks/<file_stem>/chunk000000.json。
    - 每個 chunk 結束立即更新 session。
    - 中途 Ctrl+C / 關機 / Timeout 不會遺失已知失敗資訊。
    - 重新執行仍會跳過 translated/ 已完成 chunk。
    """

    RETRY_DELAYS = [10, 30, 60]
    MAX_ATTEMPT = 3

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.project_manager = ProjectManager(self.root)
        self.log_path = self.root / "logs" / "recovery_pipeline.log"
        self.failed_dir = self.root / "failed_chunks"
        self.failed_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict:
        started_at = now_iso()
        done_count = 0
        skipped_count = 0
        failed_count = 0
        chunk_count = 0
        final_outputs: list[str] = []

        try:
            append_log(self.log_path, "Transactional Recovery Pipeline started")

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

            print(f"[NTPE v0.9.1.1] 找到 {len(files)} 個 normalized TXT")
            append_log(self.log_path, f"Files found: {len(files)}")

            for file_index, file_path in enumerate(files, start=1):
                session.set_stage(f"file:{file_path.name}")
                text = file_path.read_text(encoding="utf-8-sig")
                chunks = chunk_engine.split(text)
                chunk_count += len(chunks)

                print("")
                print(f"[File {file_index}/{len(files)}] {file_path.name}")
                print(f"Chunks: {len(chunks)}")

                file_chunk_outputs: list[Path] = []
                file_record = {
                    "file": file_path.name,
                    "chunk_count": len(chunks),
                    "chunks": [],
                    "status": "running",
                    "started_at": now_iso(),
                }

                self._save_file_progress(session, file_record)

                for chunk in chunks:
                    output_path = self._output_path(file_path, chunk.index)
                    cache_path = self._cache_path(file_path, chunk.index)

                    if output_path.exists() and output_path.stat().st_size > 0:
                        skipped_count += 1
                        file_chunk_outputs.append(output_path)
                        msg = f"[SKIP] {file_path.name} chunk {chunk.index}/{len(chunks)} 已存在"
                        print(msg)
                        append_log(self.log_path, msg)

                        chunk_record = {
                            "chunk_index": chunk.index,
                            "status": "skipped_existing",
                            "output_path": str(output_path),
                            "cache_path": str(cache_path),
                            "updated_at": now_iso(),
                        }
                        file_record["chunks"].append(chunk_record)
                        self._save_file_progress(session, file_record)
                        continue

                    print(f"[RUN ] {file_path.name} chunk {chunk.index}/{len(chunks)} chars={chunk.char_count}")
                    append_log(self.log_path, f"RUN {file_path.name} chunk {chunk.index}/{len(chunks)}")

                    package = prompt_builder.build(
                        chunk_text=chunk.text,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        chunk_total=len(chunks),
                        session_id=session.session_id,
                    )

                    package_path = self.root / "prompt_packages" / f"{file_path.stem}_chunk_{chunk.index:06d}.json"
                    save_json(package_path, package)

                    self._write_chunk_state(
                        file_path=file_path,
                        chunk_index=chunk.index,
                        state={
                            "status": "package_created",
                            "file": file_path.name,
                            "chunk_index": chunk.index,
                            "char_count": chunk.char_count,
                            "package_path": str(package_path),
                            "updated_at": now_iso(),
                        },
                    )

                    result = self._translate_with_retry(
                        translation_engine=translation_engine,
                        package=package,
                        package_path=package_path,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                    )

                    chunk_record = {
                        "chunk_index": chunk.index,
                        "char_count": chunk.char_count,
                        "package_path": str(package_path),
                        "translation_status": result.get("status"),
                        "output_path": result.get("output_path", ""),
                        "cache_path": result.get("cache_path", ""),
                        "attempts": result.get("attempts", 1),
                        "error": result.get("error", ""),
                        "qa": result.get("qa", {}),
                        "updated_at": now_iso(),
                    }

                    file_record["chunks"].append(chunk_record)
                    self._save_file_progress(session, file_record)

                    if result.get("status") == "success":
                        done_count += 1
                        file_chunk_outputs.append(Path(result["output_path"]))

                        self._write_chunk_state(
                            file_path=file_path,
                            chunk_index=chunk.index,
                            state={
                                "status": "done",
                                "file": file_path.name,
                                "chunk_index": chunk.index,
                                "char_count": chunk.char_count,
                                "attempts": result.get("attempts", 1),
                                "package_path": str(package_path),
                                "output_path": result.get("output_path", ""),
                                "cache_path": result.get("cache_path", ""),
                                "qa": result.get("qa", {}),
                                "updated_at": now_iso(),
                            },
                        )

                        print(f"[DONE] chunk {chunk.index}/{len(chunks)} attempts={result.get('attempts', 1)}")

                    else:
                        failed_count += 1

                        failed_record = {
                            "status": "failed",
                            "file": file_path.name,
                            "chunk_index": chunk.index,
                            "char_count": chunk.char_count,
                            "attempts": result.get("attempts", self.MAX_ATTEMPT),
                            "package_path": str(package_path),
                            "error": result.get("error", ""),
                            "failed_at": now_iso(),
                            "recovered": False,
                        }

                        failed_path = self._write_failed_chunk(file_path, chunk.index, failed_record)

                        self._write_chunk_state(
                            file_path=file_path,
                            chunk_index=chunk.index,
                            state={**failed_record, "failed_path": str(failed_path)},
                        )

                        print(f"[FAIL] chunk {chunk.index}/{len(chunks)} saved={failed_path}")
                        append_log(self.log_path, f"FAIL SAVED {file_path.name} chunk {chunk.index}: {failed_path}")

                        # v0.9.1.1：失敗已即時保存，繼續下一個 chunk
                        continue

                if file_chunk_outputs:
                    final_path = merger.merge_file(file_path.stem, file_chunk_outputs)
                    final_outputs.append(str(final_path))
                    file_record["final_output"] = str(final_path)
                    append_log(self.log_path, f"MERGED {file_path.name} -> {final_path}")

                file_record["status"] = "success_with_failed_chunks" if any(
                    c.get("translation_status") == "failed" for c in file_record["chunks"]
                ) else "success"
                file_record["ended_at"] = now_iso()

                self._save_file_progress(session, file_record)
                session.data.setdefault("files", []).append(file_record)
                session.save()

            status = "success" if failed_count == 0 else "partial_success"
            session.set_status(status)
            append_log(self.log_path, f"Transactional Recovery Pipeline completed status={status}")

            return {
                "status": status,
                "session_id": session.session_id,
                "started_at": started_at,
                "ended_at": now_iso(),
                "file_count": len(files),
                "chunk_count": chunk_count,
                "done_count": done_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "failed_dir": str(self.failed_dir),
                "final_outputs": final_outputs,
                "session_path": str(session.path),
            }

        except KeyboardInterrupt:
            append_log(self.log_path, "Pipeline interrupted by user")
            try:
                session.set_status("interrupted")
            except Exception:
                pass
            return {
                "status": "interrupted",
                "started_at": started_at,
                "ended_at": now_iso(),
                "chunk_count": chunk_count,
                "done_count": done_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "failed_dir": str(self.failed_dir),
                "final_outputs": final_outputs,
                "error": "User interrupted",
            }

        except Exception as e:
            append_log(self.log_path, f"Transactional Recovery Pipeline fatal error: {e}")
            return {
                "status": "failed",
                "started_at": started_at,
                "ended_at": now_iso(),
                "chunk_count": chunk_count,
                "done_count": done_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
                "failed_dir": str(self.failed_dir),
                "final_outputs": final_outputs,
                "error": str(e),
            }

    def _translate_with_retry(self, *, translation_engine, package: dict, package_path: Path, file_name: str, chunk_index: int) -> dict:
        last_result = {}

        for attempt in range(1, self.MAX_ATTEMPT + 1):
            try:
                print(f"       attempt {attempt}/{self.MAX_ATTEMPT}")
                append_log(self.log_path, f"attempt {attempt}/{self.MAX_ATTEMPT} {file_name} chunk {chunk_index}")

                result = translation_engine.translate_package(package, package_path=package_path)
                result["attempts"] = attempt

                if result.get("status") == "success":
                    return result

                last_result = result
                error = result.get("error", "")

            except Exception as e:
                error = str(e)
                last_result = {
                    "status": "failed",
                    "error": error,
                    "attempts": attempt,
                }

            # 每次失敗嘗試都先寫暫存狀態
            self._write_attempt_failure(
                file_name=file_name,
                chunk_index=chunk_index,
                attempt=attempt,
                error=error,
                package_path=package_path,
            )

            if attempt < self.MAX_ATTEMPT:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                print(f"       retry after {delay}s: {error[:160]}")
                append_log(self.log_path, f"retry after {delay}s: {error[:300]}")
                time.sleep(delay)

        last_result["status"] = "failed"
        last_result["attempts"] = self.MAX_ATTEMPT
        return last_result

    def _write_attempt_failure(self, *, file_name: str, chunk_index: int, attempt: int, error: str, package_path: Path) -> None:
        file_stem = Path(file_name).stem
        path = self.failed_dir / file_stem / f"chunk{chunk_index:06d}_attempt{attempt}.json"
        save_json(path, {
            "status": "attempt_failed",
            "file": file_name,
            "chunk_index": chunk_index,
            "attempt": attempt,
            "error": error,
            "package_path": str(package_path),
            "created_at": now_iso(),
        })

    def _write_failed_chunk(self, file_path: Path, chunk_index: int, record: dict) -> Path:
        file_stem = file_path.stem
        path = self.failed_dir / file_stem / f"chunk{chunk_index:06d}.json"
        save_json(path, record)
        return path

    def _write_chunk_state(self, file_path: Path, chunk_index: int, state: dict) -> Path:
        file_stem = file_path.stem
        path = self.root / "sessions" / "chunk_state" / file_stem / f"chunk{chunk_index:06d}.json"
        save_json(path, state)
        return path

    def _save_file_progress(self, session: PipelineSession, file_record: dict) -> None:
        session.data["current_file_record"] = file_record
        session.data["updated_at"] = now_iso()
        session.save()

    def _output_path(self, file_path: Path, chunk_index: int) -> Path:
        return self.root / "translated" / f"{file_path.stem}_chunk_{chunk_index:06d}_zh.txt"

    def _cache_path(self, file_path: Path, chunk_index: int) -> Path:
        return self.root / "translation_cache" / f"{file_path.stem}_chunk_{chunk_index:06d}_result.json"
