"""Reader-facing labels and actions (S9 §8/§9/§10/§15).

Pure mapping from reader state to Traditional-Chinese display text. The UI must
never show raw runtime statuses; it renders these labels instead.
"""

from __future__ import annotations

from .models import ReaderStatus


READER_STATUS_LABELS: dict[str, str] = {
    ReaderStatus.NOT_STARTED.value: "未開始",
    ReaderStatus.TRANSLATING.value: "翻譯中",
    ReaderStatus.RESUMABLE.value: "可繼續翻譯",
    ReaderStatus.COMPLETED.value: "已完成",
    ReaderStatus.INCOMPLETE.value: "翻譯不完整",
    ReaderStatus.FAILED.value: "翻譯失敗",
    ReaderStatus.SOURCE_CHANGED.value: "來源已變更",
    ReaderStatus.UNRECOVERABLE.value: "專案無法恢復",
}

READER_PRIMARY_ACTIONS: dict[str, str] = {
    ReaderStatus.NOT_STARTED.value: "開始翻譯",
    ReaderStatus.TRANSLATING.value: "",
    ReaderStatus.RESUMABLE.value: "繼續翻譯",
    ReaderStatus.COMPLETED.value: "開啟成品",
    ReaderStatus.INCOMPLETE.value: "繼續翻譯",
    ReaderStatus.FAILED.value: "繼續翻譯",
    ReaderStatus.SOURCE_CHANGED.value: "查看",
    ReaderStatus.UNRECOVERABLE.value: "查看問題",
}

FORMAT_LABELS: dict[str, str] = {"txt": "TXT", "epub": "EPUB"}

LANGUAGE_LABELS: dict[str, str] = {
    "ko": "韓",
    "ja": "日",
    "zh": "中",
    "en": "英",
    "zh-TW": "繁中",
}


def reader_status_label(status: str) -> str:
    return READER_STATUS_LABELS.get(str(status), "未開始")


def primary_action_label(status: str) -> str:
    return READER_PRIMARY_ACTIONS.get(str(status), "開始翻譯")


def format_label(fmt: str) -> str:
    return FORMAT_LABELS.get(str(fmt), str(fmt).upper())


def language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(str(code), str(code))


def translation_direction(source_language: str, target_language: str) -> str:
    return f"{language_label(source_language)} → {language_label(target_language)}"


def progress_percent(completed: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round(completed * 100 / total))))


def progress_text(completed: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{progress_percent(completed, total)}%"
