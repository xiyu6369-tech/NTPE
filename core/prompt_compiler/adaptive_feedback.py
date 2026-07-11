from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

ADAPTIVE_FEEDBACK_VERSION = "5.5.3.1"


@dataclass(frozen=True)
class AdaptiveFeedback:
    codes: tuple[str, ...]
    directives: tuple[str, ...]
    enabled: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": ADAPTIVE_FEEDBACK_VERSION,
            "enabled": self.enabled,
            "issue_codes": list(self.codes),
            "directive_count": len(self.directives),
        }


_DIRECTIVES: dict[str, tuple[str, ...]] = {
    "EMPTY_OUTPUT": (
        "必須輸出完整譯文，不得留空，也不得只輸出說明。",
    ),
    "TOO_SHORT": (
        "前次譯文疑似漏譯；逐句覆蓋原文全部資訊，不得摘要、合併或省略。",
        "保持原文事件與敘事資訊的先後次序。",
    ),
    "PARAGRAPH_OMISSION_SUSPECTED": (
        "前次譯文疑似漏段；逐段核對原文，確保每個敘事單位及其資訊都被翻譯。",
        "可以依繁體中文小說節奏自然分段，但不得因合併段落而省略事件、動作、對話或敘事資訊。",
        "只補回遺漏資訊，不得重述前次已完整覆蓋的內容。",
    ),
    "SENTENCE_OMISSION_SUSPECTED": (
        "前次譯文疑似漏句；逐句翻譯，不得用概括句取代具體內容。",
    ),
    "HANGUL_RESIDUE": (
        "完整翻譯所有韓文內容，除固定專名外不得留下韓文字元。",
    ),
    "LOCKED_TERM_MISSING": (
        "嚴格使用 Glossary 與鎖定譯名，不得自行改成近似音譯或替代名稱。",
    ),
    "DUPLICATE_LINE": (
        "不得重複輸出相同句行；每項原文資訊只翻譯一次。",
    ),
    "DUPLICATE_SENTENCE": (
        "不得重複敘述相同句意；刪除模型自行產生的重述。",
    ),
    "DUPLICATE_PARAGRAPH": (
        "不得重複輸出相同段落；每個原文段落只對應一次譯文。",
    ),
    "SEMANTIC_DUPLICATE_PARAGRAPH": (
        "前次輸出出現改寫式重複；不得換句話重述前文或本段已翻譯資訊。",
        "Previous 僅供語境承接，不得重新翻譯進本次輸出。",
    ),
    "QUALITY_LOCK_VIOLATION": (
        "只翻譯原文可直接支持的內容，不得新增地名、事件、動作、心理或具體程度。",
        "不得把含糊描述擴寫成更具體、更強烈的敘述。",
    ),
    "ADDED_DETAIL": (
        "移除原文未明示的具體資訊；不得補充背景、過渡、動機或結論。",
    ),
    "HALLUCINATION": (
        "不得創造原文不存在的專名、場景、事件或人物資訊。",
    ),
    "NATURALNESS_GUARD": (
        "避免生硬直譯、錯誤搭配與不合語境的詞語；使用自然的繁體中文小說句法。",
        "不得為了流暢而改變、增加或縮減原意。",
    ),
}

_GENERIC_BLOCKING = (
    "針對下列品質問題重新翻譯，必須修正問題，但不得新增原文沒有的內容。",
)


def adaptive_feedback_enabled() -> bool:
    value = os.environ.get("NTPE_ADAPTIVE_PROMPT_FEEDBACK", "1").strip().lower()
    return value not in {"0", "false", "off", "no"}


def _canonical_code(issue: Mapping[str, Any]) -> str:
    return str(issue.get("code") or issue.get("type") or "QUALITY_ISSUE").strip().upper()


def _blocking_issues(qa_report: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    report = qa_report or {}
    unified = report.get("unified_quality_report") if isinstance(report, Mapping) else None
    source = []
    if isinstance(unified, Mapping):
        source = unified.get("merged_issues") or []
    if not source:
        source = report.get("issues") or []
    blocking: list[Mapping[str, Any]] = []
    for issue in source:
        if not isinstance(issue, Mapping):
            continue
        severity = str(issue.get("severity") or "").lower()
        retry = bool(issue.get("retry_required") or issue.get("retry_worthy"))
        if retry or severity in {"critical", "high"}:
            blocking.append(issue)
    return blocking




def _format_coverage_directive(issue: Mapping[str, Any]) -> str:
    evidence = issue.get("evidence") or issue.get("metadata") or {}
    if not isinstance(evidence, Mapping):
        return ""
    values = {
        "source_paragraphs": evidence.get("source_paragraphs"),
        "translated_paragraphs": evidence.get("translated_paragraphs"),
        "source_sentences": evidence.get("source_sentences"),
        "translated_sentences": evidence.get("translated_sentences"),
        "length_ratio": evidence.get("length_ratio"),
    }
    parts: list[str] = []
    if values["source_paragraphs"] is not None and values["translated_paragraphs"] is not None:
        parts.append(f"原文段落 {values['source_paragraphs']}，前次譯文段落 {values['translated_paragraphs']}")
    if values["source_sentences"] is not None and values["translated_sentences"] is not None:
        parts.append(f"原文句數 {values['source_sentences']}，前次譯文句數 {values['translated_sentences']}")
    if values["length_ratio"] is not None:
        try:
            parts.append(f"前次譯文長度比 {float(values['length_ratio']):.2f}")
        except (TypeError, ValueError):
            pass
    return "前次完整性指標：" + "；".join(parts) + "。" if parts else ""

def build_adaptive_feedback(qa_report: Mapping[str, Any] | None) -> AdaptiveFeedback:
    if not adaptive_feedback_enabled():
        return AdaptiveFeedback(codes=(), directives=(), enabled=False)

    issues = _blocking_issues(qa_report)
    codes: list[str] = []
    directives: list[str] = []
    for issue in issues:
        code = _canonical_code(issue)
        if code.startswith("V5_"):
            code = code[3:]
        if code not in codes:
            codes.append(code)
        mapped = _DIRECTIVES.get(code, _GENERIC_BLOCKING)
        if code in {"PARAGRAPH_OMISSION_SUSPECTED", "SENTENCE_OMISSION_SUSPECTED", "TOO_SHORT"}:
            coverage = _format_coverage_directive(issue)
            if coverage and coverage not in directives:
                directives.append(coverage)
        for directive in mapped:
            if directive not in directives:
                directives.append(directive)

    return AdaptiveFeedback(codes=tuple(codes), directives=tuple(directives), enabled=True)


def render_adaptive_feedback_block(feedback: AdaptiveFeedback, qa_attempt: int) -> str:
    if not feedback.enabled or not feedback.directives:
        return ""
    code_text = ", ".join(feedback.codes) or "QUALITY_ISSUE"
    lines = [
        "【NTPE Adaptive Prompt Feedback】",
        f"QA retry attempt: {qa_attempt}",
        f"Blocking issue codes: {code_text}",
        "請重新翻譯原文，並遵守以下定向修正：",
    ]
    lines.extend(f"- {directive}" for directive in feedback.directives)
    lines.extend([
        "- 不得沿用或改寫前次錯誤輸出。",
        "- 只輸出完整繁體中文譯文，不要輸出分析或說明。",
        "[/NTPE Adaptive Prompt Feedback]",
    ])
    return "\n".join(lines)
