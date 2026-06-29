from __future__ import annotations

import re
import time
from pathlib import Path

from core.prompt_builder.prompt_builder import PromptBuilder
from core.translation_engine.translation_engine import TranslationEngine
from core.quality.coverage_checker import CoverageChecker

try:
    from core.quality.structure_engine import DocumentStructureEngine
except Exception:
    DocumentStructureEngine = None

from .chunk_engine import ChunkEngine
from .project_manager import ProjectManager
from .utils import append_log, save_json


class RetranslateChunkTool:
    """
    NTPE TQF-03.2 Best Effort Save + UltraSplit

    修正：
    - TQF-03.1 嚴格 coverage 失敗時完全不寫入，導致標題修正無法落地。
    - 這版會保存 coverage 分數最高的最佳版本，狀態回傳 best_effort。
    - 分段更小，降低摘要化。
    """

    SUBCHUNK_TARGET = 420
    SUBCHUNK_MAX = 650
    MAX_ATTEMPT = 4
    RETRY_DELAYS = [5, 10, 20]
    BEST_EFFORT_MIN_SCORE = 50

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.log_path = self.root / "logs" / "retranslate_chunk.log"
        self.project_manager = ProjectManager(self.root)
        self.coverage_checker = CoverageChecker(root=self.root)
        self.structure_engine = DocumentStructureEngine(self.root) if DocumentStructureEngine else None

    def run(self, file_name: str, chunk_index: int) -> dict:
        try:
            profile = self.project_manager.load_profile()
            source_path = self.root / profile["paths"]["normalized_dir"] / file_name

            if not source_path.exists():
                return {"status": "failed", "error": f"找不到檔案：{source_path}"}

            chunk_engine = ChunkEngine(
                chunk_size=profile["chunking"].get("chunk_size", 3000),
                max_chunk_size=profile["chunking"].get("max_chunk_size", 4200),
            )

            text = source_path.read_text(encoding="utf-8-sig")
            chunks = chunk_engine.split(text)

            if chunk_index < 1 or chunk_index > len(chunks):
                return {"status": "failed", "error": f"chunk_index 超出範圍：{chunk_index} / {len(chunks)}"}

            original_chunk = chunks[chunk_index - 1].text
            structure = self._analyze_structure(original_chunk)
            locked_title = self._get_locked_title(structure)
            body_text = self._remove_title_from_body(original_chunk, structure) if locked_title else original_chunk

            output_path = self._output_path(file_name, chunk_index)
            backup_path = None
            if output_path.exists() and output_path.stat().st_size > 0:
                backup_path = output_path.with_suffix(".bak.txt")
                backup_path.write_text(output_path.read_text(encoding="utf-8-sig"), encoding="utf-8")

            prompt_builder = PromptBuilder(root=self.root)
            engine = TranslationEngine(root=self.root)

            paragraphs = self._split_paragraphs(body_text)
            groups = self._group_paragraphs(paragraphs)

            print(f"[TQF-03.2 RETRANSLATE] {file_name} chunk {chunk_index}")
            print(f"Original chars: {len(original_chunk)}")
            print(f"Locked title: {locked_title or '(none)'}")
            print(f"Body paragraphs: {len(paragraphs)}")
            print(f"Subgroups: {len(groups)}")

            outputs = []
            warnings = []

            for sub_index, group in enumerate(groups, start=1):
                marked_source = self._mark_paragraphs(group)
                package = prompt_builder.build(
                    chunk_text=marked_source,
                    file_name=file_name,
                    chunk_index=chunk_index * 1000 + sub_index,
                    chunk_total=len(groups),
                    session_id=f"TQF032_RETRANSLATE_{Path(file_name).stem}_{chunk_index:06d}",
                    context={
                        "previous_summary": "",
                        "previous_chunk_tail": "",
                        "recent_characters": [],
                        "recent_terms": [],
                    },
                )

                self._strengthen_package_for_coverage(package, locked_title=locked_title)
                package_path = self.root / "prompt_packages" / f"{Path(file_name).stem}_chunk_{chunk_index:06d}_tqf032_sub_{sub_index:03d}.json"
                save_json(package_path, package)

                result = self._translate_with_best_effort(
                    engine=engine,
                    package=package,
                    package_path=package_path,
                    source_text=marked_source,
                    sub_index=sub_index,
                )

                if result["status"] not in ["success", "best_effort"]:
                    return {
                        "status": "failed",
                        "file": file_name,
                        "chunk": chunk_index,
                        "sub_index": sub_index,
                        "error": result.get("error", ""),
                        "coverage": result.get("coverage", {}),
                        "backup_path": str(backup_path) if backup_path else "",
                    }

                if result["status"] == "best_effort":
                    warnings.append(f"sub {sub_index} best_effort coverage={result.get('coverage', {}).get('score')}")

                outputs.append(Path(result["output_path"]))

            merged = self._merge_and_clean(output_path, outputs, locked_title=locked_title)
            final_text = merged.read_text(encoding="utf-8-sig")
            body_translation = self._remove_locked_title_from_translation(final_text, locked_title)
            final_coverage = self.coverage_checker.check(body_text, body_translation)

            append_log(self.log_path, f"TQF-03.2 done {file_name} chunk {chunk_index} coverage={final_coverage['score']}")

            return {
                "status": "success" if final_coverage["passed"] else "best_effort",
                "file": file_name,
                "chunk": chunk_index,
                "output_path": str(merged),
                "backup_path": str(backup_path) if backup_path else "",
                "subgroup_count": len(groups),
                "locked_title": locked_title,
                "coverage": final_coverage,
                "warnings": warnings,
            }

        except Exception as e:
            append_log(self.log_path, f"TQF-03.2 fatal error: {e}")
            return {"status": "failed", "error": str(e)}

    def _translate_with_best_effort(self, *, engine, package: dict, package_path: Path, source_text: str, sub_index: int) -> dict:
        best = None
        best_score = -1

        for attempt in range(1, self.MAX_ATTEMPT + 1):
            print(f"  sub {sub_index} attempt {attempt}/{self.MAX_ATTEMPT}")
            result = engine.translate_package(package, package_path=package_path)
            result["attempts"] = attempt

            if result.get("status") == "success":
                out_path = Path(result["output_path"])
                translation = self._clean_paragraph_markers(out_path.read_text(encoding="utf-8-sig"))
                out_path.write_text(translation.strip() + "\n", encoding="utf-8")

                coverage = self.coverage_checker.check(source_text, translation)
                result["coverage"] = coverage
                score = coverage.get("score", 0)

                if score > best_score:
                    best = result
                    best_score = score

                if coverage["passed"]:
                    return result

                print(f"  coverage not strict-pass score={score} issues={len(coverage['issues'])}")
                self._upgrade_package_strictness(package, attempt, coverage)
                save_json(package_path, package)
            else:
                if best is None:
                    best = result

            if attempt < self.MAX_ATTEMPT:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                print(f"  retry after {delay}s")
                time.sleep(delay)

        if best and best.get("status") == "success" and best_score >= self.BEST_EFFORT_MIN_SCORE:
            best["status"] = "best_effort"
            best["error"] = "Coverage did not pass strict threshold; saved best attempt."
            return best

        return best or {"status": "failed", "error": "No valid translation result."}

    def _strengthen_package_for_coverage(self, package: dict, locked_title: str = "") -> None:
        extra_rules = [
            "這是 TQF-03.2 覆蓋率重翻：禁止摘要，禁止合併段落。",
            "原文使用【P001】等段落標記。每個標記都必須出現在譯文中。",
            "每個【Pxxx】之後都必須有完整譯文，不能只輸出空標記。",
            "每個原文段落必須對應一個譯文段落，段落之間保留空行。",
            "不要濃縮、不要概括、不要省略心理描寫、動作、景物、比喻、停頓與語氣。",
            "譯文可以比原文長，忠實完整優先於簡短。",
            "不可把 패션 翻成時尚；作品標題由系統鎖定。",
        ]

        if locked_title:
            extra_rules.append(f"本段標題已鎖定為「{locked_title}」，不要再翻譯或輸出標題。")

        package["rules"].setdefault("coverage_rules", [])
        package["rules"]["coverage_rules"].extend(extra_rules)

        rule_text = "\n".join(f"- {r}" for r in extra_rules)
        package["prompt"]["user_prompt"] = package["prompt"]["user_prompt"].replace(
            "【待翻譯內容】",
            f"【TQF-03.2 覆蓋率要求】\n{rule_text}\n\n【待翻譯內容】"
        )

    def _upgrade_package_strictness(self, package: dict, attempt: int, coverage: dict) -> None:
        issues = coverage.get("issues", [])
        issue_text = "\n".join(f"- {i.get('message','')}" for i in issues)
        stricter = (
            f"\n\n【前一次覆蓋率檢查未達標 attempt={attempt}】\n"
            f"{issue_text}\n"
            "請重翻：每個【Pxxx】都必須保留並完整翻譯。不可摘要、不可合併段落、不可縮寫。\n"
        )
        package["prompt"]["user_prompt"] = stricter + package["prompt"]["user_prompt"]

    def _analyze_structure(self, text: str) -> dict:
        if not self.structure_engine:
            return {"has_title": False, "title": None}
        try:
            return self.structure_engine.analyze(text)
        except Exception:
            return {"has_title": False, "title": None}

    def _get_locked_title(self, structure: dict) -> str:
        if not structure or not structure.get("has_title"):
            return ""
        title = structure.get("title") or {}
        return str(title.get("target", "")).strip()

    def _remove_title_from_body(self, text: str, structure: dict) -> str:
        title = structure.get("title") or {}
        source_title = str(title.get("source", "")).strip()
        if not source_title:
            return text

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        new_lines = []
        removed = False

        for line in lines:
            if not removed and line.strip() == source_title:
                removed = True
                continue
            new_lines.append(line)

        return "\n".join(new_lines).strip() + "\n"

    def _split_paragraphs(self, text: str) -> list[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    def _group_paragraphs(self, paragraphs: list[str]) -> list[list[tuple[int, str]]]:
        groups = []
        current = []
        current_len = 0

        for idx, para in enumerate(paragraphs, start=1):
            para_len = len(para)

            if current and current_len + para_len > self.SUBCHUNK_TARGET:
                groups.append(current)
                current = [(idx, para)]
                current_len = para_len
            else:
                current.append((idx, para))
                current_len += para_len

        if current:
            groups.append(current)

        return groups

    def _mark_paragraphs(self, group: list[tuple[int, str]]) -> str:
        return "\n\n".join(f"【P{idx:03d}】\n{para}" for idx, para in group).strip() + "\n"

    def _merge_and_clean(self, output_path: Path, sub_outputs: list[Path], locked_title: str = "") -> Path:
        with output_path.open("w", encoding="utf-8", newline="\n") as out:
            if locked_title:
                out.write(locked_title.strip())
                out.write("\n\n")

            for p in sorted(sub_outputs, key=lambda x: x.name):
                text = p.read_text(encoding="utf-8-sig").strip()
                if text:
                    text = self._clean_paragraph_markers(text)
                    out.write(text.strip())
                    out.write("\n\n")

        return output_path

    def _clean_paragraph_markers(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\s*【P\d{3}】\s*", "\n\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _remove_locked_title_from_translation(self, text: str, locked_title: str) -> str:
        if not locked_title:
            return text

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        new_lines = []
        removed = False

        for line in lines:
            if not removed and line.strip() == locked_title:
                removed = True
                continue
            new_lines.append(line)

        return "\n".join(new_lines).strip()

    def _output_path(self, file_name: str, chunk_index: int) -> Path:
        return self.root / "translated" / f"{Path(file_name).stem}_chunk_{chunk_index:06d}_zh.txt"
