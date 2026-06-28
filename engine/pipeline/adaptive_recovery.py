from __future__ import annotations

import re
import time
from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine
from .utils import append_log, load_json, save_json, now_iso


class AdaptiveRecoveryPipeline:
    SUBCHUNK_TARGET = 1400
    SUBCHUNK_MAX = 1800
    MAX_ATTEMPT = 3
    RETRY_DELAYS = [10, 30, 60]

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.failed_dir = self.root / "failed_chunks"
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.root / "logs" / "adaptive_recovery.log"
        stamp = now_iso().replace(":", "").replace("-", "").replace("T", "_")
        self.report_path = self.failed_dir / f"adaptive_recovery_report_{stamp}.json"

    def run(self) -> dict:
        recovered = []
        failed = []

        try:
            failed_files = self._list_failed_files()
            if not failed_files:
                return {
                    "status": "success",
                    "recovered_count": 0,
                    "failed_count": 0,
                    "report_path": "",
                    "message": "沒有 failed_chunks 記錄可恢復。",
                }

            append_log(self.log_path, f"Adaptive recovery started. failed files={len(failed_files)}")
            print(f"[v0.9.2] 找到 {len(failed_files)} 個 failed_chunks 記錄")

            prompt_builder = PromptBuilder(root=self.root)
            engine = TranslationEngine(root=self.root)

            for failed_file in failed_files:
                data = load_json(failed_file)
                records = data.get("failed_chunks", [])
                print(f"[Failed File] {failed_file.name} chunks={len(records)}")

                for record in records:
                    result = self._recover_one(record, prompt_builder, engine)
                    if result["status"] == "success":
                        recovered.append(result)
                    else:
                        failed.append(result)

            report = {
                "generated_at": now_iso(),
                "recovered_count": len(recovered),
                "failed_count": len(failed),
                "recovered": recovered,
                "failed": failed,
            }
            save_json(self.report_path, report)

            status = "success" if not failed else "partial_success"
            append_log(self.log_path, f"Adaptive recovery finished status={status} recovered={len(recovered)} failed={len(failed)}")

            return {
                "status": status,
                "recovered_count": len(recovered),
                "failed_count": len(failed),
                "report_path": str(self.report_path),
            }

        except Exception as e:
            append_log(self.log_path, f"Adaptive recovery fatal error: {e}")
            return {
                "status": "failed",
                "recovered_count": len(recovered),
                "failed_count": len(failed),
                "error": str(e),
                "report_path": str(self.report_path),
            }

    def _list_failed_files(self) -> list[Path]:
        return sorted(self.failed_dir.glob("*_failed_chunks.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    def _recover_one(self, record: dict, prompt_builder: PromptBuilder, engine: TranslationEngine) -> dict:
        file_name = record["file"]
        chunk_index = int(record["chunk_index"])
        package_path = Path(record["package_path"])

        print(f"[RECOVER] {file_name} chunk {chunk_index}")

        if not package_path.exists():
            msg = f"package 不存在：{package_path}"
            print(f"[FAIL] {msg}")
            return {"status": "failed", "file": file_name, "chunk_index": chunk_index, "error": msg}

        final_output = self._original_output_path(file_name, chunk_index)
        if final_output.exists() and final_output.stat().st_size > 0:
            print(f"[SKIP] 已存在：{final_output.name}")
            return {"status": "success", "file": file_name, "chunk_index": chunk_index, "mode": "skipped_existing", "output_path": str(final_output)}

        original_package = load_json(package_path)
        original_text = original_package["source"]["chunk_text"]
        subchunks = self._split_text(original_text)
        print(f"          split into {len(subchunks)} subchunks")

        sub_outputs = []
        for sub_index, sub_text in enumerate(subchunks, start=1):
            sub_package = prompt_builder.build(
                chunk_text=sub_text,
                file_name=file_name,
                chunk_index=self._subchunk_index(chunk_index, sub_index),
                chunk_total=len(subchunks),
                session_id=f"ADAPTIVE_{Path(file_name).stem}_{chunk_index:06d}",
            )

            sub_package_path = self.root / "prompt_packages" / f"{Path(file_name).stem}_chunk_{chunk_index:06d}_sub_{sub_index:03d}.json"
            save_json(sub_package_path, sub_package)

            result = self._translate_subchunk(engine, sub_package, sub_package_path, file_name, chunk_index, sub_index)
            if result["status"] != "success":
                return {
                    "status": "failed",
                    "file": file_name,
                    "chunk_index": chunk_index,
                    "sub_index": sub_index,
                    "error": result.get("error", ""),
                }

            sub_outputs.append(Path(result["output_path"]))

        merged_path = self._merge_sub_outputs(file_name, chunk_index, sub_outputs)
        print(f"[DONE] recovered {file_name} chunk {chunk_index} -> {merged_path.name}")

        return {
            "status": "success",
            "file": file_name,
            "chunk_index": chunk_index,
            "subchunk_count": len(subchunks),
            "output_path": str(merged_path),
        }

    def _translate_subchunk(self, engine: TranslationEngine, package: dict, package_path: Path, file_name: str, chunk_index: int, sub_index: int) -> dict:
        last = {}
        for attempt in range(1, self.MAX_ATTEMPT + 1):
            print(f"          sub {sub_index} attempt {attempt}/{self.MAX_ATTEMPT}")
            append_log(self.log_path, f"{file_name} chunk {chunk_index} sub {sub_index} attempt {attempt}")

            result = engine.translate_package(package, package_path=package_path)
            result["attempts"] = attempt

            if result.get("status") == "success":
                return result

            last = result
            error = result.get("error", "")
            if attempt < self.MAX_ATTEMPT:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                print(f"          retry after {delay}s: {error[:160]}")
                time.sleep(delay)

        last["status"] = "failed"
        return last

    def _split_text(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        parts = []
        current = ""

        for para in paragraphs:
            if len(para) > self.SUBCHUNK_MAX:
                if current:
                    parts.append(current.strip() + "\n")
                    current = ""
                parts.extend(self._split_long_paragraph(para))
                continue

            candidate = (current + "\n\n" + para).strip() if current else para
            if len(candidate) > self.SUBCHUNK_TARGET and current:
                parts.append(current.strip() + "\n")
                current = para
            else:
                current = candidate

        if current:
            parts.append(current.strip() + "\n")

        return [p for p in parts if p.strip()]

    def _split_long_paragraph(self, para: str) -> list[str]:
        sentences = re.split(r"(?<=[。！？!?\.])\s*", para)
        parts = []
        current = ""

        for s in sentences:
            if not s:
                continue
            candidate = current + s
            if len(candidate) > self.SUBCHUNK_TARGET and current:
                parts.append(current.strip() + "\n")
                current = s
            else:
                current = candidate

        if current:
            parts.append(current.strip() + "\n")

        final = []
        for p in parts:
            if len(p) <= self.SUBCHUNK_MAX:
                final.append(p)
            else:
                for i in range(0, len(p), self.SUBCHUNK_TARGET):
                    final.append(p[i:i + self.SUBCHUNK_TARGET].strip() + "\n")
        return final

    def _merge_sub_outputs(self, file_name: str, chunk_index: int, sub_outputs: list[Path]) -> Path:
        final_path = self._original_output_path(file_name, chunk_index)
        with final_path.open("w", encoding="utf-8", newline="\n") as out:
            for p in sorted(sub_outputs, key=lambda x: x.name):
                text = p.read_text(encoding="utf-8-sig").strip()
                if text:
                    out.write(text)
                    out.write("\n\n")
        return final_path

    def _original_output_path(self, file_name: str, chunk_index: int) -> Path:
        stem = Path(file_name).stem
        return self.root / "translated" / f"{stem}_chunk_{chunk_index:06d}_zh.txt"

    def _subchunk_index(self, chunk_index: int, sub_index: int) -> int:
        return chunk_index * 1000 + sub_index
