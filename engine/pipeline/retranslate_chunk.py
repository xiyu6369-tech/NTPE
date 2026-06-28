from __future__ import annotations

import re
import time
from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine
from .chunk_engine import ChunkEngine
from .project_manager import ProjectManager
from .utils import append_log, save_json, now_iso


class RetranslateChunkTool:
    """
    NTPE v0.9.1.2 Retranslate Chunk Tool

    用途：
    - 指定重翻某個 chunk。
    - 不依賴 failed_chunks。
    - 自動把原 chunk 切成較小 subchunks 翻譯。
    - 合併後覆蓋原 translated/*_chunk_xxxxxx_zh.txt。
    - 適合修復已成功但品質不合格的 chunk。
    """

    SUBCHUNK_TARGET = 1200
    SUBCHUNK_MAX = 1600
    MAX_ATTEMPT = 3
    RETRY_DELAYS = [10, 30, 60]

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.log_path = self.root / "logs" / "retranslate_chunk.log"
        self.project_manager = ProjectManager(self.root)

    def run(self, file_name: str, chunk_index: int) -> dict:
        try:
            profile = self.project_manager.load_profile()
            source_path = self.root / profile["paths"]["normalized_dir"] / file_name

            if not source_path.exists():
                return {
                    "status": "failed",
                    "error": f"找不到檔案：{source_path}",
                }

            chunking = profile["chunking"]
            chunk_engine = ChunkEngine(
                chunk_size=chunking.get("chunk_size", 3000),
                max_chunk_size=chunking.get("max_chunk_size", 4200),
            )

            text = source_path.read_text(encoding="utf-8-sig")
            chunks = chunk_engine.split(text)

            if chunk_index < 1 or chunk_index > len(chunks):
                return {
                    "status": "failed",
                    "error": f"chunk_index 超出範圍：{chunk_index} / {len(chunks)}",
                }

            chunk = chunks[chunk_index - 1]
            append_log(self.log_path, f"Retranslate start {file_name} chunk {chunk_index}")

            output_path = self._output_path(file_name, chunk_index)
            backup_path = None

            if output_path.exists():
                backup_path = output_path.with_suffix(".bak.txt")
                backup_path.write_text(output_path.read_text(encoding="utf-8-sig"), encoding="utf-8")

            prompt_builder = PromptBuilder(root=self.root)
            engine = TranslationEngine(root=self.root)

            subchunks = self._split_text(chunk.text)
            print(f"[RETRANSLATE] {file_name} chunk {chunk_index}")
            print(f"Original chars: {len(chunk.text)}")
            print(f"Subchunks: {len(subchunks)}")

            outputs = []

            for sub_index, sub_text in enumerate(subchunks, start=1):
                package = prompt_builder.build(
                    chunk_text=sub_text,
                    file_name=file_name,
                    chunk_index=chunk_index * 1000 + sub_index,
                    chunk_total=len(subchunks),
                    session_id=f"RETRANSLATE_{Path(file_name).stem}_{chunk_index:06d}",
                    context={
                        "previous_summary": "",
                        "previous_chunk_tail": "",
                        "recent_characters": [],
                        "recent_terms": [],
                    },
                )

                # 強化本次重翻規則
                package["rules"]["negative_rules"].extend([
                    "嚴禁濃縮成摘要，必須逐段完整翻譯。",
                    "原文每個敘述資訊都必須保留。",
                    "초인종 必須翻成門鈴，不可翻成電話鈴。",
                    "밥 / 아침 식사 是早餐或飯，不可誤譯成喝酒。",
                ])

                package["prompt"]["user_prompt"] = package["prompt"]["user_prompt"].replace(
                    "【待翻譯內容】",
                    "【重翻要求】\n這是品質修復重翻。請比第一次更完整、更忠實，不可摘要，不可漏段。\n\n【待翻譯內容】"
                )

                package_path = self.root / "prompt_packages" / f"{Path(file_name).stem}_chunk_{chunk_index:06d}_retranslate_sub_{sub_index:03d}.json"
                save_json(package_path, package)

                result = self._translate(engine, package, package_path, sub_index)
                if result["status"] != "success":
                    return {
                        "status": "failed",
                        "file": file_name,
                        "chunk": chunk_index,
                        "sub_index": sub_index,
                        "error": result.get("error", ""),
                        "backup_path": str(backup_path) if backup_path else "",
                    }

                outputs.append(Path(result["output_path"]))

            merged = self._merge(output_path, outputs)

            append_log(self.log_path, f"Retranslate done {file_name} chunk {chunk_index} -> {merged}")

            return {
                "status": "success",
                "file": file_name,
                "chunk": chunk_index,
                "output_path": str(merged),
                "backup_path": str(backup_path) if backup_path else "",
                "subchunk_count": len(subchunks),
            }

        except Exception as e:
            append_log(self.log_path, f"Retranslate fatal error: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def _translate(self, engine, package: dict, package_path: Path, sub_index: int) -> dict:
        last = {}

        for attempt in range(1, self.MAX_ATTEMPT + 1):
            print(f"  sub {sub_index} attempt {attempt}/{self.MAX_ATTEMPT}")
            result = engine.translate_package(package, package_path=package_path)
            result["attempts"] = attempt

            if result.get("status") == "success":
                return result

            last = result
            if attempt < self.MAX_ATTEMPT:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                print(f"  retry after {delay}s: {result.get('error', '')[:160]}")
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

            if current and len(candidate) > self.SUBCHUNK_TARGET:
                parts.append(current.strip() + "\n")
                current = para
            else:
                current = candidate

        if current:
            parts.append(current.strip() + "\n")

        return [p for p in parts if p.strip()]

    def _split_long_paragraph(self, para: str) -> list[str]:
        # 韓文句末標點 + 常見中文英文標點
        sentences = re.split(r"(?<=[。！？!?\.])\s*", para)
        parts = []
        current = ""

        for s in sentences:
            if not s:
                continue

            candidate = current + s
            if current and len(candidate) > self.SUBCHUNK_TARGET:
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

    def _merge(self, output_path: Path, sub_outputs: list[Path]) -> Path:
        with output_path.open("w", encoding="utf-8", newline="\n") as out:
            for p in sorted(sub_outputs, key=lambda x: x.name):
                text = p.read_text(encoding="utf-8-sig").strip()
                if text:
                    out.write(text)
                    out.write("\n\n")
        return output_path

    def _output_path(self, file_name: str, chunk_index: int) -> Path:
        stem = Path(file_name).stem
        return self.root / "translated" / f"{stem}_chunk_{chunk_index:06d}_zh.txt"
