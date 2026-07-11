from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .models import QualityIssue, QualityReport


_HANGUL_RE = re.compile(r"[가-힣]")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_DIALOGUE_BAD_RE = re.compile(r'(^|[\s])["“”](.+?)["“”]')
_SENTENCE_END_RE = re.compile(r"[。！？!?…]+")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


class TranslationQualityBaseline:
    """Side-effect-free Korean→Traditional Chinese quality baseline."""

    version = "TE-v5.0"
    stage = "5.0.1"

    def evaluate(
        self,
        source_text: Optional[str],
        translated_text: Optional[str],
        *,
        locked_terms: Optional[Mapping[str, str]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        source = str(source_text or "")
        translated = str(translated_text or "")
        cfg = self._config(config)
        terms = dict(locked_terms or {})
        issues: List[QualityIssue] = []

        source_chars = len(source)
        translated_chars = len(translated)
        ratio = round(translated_chars / source_chars, 4) if source_chars else 0.0
        hangul_count = len(_HANGUL_RE.findall(translated))
        cjk_count = len(_CJK_RE.findall(translated))
        duplicate_paragraphs = self._duplicate_paragraph_count(translated)
        duplicate_lines = self._duplicate_line_count(translated)
        source_paragraphs = self._paragraph_count(source)
        translated_paragraphs = self._paragraph_count(translated)
        source_sentences = self._sentence_count(source)
        translated_sentences = self._sentence_count(translated)
        bad_dialogue_quotes = len(_DIALOGUE_BAD_RE.findall(translated))
        terminology_mismatches = self._terminology_mismatches(
            source, translated, terms
        )

        if source and not translated.strip():
            issues.append(QualityIssue(
                "empty_output", "critical", "譯文為空。",
                "retranslate_original_chunk"
            ))
        if source and translated and ratio < cfg["min_length_ratio"]:
            issues.append(QualityIssue(
                "too_short", "critical", "譯文長度相對原文過短。",
                "split_and_retranslate",
                {"length_ratio": ratio}
            ))
        if source and translated and ratio > cfg["max_length_ratio"]:
            issues.append(QualityIssue(
                "too_long", "high", "譯文長度異常偏長，可能有重複或擴寫。",
                "inspect_and_retranslate",
                {"length_ratio": ratio}
            ))
        if hangul_count > cfg["max_hangul_residue"]:
            issues.append(QualityIssue(
                "hangul_residue", "critical", "譯文仍殘留韓文。",
                "retranslate_residual_spans",
                {"count": hangul_count}
            ))
        if duplicate_paragraphs > cfg["max_duplicate_paragraphs"]:
            issues.append(QualityIssue(
                "duplicate_paragraph", "high", "偵測到重複段落。",
                "deduplicate_or_retranslate",
                {"count": duplicate_paragraphs}
            ))
        if duplicate_lines > cfg["max_duplicate_lines"]:
            issues.append(QualityIssue(
                "duplicate_line", "medium", "偵測到重複句行。",
                "deduplicate_or_retranslate",
                {"count": duplicate_lines}
            ))
        paragraph_ratio = (
            translated_paragraphs / source_paragraphs
            if source_paragraphs else 0.0
        )
        sentence_ratio = (
            translated_sentences / source_sentences
            if source_sentences else 0.0
        )
        paragraph_ratio_low = (
            source_paragraphs >= cfg["paragraph_check_min"]
            and translated_paragraphs
            < max(1, round(source_paragraphs * cfg["min_paragraph_ratio"]))
        )
        if paragraph_ratio_low:
            # TE v5.3.1.1: literary Chinese may legitimately merge adjacent
            # Korean paragraphs.  Paragraph count alone is therefore not
            # sufficient evidence of omitted content.  Escalate to a retry
            # only when sentence or length coverage independently supports
            # the omission suspicion; otherwise retain a non-blocking warning.
            corroborated = (
                ratio < cfg["paragraph_omission_length_ratio"]
                or (
                    source_sentences >= cfg["sentence_check_min"]
                    and sentence_ratio < cfg["paragraph_omission_sentence_ratio"]
                )
            )
            issues.append(QualityIssue(
                "paragraph_omission_suspected" if corroborated
                else "paragraph_structure_merged",
                "high" if corroborated else "medium",
                "譯文段落數明顯少於原文，且句數或長度覆蓋不足，疑似漏段。"
                if corroborated else
                "譯文合併了部分原文段落；內容覆蓋未顯示明顯漏譯。",
                "retranslate_original_chunk" if corroborated
                else "review_paragraph_structure",
                {
                    "source_paragraphs": source_paragraphs,
                    "translated_paragraphs": translated_paragraphs,
                    "paragraph_ratio": round(paragraph_ratio, 4),
                    "source_sentences": source_sentences,
                    "translated_sentences": translated_sentences,
                    "sentence_ratio": round(sentence_ratio, 4),
                    "length_ratio": ratio,
                    "corroborated": corroborated,
                }
            ))
        if (
            source_sentences >= cfg["sentence_check_min"]
            and translated_sentences
            < max(1, round(source_sentences * cfg["min_sentence_ratio"]))
        ):
            issues.append(QualityIssue(
                "sentence_omission_suspected", "high",
                "譯文句子數明顯少於原文，疑似摘要或漏翻。",
                "retranslate_original_chunk",
                {
                    "source_sentences": source_sentences,
                    "translated_sentences": translated_sentences,
                }
            ))
        if bad_dialogue_quotes > 0:
            issues.append(QualityIssue(
                "dialogue_quote_format", "low",
                "偵測到非「」形式的對話引號。",
                "normalize_dialogue_quotes",
                {"count": bad_dialogue_quotes}
            ))
        for mismatch in terminology_mismatches:
            issues.append(QualityIssue(
                "locked_term_missing", "high",
                f"固定譯名未依規則出現：{mismatch['source']} → {mismatch['target']}",
                "apply_locked_terminology",
                mismatch,
            ))

        score = self._score(issues)
        accepted = not any(
            issue.severity in {"critical", "high"} for issue in issues
        )

        report = QualityReport(
            accepted=accepted,
            score=score,
            issues=[issue.to_dict() for issue in issues],
            metrics={
                "source_chars": source_chars,
                "translated_chars": translated_chars,
                "length_ratio": ratio,
                "hangul_residue_count": hangul_count,
                "cjk_count": cjk_count,
                "duplicate_paragraph_count": duplicate_paragraphs,
                "duplicate_line_count": duplicate_lines,
                "source_paragraph_count": source_paragraphs,
                "translated_paragraph_count": translated_paragraphs,
                "source_sentence_count": source_sentences,
                "translated_sentence_count": translated_sentences,
                "bad_dialogue_quote_count": bad_dialogue_quotes,
                "terminology_mismatch_count": len(terminology_mismatches),
            },
            normalized_text=translated,
            stage=self.stage,
        )
        return report.to_dict()

    def validate_report(self, report: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(report, Mapping):
            return False
        required = {
            "accepted", "score", "issues", "metrics",
            "normalized_text", "stage"
        }
        if not required.issubset(report):
            return False
        if report.get("stage") != self.stage:
            return False
        score = report.get("score")
        if not isinstance(score, int) or not 0 <= score <= 100:
            return False
        if not isinstance(report.get("issues"), list):
            return False
        if not isinstance(report.get("metrics"), Mapping):
            return False
        return True

    @staticmethod
    def _config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        src = dict(config or {})
        return {
            "min_length_ratio": float(src.get("min_length_ratio", 0.35)),
            "max_length_ratio": float(src.get("max_length_ratio", 2.5)),
            "max_hangul_residue": int(src.get("max_hangul_residue", 0)),
            "max_duplicate_paragraphs": int(
                src.get("max_duplicate_paragraphs", 0)
            ),
            "max_duplicate_lines": int(src.get("max_duplicate_lines", 1)),
            "paragraph_check_min": int(src.get("paragraph_check_min", 3)),
            "min_paragraph_ratio": float(src.get("min_paragraph_ratio", 0.5)),
            "paragraph_omission_length_ratio": float(
                src.get("paragraph_omission_length_ratio", 0.45)
            ),
            "paragraph_omission_sentence_ratio": float(
                src.get("paragraph_omission_sentence_ratio", 0.60)
            ),
            "sentence_check_min": int(src.get("sentence_check_min", 4)),
            "min_sentence_ratio": float(src.get("min_sentence_ratio", 0.5)),
        }

    @staticmethod
    def _score(issues: Iterable[QualityIssue]) -> int:
        penalties = {"critical": 35, "high": 20, "medium": 10, "low": 4}
        return max(0, 100 - sum(penalties.get(i.severity, 5) for i in issues))

    @staticmethod
    def _paragraph_count(text: str) -> int:
        if not text.strip():
            return 0
        return len([p for p in _PARAGRAPH_SPLIT_RE.split(text.strip()) if p.strip()])

    @staticmethod
    def _sentence_count(text: str) -> int:
        if not text.strip():
            return 0
        count = len(_SENTENCE_END_RE.findall(text))
        if count:
            return count
        return len([line for line in text.splitlines() if line.strip()])

    @staticmethod
    def _duplicate_paragraph_count(text: str) -> int:
        paragraphs = [
            p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text.strip()) if p.strip()
        ]
        counts = Counter(paragraphs)
        return sum(count - 1 for count in counts.values() if count > 1)

    @staticmethod
    def _duplicate_line_count(text: str) -> int:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        counts = Counter(lines)
        return sum(count - 1 for count in counts.values() if count > 1)

    @staticmethod
    def _terminology_mismatches(
        source: str,
        translated: str,
        terms: Mapping[str, str],
    ) -> List[Dict[str, str]]:
        mismatches: List[Dict[str, str]] = []
        for source_term, target_term in terms.items():
            if source_term and source_term in source and target_term not in translated:
                mismatches.append({"source": source_term, "target": target_term})
        return mismatches
