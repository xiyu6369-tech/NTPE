from __future__ import annotations

import hashlib
from typing import Mapping

from .model import PromptContextAnchor

ANCHOR_VERSION = "7.0.0-stage07.3"
PACKAGE_ANCHOR_VERSION = "7.0.0-stage07.4"
_BOUND_KEY = "prompt_context_anchor_bound"

_ZH_START = "【前文參考，僅供保持語氣與銜接，禁止重複翻譯】\n"
_ZH_END = "\n\n【待翻譯內容】"
_LITERARY_START = "【Previous】"
_LEGACY_START = "前文：\n"
_LEGACY_ENDS = ("\n待翻譯：", "\n待翻譯")
_FIXTURE_START = "CTX\n"
_FIXTURE_END = "\nSRC"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _compact_previous(value: str, limit: int = 160) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[-limit:]


def _failure(reason: str, *, source: str = "", strategy: str = "none") -> PromptContextAnchor:
    return PromptContextAnchor(
        version=ANCHOR_VERSION,
        strategy=strategy,
        addressable=False,
        reason=reason,
        start=-1,
        end=-1,
        content_sha256="",
        source_sha256=_sha(source),
    )


def _candidate_matches_source(candidate: str, source: str) -> bool:
    if candidate == source:
        return True
    candidate_normalized = " ".join(candidate.split())
    source_normalized = " ".join(source.split())
    if candidate_normalized == source_normalized:
        return True
    compact = _compact_previous(source)
    return bool(compact) and candidate_normalized == compact



def _anchor_from_metadata(package: Mapping[str, object]) -> PromptContextAnchor | None:
    context = package.get("context", {})
    prompt = package.get("prompt", {})
    if not isinstance(context, Mapping) or not isinstance(prompt, Mapping):
        return None
    metadata = context.get(_BOUND_KEY)
    if not isinstance(metadata, Mapping):
        return None
    user_prompt = str(prompt.get("user_prompt", "") or "")
    source = str(context.get("previous_chunk_tail", "") or "")
    try:
        start = int(metadata.get("start", -1))
        end = int(metadata.get("end", -1))
    except (TypeError, ValueError):
        return _failure("prompt-context-bound-anchor-invalid", source=source, strategy="package-bound")
    if start < 0 or end <= start or end > len(user_prompt):
        return _failure("prompt-context-bound-anchor-invalid", source=source, strategy="package-bound")
    candidate = user_prompt[start:end]
    expected_content = str(metadata.get("content_sha256", "") or "")
    expected_prompt = str(metadata.get("prompt_sha256", "") or "")
    expected_source = str(metadata.get("source_sha256", "") or "")
    if expected_prompt != _sha(user_prompt) or expected_content != _sha(candidate) or expected_source != _sha(source):
        return _failure("prompt-context-bound-anchor-hash-mismatch", source=source, strategy="package-bound")
    if not _candidate_matches_source(candidate, source):
        return _failure("prompt-context-bound-anchor-source-mismatch", source=source, strategy="package-bound")
    return PromptContextAnchor(
        version=ANCHOR_VERSION, strategy="package-bound", addressable=True, reason="",
        start=start, end=end, content_sha256=_sha(candidate), source_sha256=_sha(source),
    )


def _section_candidates(user_prompt: str, start_marker: str, end_marker: str) -> list[tuple[int, int, str]]:
    results: list[tuple[int, int, str]] = []
    cursor = 0
    while True:
        marker_at = user_prompt.find(start_marker, cursor)
        if marker_at < 0:
            break
        start = marker_at + len(start_marker)
        end = user_prompt.find(end_marker, start)
        if end >= 0:
            results.append((start, end, user_prompt[start:end]))
        cursor = marker_at + 1
    return results


def bind_prompt_context_anchor(package: dict[str, object]) -> PromptContextAnchor:
    context = package.get("context", {})
    prompt = package.get("prompt", {})
    if not isinstance(context, dict) or not isinstance(prompt, dict):
        return _failure("invalid-package-shape")
    source = str(context.get("previous_chunk_tail", "") or "")
    user_prompt = str(prompt.get("user_prompt", "") or "")
    if not source:
        return _failure("empty-previous-context", source=source, strategy="package-bound")
    candidates: list[tuple[str, int, int, str]] = []
    for start, end, value in _section_candidates(user_prompt, _ZH_START, _ZH_END):
        candidates.append(("zh-section", start, end, value))
    for start, end, value in _section_candidates(user_prompt, _LEGACY_START, _LEGACY_ENDS[0]):
        candidates.append(("legacy-labeled-section", start, end, value))
    for start, end, value in _section_candidates(user_prompt, _FIXTURE_START, _FIXTURE_END):
        candidates.append(("fixture-labeled-section", start, end, value))
    # Literary prompts do not have a fixed end marker; enumerate every marker and use the next section.
    cursor = 0
    while True:
        marker_at = user_prompt.find(_LITERARY_START, cursor)
        if marker_at < 0:
            break
        start = marker_at + len(_LITERARY_START)
        end = user_prompt.find("\n【", start)
        if end < 0:
            end = len(user_prompt)
        raw = user_prompt[start:end]
        leading = len(raw) - len(raw.lstrip("\n"))
        trailing = len(raw) - len(raw.rstrip("\n"))
        start += leading
        end -= trailing
        candidates.append(("literary-previous", start, end, user_prompt[start:end]))
        cursor = marker_at + 1
    matches = [row for row in candidates if _candidate_matches_source(row[3], source)]
    if len(matches) != 1:
        reason = "prompt-context-bound-anchor-missing" if not matches else "prompt-context-bound-anchor-ambiguous"
        return _failure(reason, source=source, strategy="package-bound")
    _, start, end, candidate = matches[0]
    context[_BOUND_KEY] = {
        "version": PACKAGE_ANCHOR_VERSION,
        "strategy": "package-bound",
        "start": start,
        "end": end,
        "content_sha256": _sha(candidate),
        "source_sha256": _sha(source),
        "prompt_sha256": _sha(user_prompt),
        "content_redacted": True,
    }
    package["context"] = context
    return PromptContextAnchor(
        version=ANCHOR_VERSION, strategy="package-bound", addressable=True, reason="",
        start=start, end=end, content_sha256=_sha(candidate), source_sha256=_sha(source),
    )

def resolve_prompt_context_anchor(package: Mapping[str, object]) -> PromptContextAnchor:
    bound = _anchor_from_metadata(package)
    if bound is not None:
        return bound
    context = package.get("context", {})
    prompt = package.get("prompt", {})
    if not isinstance(context, Mapping) or not isinstance(prompt, Mapping):
        return _failure("invalid-package-shape")
    source = str(context.get("previous_chunk_tail", "") or "")
    user_prompt = str(prompt.get("user_prompt", "") or "")
    if not source:
        return _failure("empty-previous-context", source=source)
    if not user_prompt:
        return _failure("empty-user-prompt", source=source)

    start_count = user_prompt.count(_ZH_START)
    end_count = user_prompt.count(_ZH_END)
    if start_count == 1 and end_count == 1:
        content_start = user_prompt.index(_ZH_START) + len(_ZH_START)
        content_end = user_prompt.index(_ZH_END, content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="zh-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="zh-section",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if start_count > 1 or end_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="zh-section")

    previous_count = user_prompt.count(_LITERARY_START)
    if previous_count == 1:
        content_start = user_prompt.index(_LITERARY_START) + len(_LITERARY_START)
        content_end = len(user_prompt)
        next_section = user_prompt.find("\n【", content_start)
        if next_section >= 0:
            content_end = next_section
        candidate = user_prompt[content_start:content_end].strip("\n")
        leading = len(user_prompt[content_start:content_end]) - len(user_prompt[content_start:content_end].lstrip("\n"))
        trailing = len(user_prompt[content_start:content_end]) - len(user_prompt[content_start:content_end].rstrip("\n"))
        content_start += leading
        content_end -= trailing
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="literary-previous")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="literary-previous",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if previous_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="literary-previous")

    legacy_count = user_prompt.count(_LEGACY_START)
    matching_ends = tuple(marker for marker in _LEGACY_ENDS if user_prompt.count(marker) == 1)
    if len(matching_ends) > 1:
        matching_ends = (max(matching_ends, key=len),)
    if legacy_count == 1 and len(matching_ends) == 1:
        content_start = user_prompt.index(_LEGACY_START) + len(_LEGACY_START)
        content_end = user_prompt.index(matching_ends[0], content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="legacy-labeled-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION,
            strategy="legacy-labeled-section",
            addressable=True,
            reason="",
            start=content_start,
            end=content_end,
            content_sha256=_sha(candidate),
            source_sha256=_sha(source),
        )
    if legacy_count > 1 or len(matching_ends) > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="legacy-labeled-section")

    fixture_start_count = user_prompt.count(_FIXTURE_START)
    fixture_end_count = user_prompt.count(_FIXTURE_END)
    if fixture_start_count == 1 and fixture_end_count == 1:
        content_start = user_prompt.index(_FIXTURE_START) + len(_FIXTURE_START)
        content_end = user_prompt.index(_FIXTURE_END, content_start)
        candidate = user_prompt[content_start:content_end]
        if not _candidate_matches_source(candidate, source):
            return _failure("prompt-context-anchor-hash-mismatch", source=source, strategy="fixture-labeled-section")
        return PromptContextAnchor(
            version=ANCHOR_VERSION, strategy="fixture-labeled-section", addressable=True, reason="",
            start=content_start, end=content_end, content_sha256=_sha(candidate), source_sha256=_sha(source),
        )
    if fixture_start_count > 1 or fixture_end_count > 1:
        return _failure("prompt-context-anchor-ambiguous", source=source, strategy="fixture-labeled-section")
    return _failure("prompt-context-anchor-marker-missing", source=source)


def anchored_context_text(package: Mapping[str, object], anchor: PromptContextAnchor) -> str:
    if not anchor.addressable:
        return ""
    prompt = package.get("prompt", {})
    if not isinstance(prompt, Mapping):
        return ""
    user_prompt = str(prompt.get("user_prompt", "") or "")
    if anchor.start < 0 or anchor.end < anchor.start or anchor.end > len(user_prompt):
        return ""
    value = user_prompt[anchor.start:anchor.end]
    if _sha(value) != anchor.content_sha256:
        return ""
    return value


def replace_anchored_context(
    package: dict[str, object],
    anchor: PromptContextAnchor,
    replacement: str,
) -> bool:
    if not anchor.addressable or not replacement:
        return False
    prompt = package.get("prompt", {})
    context = package.get("context", {})
    if not isinstance(prompt, dict) or not isinstance(context, dict):
        return False
    user_prompt = str(prompt.get("user_prompt", "") or "")
    current = anchored_context_text(package, anchor)
    if not current:
        return False
    prefix = user_prompt[: anchor.start]
    suffix = user_prompt[anchor.end :]
    replaced = prefix + replacement + suffix
    if replaced[: anchor.start] != prefix or not replaced.endswith(suffix):
        return False
    new_prompt = dict(prompt)
    new_prompt["user_prompt"] = replaced
    new_context = dict(context)
    new_context["previous_chunk_tail"] = replacement
    new_context["prompt_context_anchor"] = {
        **anchor.to_metadata(),
        "replacement_sha256": _sha(replacement),
        "replacement_length": len(replacement),
    }
    package["prompt"] = new_prompt
    package["context"] = new_context
    return True
