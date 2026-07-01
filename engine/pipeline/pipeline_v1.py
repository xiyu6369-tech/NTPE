from __future__ import annotations

import json
import time
from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine
from core.quality.semantic_qa import SemanticQA
from core.quality.semantic_repair import SemanticRepair
from core.quality.coverage_checker import CoverageChecker
from core.context.memory_engine import ContextMemoryEngine
from core.runtime import RuntimeManager
try:
    from core.expansion.style_expansion_engine import StyleExpansionEngine
except Exception:
    StyleExpansionEngine = None

from .project_manager import ProjectManager
from .chunk_engine import ChunkEngine
from .merger import ChunkMerger
from .utils import append_log, save_json, now_iso


class ProductionPipelineV1:
    QUALITY_TARGET = 95
    RETRY_DELAYS = [10, 30, 60]
    MAX_TRANSLATE_ATTEMPT = 3

    def __init__(self, root: str | Path):
        self.root = Path(root)
        
        # Foundation-02 Runtime Manager
        self.runtime = RuntimeManager(self.root)

        self.project_manager = ProjectManager(self.root)
        self.log_path = self.runtime.log_path("pipeline_v1.log")

        self.report_dir = self.runtime.reports_dir

        self.state_dir = self.runtime.session_path("pipeline_v1")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.live_report_path = self.runtime.report_path(
            "pipeline_v1_live_report.json"
        )

        self.quality_failed_path = self.runtime.report_path(
            "quality_failed_chunks.json"
        )

    def run(self) -> dict:
        started_at = now_iso()
        counters = {
            "file_count": 0,
            "chunk_count": 0,
            "translated_count": 0,
            "skipped_count": 0,
            "semantic_repaired_count": 0,
            "style_expanded_count": 0,
            "quality_failed_count": 0,
            "missing_file_count": 0,
            "failed_count": 0,
        }

        report = {
            "status": "running",
            "started_at": started_at,
            "updated_at": started_at,
            **counters,
            "final_outputs": [],
            "missing_files": [],
            "failed_chunks": [],
            "quality_failed_chunks": [],
            "files": [],
        }

        try:
            append_log(self.log_path, "NTPE v1.0.1 Production Pipeline started")
            profile = self.project_manager.load_profile()
            files = self.project_manager.scan_normalized_files(profile)
            counters["file_count"] = len(files)
            self._update_report(report, counters)

            if not files:
                report["status"] = "failed"
                report["error"] = "找不到 normalized TXT。請先執行 Document Normalizer。"
                self._save_live_report(report)
                return {**report, "report_path": str(self.live_report_path)}

            chunk_engine = ChunkEngine(
                chunk_size=profile["chunking"].get("chunk_size", 3000),
                max_chunk_size=profile["chunking"].get("max_chunk_size", 4200),
            )

            prompt_builder = PromptBuilder(root=self.root)
            translation_engine = TranslationEngine(root=self.root)
            semantic_qa = SemanticQA(root=self.root)
            semantic_repair = SemanticRepair(root=self.root)
            coverage_checker = CoverageChecker(root=self.root)
            context_memory = ContextMemoryEngine(root=self.root)
            style_expansion = StyleExpansionEngine(root=self.root) if StyleExpansionEngine else None
            merger = ChunkMerger(root=self.root)

            print(f"[NTPE v1.0.1] 找到 {len(files)} 個 normalized TXT")

            for file_index, file_path in enumerate(files, start=1):
                print("")
                print(f"[File {file_index}/{len(files)}] {file_path.name}")
                append_log(self.log_path, f"FILE START {file_path.name}")

                if not file_path.exists():
                    counters["missing_file_count"] += 1
                    report["missing_files"].append({
                        "file": file_path.name,
                        "path": str(file_path),
                        "detected_at": now_iso(),
                    })
                    self._update_report(report, counters)
                    print(f"  MISSING normalized file, skip: {file_path}")
                    continue

                source_text = file_path.read_text(encoding="utf-8-sig")
                chunks = chunk_engine.split(source_text)
                counters["chunk_count"] += len(chunks)

                file_chunk_outputs = []
                file_report = {
                    "file": file_path.name,
                    "status": "running",
                    "chunk_count": len(chunks),
                    "chunks": [],
                    "final_output": "",
                    "started_at": now_iso(),
                }
                report["files"].append(file_report)
                self._update_report(report, counters)

                print(f"Chunks: {len(chunks)}")

                for chunk in chunks:
                    print(f"[Chunk {chunk.index}/{len(chunks)}] chars={chunk.char_count}")
                    state_path = self._state_path(file_path, chunk.index)
                    output_path = self._output_path(file_path, chunk.index)

                    if output_path.exists() and output_path.stat().st_size > 0:
                        counters["skipped_count"] += 1
                        file_chunk_outputs.append(output_path)
                        state = self._load_state(state_path) or {}
                        file_report["chunks"].append({
                            "chunk_index": chunk.index,
                            "status": "skipped_existing",
                            "output_path": str(output_path),
                            "state_path": str(state_path),
                            "quality": state.get("quality", {}),
                        })
                        self._update_report(report, counters)
                        print("  SKIP existing")
                        continue

                    package = prompt_builder.build(
                        chunk_text=chunk.text,
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        chunk_total=len(chunks),
                        session_id=f"PIPELINE_V1_{file_path.stem}",
                    )
                    package_path = self.runtime.prompt_package_path(
                        f"{file_path.stem}_chunk_{chunk.index:06d}_v1.json"
                    ) 

                    base_state = {
                        "file": file_path.name,
                        "chunk_index": chunk.index,
                        "status": "package_created",
                        "package_path": str(package_path),
                        "updated_at": now_iso(),
                    }
                    save_json(state_path, base_state)

                    result = self._translate_with_retry(
                        translation_engine=translation_engine,
                        package=package,
                        package_path=package_path,
                        chunk_label=f"{file_path.name} chunk {chunk.index}",
                    )

                    if result.get("status") != "success":
                        counters["failed_count"] += 1
                        failed = {
                            "file": file_path.name,
                            "chunk_index": chunk.index,
                            "error": result.get("error", ""),
                            "package_path": str(package_path),
                            "failed_at": now_iso(),
                        }
                        report["failed_chunks"].append(failed)
                        save_json(state_path, {**base_state, "status": "failed_translate", "error": failed["error"], "updated_at": now_iso()})
                        self._update_report(report, counters)
                        print(f"  FAIL translate: {failed['error'][:160]}")
                        continue

                    counters["translated_count"] += 1
                    translation_path = Path(result["output_path"])
                    translation_text = translation_path.read_text(encoding="utf-8-sig")

                    repaired = False
                    semantic_before = semantic_qa.check(chunk.text, translation_text)
                    if semantic_before.get("issue_count", 0) > 0:
                        repair_result = semantic_repair.repair(chunk.text, translation_text)
                        if repair_result.get("changed"):
                            translation_text = repair_result["translation"]
                            translation_path.write_text(translation_text, encoding="utf-8")
                            counters["semantic_repaired_count"] += 1
                            repaired = True
                            print(f"  semantic repair applied={len(repair_result.get('applied', []))}")

                    coverage = coverage_checker.check(chunk.text, translation_text)
                    expanded = False
                    expansion_result = None

                    if style_expansion and not coverage.get("passed", False):
                        print(f"  coverage not pass score={coverage.get('score')} → expansion")
                        try:
                            expansion_result = style_expansion.expand(
                                source_text=chunk.text,
                                translation_text=translation_text,
                                file_name=file_path.name,
                                chunk_index=chunk.index,
                                model=package["model_profile"]["model"],
                                max_output_tokens=1600,
                            )
                            if expansion_result.get("status") == "expanded":
                                translation_text = expansion_result["translation"]
                                translation_path.write_text(translation_text, encoding="utf-8")
                                counters["style_expanded_count"] += 1
                                expanded = True

                                repair_result = semantic_repair.repair(chunk.text, translation_text)
                                if repair_result.get("changed"):
                                    translation_text = repair_result["translation"]
                                    translation_path.write_text(translation_text, encoding="utf-8")
                                    counters["semantic_repaired_count"] += 1
                                    repaired = True

                                coverage = coverage_checker.check(chunk.text, translation_text)
                        except Exception as e:
                            append_log(self.log_path, f"EXPANSION ERROR {file_path.name} chunk {chunk.index}: {e}")

                    semantic_after = semantic_qa.check(chunk.text, translation_text)
                    quality = self._score_quality(coverage, semantic_after)

                    final_status = "done" if quality["passed"] else "needs_review"
                    if final_status == "needs_review":
                        counters["quality_failed_count"] += 1
                        quality_failed = {
                            "file": file_path.name,
                            "chunk_index": chunk.index,
                            "output_path": str(translation_path),
                            "quality": quality,
                            "coverage": coverage,
                            "semantic_issue_count": semantic_after.get("issue_count", 0),
                            "state_path": str(state_path),
                            "recorded_at": now_iso(),
                        }
                        report["quality_failed_chunks"].append(quality_failed)
                        self._save_quality_failed(report["quality_failed_chunks"])

                    chunk_state = {
                        **base_state,
                        "status": final_status,
                        "output_path": str(translation_path),
                        "semantic_repaired": repaired,
                        "style_expanded": expanded,
                        "semantic": semantic_after,
                        "coverage": coverage,
                        "quality": quality,
                        "updated_at": now_iso(),
                    }
                    if expansion_result:
                        chunk_state["expansion_status"] = expansion_result.get("status")
                        chunk_state["expansion_tasks"] = expansion_result.get("plan", {}).get("task_count", 0)

                    save_json(state_path, chunk_state)

                    context_memory.update_after_chunk(
                        file_name=file_path.name,
                        chunk_index=chunk.index,
                        source_text=chunk.text,
                        translation_text=translation_text,
                    )
                    file_chunk_outputs.append(translation_path)
                    file_report["chunks"].append({
                        "chunk_index": chunk.index,
                        "status": final_status,
                        "output_path": str(translation_path),
                        "state_path": str(state_path),
                        "quality": quality,
                        "coverage": coverage,
                        "semantic_issue_count": semantic_after.get("issue_count", 0),
                        "semantic_repaired": repaired,
                        "style_expanded": expanded,
                    })

                    self._update_report(report, counters)
                    print(f"  {final_status.upper()} quality={quality['overall']} coverage={coverage.get('score')} semantic_issues={semantic_after.get('issue_count', 0)}")

                if file_chunk_outputs:
                    final_path = merger.merge_file(file_path.stem, file_chunk_outputs)
                    file_report["final_output"] = str(final_path)
                    report["final_outputs"].append(str(final_path))
                    print(f"MERGED -> {final_path}")

                file_report["status"] = "done"
                file_report["ended_at"] = now_iso()
                self._update_report(report, counters)
                append_log(self.log_path, f"FILE DONE {file_path.name}")

            status = "success" if counters["failed_count"] == 0 and counters["missing_file_count"] == 0 else "partial_success"
            report["status"] = status
            report["ended_at"] = now_iso()
            self._update_report(report, counters)

            final_report_path = self.report_dir / f"pipeline_v1_report_{self._stamp()}.json"
            save_json(final_report_path, report)
            append_log(self.log_path, f"NTPE v1.0.1 Production Pipeline finished status={status}")

            return {"status": status, "report_path": str(final_report_path), **counters}

        except KeyboardInterrupt:
            report["status"] = "interrupted"
            report["ended_at"] = now_iso()
            self._update_report(report, counters)
            append_log(self.log_path, "PIPELINE V1 interrupted by user")
            return {"status": "interrupted", "report_path": str(self.live_report_path), **counters, "error": "User interrupted"}

        except Exception as e:
            report["status"] = "failed"
            report["error"] = str(e)
            report["ended_at"] = now_iso()
            self._update_report(report, counters)
            append_log(self.log_path, f"PIPELINE V1 FATAL ERROR: {e}")
            return {"status": "failed", "report_path": str(self.live_report_path), **counters, "error": str(e)}

    def _translate_with_retry(self, *, translation_engine, package: dict, package_path: Path, chunk_label: str) -> dict:
        last = {}
        for attempt in range(1, self.MAX_TRANSLATE_ATTEMPT + 1):
            print(f"  translate attempt {attempt}/{self.MAX_TRANSLATE_ATTEMPT}")
            result = translation_engine.translate_package(package, package_path=package_path)
            result["attempts"] = attempt
            if result.get("status") == "success":
                return result
            last = result
            if attempt < self.MAX_TRANSLATE_ATTEMPT:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                append_log(self.log_path, f"TRANSLATE RETRY {chunk_label} after {delay}s: {result.get('error','')[:300]}")
                time.sleep(delay)
        return last

    def _score_quality(self, coverage: dict, semantic: dict) -> dict:
        semantic_score = 100 if semantic.get("issue_count", 0) == 0 else max(0, 100 - semantic.get("issue_count", 0) * 15)
        coverage_score = int(coverage.get("score", 0))
        overall = round((semantic_score * 0.4) + (coverage_score * 0.6), 1)
        return {
            "overall": overall,
            "semantic": semantic_score,
            "coverage": coverage_score,
            "passed": overall >= self.QUALITY_TARGET and semantic.get("issue_count", 0) == 0,
        }

    def _update_report(self, report: dict, counters: dict) -> None:
        report.update(counters)
        report["updated_at"] = now_iso()
        self._save_live_report(report)

    def _save_live_report(self, report: dict) -> None:
        save_json(self.live_report_path, report)

    def _save_quality_failed(self, items: list[dict]) -> None:
        save_json(self.quality_failed_path, {
            "updated_at": now_iso(),
            "count": len(items),
            "quality_failed_chunks": items,
        })

    def _output_path(self, file_path: Path, chunk_index: int) -> Path:
        return self.runtime.translated_path(
            f"{file_path.stem}_chunk_{chunk_index:06d}_zh.txt"
        )

    def _state_path(self, file_path: Path, chunk_index: int) -> Path:
        return self.state_dir / file_path.stem / f"chunk{chunk_index:06d}.json"

    def _load_state(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None

    def _stamp(self) -> str:
        return now_iso().replace(":", "").replace("-", "").replace("T", "_")
