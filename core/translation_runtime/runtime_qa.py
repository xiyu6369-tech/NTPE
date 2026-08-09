from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from core.translation_engine.context_intelligence import detect_unnatural_phrases


NATURALNESS_GUARD_CODE = "NATURALNESS_GUARD"
KOREAN_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")
_SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_DIALOGUE_QUOTE_RE = re.compile(r"[“”]|(?<![A-Za-z0-9])\"[^\"\n]{1,200}\"")

_LITERARY_QUALITY_CODES = {
    "NATURALNESS_PERSON_HUMAN_WORLD",
    "NATURALNESS_BREATH_ACTION",
    "NATURALNESS_REDUNDANT_COUNTING",
    "NATURALNESS_TOURIST_PERSON",
    "NATURALNESS_OVERLITERAL_ENTANGLED",
}


@dataclass(frozen=True)
class RuntimeQAPolicy:
    """Runtime-level translation quality gate policy.

    TER-v2.2 keeps the policy small and deterministic so it can be reused by
    TXT runtime, provider integration tests, and regression tests without
    calling an external model.
    """

    enabled: bool = True
    min_length_ratio: float = 0.25
    max_korean_chars: int = 3
    max_repeated_lines: int = 2
    max_repeated_sentences: int = 2
    simplified_chinese_policy: str = "normalize"  # normalize|warn|fail
    dialogue_quote_policy: str = "fail"  # normalize|warn|fail
    quality_profile: str = "general"
    naturalness_guard_policy: str = "warn"  # off|warn|high_confidence_only|quality_retry|literary_retry|fail

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def count_korean_characters(text: str) -> int:
    return len(KOREAN_RE.findall(text or ""))


def _normalized_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def detect_repeated_lines(text: str, max_repeated_lines: int = 2) -> list[str]:
    counts: dict[str, int] = {}
    repeated: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if len(line) < 4:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] > max_repeated_lines and line not in repeated:
            repeated.append(line)
    return repeated


def detect_repeated_sentences(text: str, max_repeated_sentences: int = 2) -> list[str]:
    counts: dict[str, int] = {}
    repeated: list[str] = []
    for match in _SENTENCE_RE.finditer(text or ""):
        sentence = match.group(0).strip()
        if len(sentence) < 4:
            continue
        counts[sentence] = counts.get(sentence, 0) + 1
        if counts[sentence] > max_repeated_sentences and sentence not in repeated:
            repeated.append(sentence)
    return repeated


def detect_dialogue_quote_violations(text: str) -> list[str]:
    """Detect provider dialogue quotes that should be normalized to 「」."""
    hits: list[str] = []
    for match in _DIALOGUE_QUOTE_RE.finditer(text or ""):
        sample = match.group(0)
        if sample and sample not in hits:
            hits.append(sample)
        if len(hits) >= 10:
            break
    return hits


def detect_simplified_chinese(text: str, simplified_terms: Sequence[str] | None = None) -> list[str]:
    terms = list(simplified_terms or ())
    hits: list[str] = []
    for term in terms:
        if term and term in (text or "") and term not in hits:
            hits.append(term)
        if len(hits) >= 20:
            break
    return hits


def detect_locked_term_violations(
    source_text: str,
    translated_text: str,
    locked_dictionary: Mapping[str, str] | None = None,
    alias_map: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for src, target in (locked_dictionary or {}).items():
        if src and src in source_text and target and target not in translated_text:
            violations.append({"source": src, "target": target, "code": "LOCKED_TERM_MISSING"})
    for alias, target in (alias_map or {}).items():
        if alias and alias in translated_text:
            violations.append({"alias": alias, "target": target, "code": "LOCKED_ALIAS_USED"})
    return violations


def _simplified_severity(policy: str) -> str:
    return "error" if (policy or "normalize").lower() == "fail" else "warning"


def analyze_runtime_quality(
    source_text: str,
    translated_text: str,
    policy: RuntimeQAPolicy | None = None,
    *,
    locked_dictionary: Mapping[str, str] | None = None,
    alias_map: Mapping[str, str] | None = None,
    simplified_terms: Sequence[str] | None = None,
    extra_violations: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    policy = policy or RuntimeQAPolicy()
    source_len = max(1, _normalized_len(source_text))
    translated_len = _normalized_len(translated_text)
    length_ratio = translated_len / source_len
    korean_chars = count_korean_characters(translated_text)
    repeated_lines = detect_repeated_lines(translated_text, policy.max_repeated_lines)
    repeated_sentences = detect_repeated_sentences(translated_text, policy.max_repeated_sentences)
    simplified_hits = detect_simplified_chinese(translated_text, simplified_terms)
    dialogue_quote_hits = detect_dialogue_quote_violations(translated_text)
    naturalness_hits = detect_unnatural_phrases(translated_text)
    lit_classification = classify_literary_quality_hits(naturalness_hits)
    term_violations = detect_locked_term_violations(source_text, translated_text, locked_dictionary, alias_map)
    quality_lock_violations = [dict(item) for item in (extra_violations or [])]
    issues: list[dict[str, Any]] = []

    if not policy.enabled:
        return {
            "passed": True,
            "enabled": False,
            "issues": [],
            "metrics": {
                "source_chars": source_len,
                "translated_chars": translated_len,
                "length_ratio": round(length_ratio, 4),
                "korean_chars": korean_chars,
                "repeated_line_count": len(repeated_lines),
                "repeated_sentence_count": len(repeated_sentences),
                "simplified_hits": len(simplified_hits),
                "dialogue_quote_violations": len(dialogue_quote_hits),
                "naturalness_violations": len(naturalness_hits),
                "locked_term_violations": len(term_violations),
                "quality_lock_violations": len(quality_lock_violations),
                "literary_quality_hits": lit_classification["literary_quality_hit_count"],
                "literary_quality_errors": 0,
                "literary_quality_warnings": 0,
                "literary_quality_passed": True,
                "literary_quality_issue_codes": [h.get("code") for h in lit_classification["literary_quality_hits"]],
            },
        }

    if translated_len == 0:
        issues.append({"code": "EMPTY_TRANSLATION", "message": "EMPTY_TRANSLATION translated output is empty"})
    elif length_ratio < policy.min_length_ratio:
        issues.append({"code": "LENGTH_RATIO_TOO_LOW", "message": f"LENGTH_RATIO_TOO_LOW ratio={length_ratio:.3f} min={policy.min_length_ratio:.3f}"})
    if korean_chars > policy.max_korean_chars:
        issues.append({"code": "KOREAN_RESIDUE", "message": f"KOREAN_RESIDUE korean_chars={korean_chars} max={policy.max_korean_chars}"})
    if repeated_lines:
        issues.append({"code": "REPEATED_LINES", "message": f"REPEATED_LINES count={len(repeated_lines)}", "samples": repeated_lines[:3]})
    if repeated_sentences:
        issues.append({"code": "REPEATED_SENTENCES", "message": f"REPEATED_SENTENCES count={len(repeated_sentences)}", "samples": repeated_sentences[:3]})
    if simplified_hits:
        issues.append({
            "code": "SIMPLIFIED_CHINESE",
            "message": f"SIMPLIFIED_CHINESE hits={len(simplified_hits)} policy={policy.simplified_chinese_policy}",
            "samples": simplified_hits[:10],
            "severity": _simplified_severity(policy.simplified_chinese_policy),
        })
    if dialogue_quote_hits and (policy.dialogue_quote_policy or "fail").lower() != "normalize":
        issues.append({
            "code": "DIALOGUE_QUOTE_FORMAT",
            "message": f"DIALOGUE_QUOTE_FORMAT count={len(dialogue_quote_hits)} policy={policy.dialogue_quote_policy}",
            "samples": dialogue_quote_hits[:10],
            "severity": "error" if (policy.dialogue_quote_policy or "fail").lower() == "fail" else "warning",
        })
    if naturalness_hits and (policy.naturalness_guard_policy or "warn").lower() != "off":
        retryable_hits = _retryable_naturalness_hits(policy, naturalness_hits)
        severity = "error" if retryable_hits else "warning"
        issues.append({
            "code": "NATURALNESS_GUARD",
            "message": f"NATURALNESS_GUARD high-risk phrases={len(naturalness_hits)} policy={policy.naturalness_guard_policy}",
            "samples": naturalness_hits[:10],
            "severity": severity,
            "retry_worthy": severity == "error",
            "retryable_samples": retryable_hits[:10],
        })
    if term_violations:
        issues.append({"code": "LOCKED_TERM_VIOLATION", "message": f"LOCKED_TERM_VIOLATION count={len(term_violations)}", "samples": term_violations[:10]})
    if quality_lock_violations:
        issues.append({"code": "QUALITY_LOCK_VIOLATION", "message": f"QUALITY_LOCK_VIOLATION count={len(quality_lock_violations)}", "samples": quality_lock_violations[:10]})

    # Calculate literary quality metrics based on severity applied to naturalness hits
    if naturalness_hits and (policy.naturalness_guard_policy or "warn").lower() != "off":
        retryable_hits = _retryable_naturalness_hits(policy, naturalness_hits)
        lit_severity = "error" if retryable_hits else "warning"
        lit_errors = lit_classification["literary_quality_hit_count"] if lit_severity == "error" else 0
        lit_warnings = lit_classification["literary_quality_hit_count"] if lit_severity == "warning" else 0
    else:
        lit_errors = 0
        lit_warnings = 0

    return {
        "passed": not any(issue.get("severity", "error") == "error" for issue in issues),
        "enabled": True,
        "issues": issues,
        "metrics": {
            "source_chars": source_len,
            "translated_chars": translated_len,
            "length_ratio": round(length_ratio, 4),
            "korean_chars": korean_chars,
            "repeated_line_count": len(repeated_lines),
            "repeated_sentence_count": len(repeated_sentences),
            "simplified_hits": len(simplified_hits),
            "dialogue_quote_violations": len(dialogue_quote_hits),
            "naturalness_violations": len(naturalness_hits),
            "locked_term_violations": len(term_violations),
            "quality_lock_violations": len(quality_lock_violations),
            "literary_quality_hits": lit_classification["literary_quality_hit_count"],
            "literary_quality_errors": lit_errors,
            "literary_quality_warnings": lit_warnings,
            "literary_quality_passed": lit_errors == 0,
            "literary_quality_issue_codes": [h.get("code") for h in lit_classification["literary_quality_hits"]],
        },
    }


def _naturalness_severity(policy: RuntimeQAPolicy) -> str:
    guard_policy = (policy.naturalness_guard_policy or "warn").lower()
    if guard_policy == "fail":
        return "error"
    if guard_policy == "literary_retry" and (policy.quality_profile or "").lower() in {"literary", "novel", "premium", "quality"}:
        return "error"
    return "warning"


def _retryable_naturalness_hits(policy: RuntimeQAPolicy, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guard_policy = (policy.naturalness_guard_policy or "warn").lower()
    if guard_policy in {"off", "warn"}:
        return []
    if guard_policy == "fail":
        return hits
    if guard_policy == "quality_retry":
        return hits if (policy.quality_profile or "").lower() in {"quality", "premium"} else []
    if guard_policy == "literary_retry":
        return hits if _naturalness_severity(policy) == "error" else []
    if guard_policy == "high_confidence_only":
        return [hit for hit in hits if hit.get("confidence") == "high"]
    return []


def classify_literary_quality_hits(naturalness_hits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Split naturalness_hits into literary-quality vs other.
    Pure function, no side effects, deterministic.
    """
    lit = [h for h in naturalness_hits if h.get("code") in _LITERARY_QUALITY_CODES]
    other = [h for h in naturalness_hits if h.get("code") not in _LITERARY_QUALITY_CODES]
    return {
        "literary_quality_hits": lit,
        "other_naturalness_hits": other,
        "literary_quality_hit_count": len(lit),
    }


def should_soft_fail_naturalness(qa_report: Mapping[str, Any], speed: str | None) -> bool:
    """Return True when final QA failure is only balanced-mode naturalness."""
    if str(speed or "").strip().lower() != "balanced":
        return False
    issues = qa_report.get("issues", []) if isinstance(qa_report, Mapping) else []
    naturalness_errors = 0
    hard_errors = 0
    for issue in issues if isinstance(issues, list) else []:
        if not isinstance(issue, Mapping):
            continue
        if issue.get("severity", "error") != "error":
            continue
        if issue.get("code") == NATURALNESS_GUARD_CODE:
            naturalness_errors += 1
        else:
            hard_errors += 1
    return naturalness_errors > 0 and hard_errors == 0


def soft_fail_naturalness_report(qa_report: Mapping[str, Any], speed: str | None) -> dict[str, Any]:
    """Downgrade balanced naturalness-only final QA failure to a warning report."""
    report = dict(qa_report)
    if not should_soft_fail_naturalness(report, speed):
        return report
    downgraded_issues: list[Any] = []
    issues = report.get("issues", [])
    for issue in issues if isinstance(issues, list) else []:
        if isinstance(issue, Mapping) and issue.get("code") == NATURALNESS_GUARD_CODE:
            item = dict(issue)
            item["severity"] = "warning"
            item["retry_worthy"] = False
            item["soft_failed"] = True
            downgraded_issues.append(item)
        else:
            downgraded_issues.append(issue)
    report["issues"] = downgraded_issues
    report["passed"] = True
    report["status"] = "pass_with_warning"
    report["passed_with_warning"] = True
    return report
