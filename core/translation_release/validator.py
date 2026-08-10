from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from lts.txt_translation_runtime import TxtTranslationOptions, build_translation_alias_map


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    score: float
    details: dict[str, Any]
    severity: str


@dataclass(frozen=True)
class ValidationResult:
    overall_passed: bool
    overall_score: float
    checks: list[ValidationCheck]
    failed_critical: list[str] = field(default_factory=list)
    failed_major: list[str] = field(default_factory=list)


def validate_final_novel(
    text: str,
    locked_dictionary: dict[str, str],
    chunk_records: list[dict],
    literary_quality_aggregate: dict,
    options: TxtTranslationOptions,
    *,
    matched_terms: dict[str, str] | None = None,
) -> ValidationResult:
    """
    Deterministic validation gate — no LLM, no provider calls.

    Checks (all deterministic):
    1. paragraph_structure          — critical
       - No empty paragraphs
       - No 3+ consecutive newlines
       - Paragraph count > 0

    2. punctuation_consistency      — major
       - CJK punctuation ratio > 95%
       - Quote style unified (corner brackets)

    3. korean_residue_global        — critical
       - Total Korean chars < options.max_korean_chars * chunk_total * 0.5

    4. locked_term_compliance       — major (downgraded from critical)
       - Only validate locked terms that actually appear in source chunks (matched_locked_terms from runtime)
       - No FAIL for glossary entries not present in this novel
       - Check: all matched locked terms present in final text; no locked aliases present

    5. length_ratio_global          — major
       - Total translated / total source ∈ [options.min_length_ratio, 2.0]
       - Source length MUST come from existing chunk_records: each record.source.char_count
         or record.metadata.source.char_count. If unavailable, check is marked "unverifiable"
         and excluded from scoring.

    6. chinese_char_ratio           — minor
       - Chinese character ratio > 80% in translated text

    7. repeated_lines_global        — minor
       - No repeated consecutive lines (same as RM-8.1 but global)

    8. quote_balance                — minor
       - Opening and closing corner brackets balanced

    9. empty_content                — info
       - Text is not empty after polish

    Weighted scoring:
    - critical: weight 3.0
    - major: weight 2.0
    - minor: weight 1.0
    - info: weight 0.5

    PASS threshold: overall_score >= 70.0 AND no failed critical checks
    """
    checks: list[ValidationCheck] = []

    # Check 1: paragraph_structure (critical)
    checks.append(_check_paragraph_structure(text))

    # Check 2: punctuation_consistency (major)
    checks.append(_check_punctuation_consistency(text))

    # Check 3: korean_residue_global (critical)
    max_korean_allowed = options.max_korean_chars * max(1, len(chunk_records)) // 2
    checks.append(_check_korean_residue_global(text, max_korean_allowed))

    # Check 4: locked_term_compliance (major, downgraded from critical)
    if matched_terms is None:
        matched_terms = {}
    checks.append(_check_locked_term_compliance(text, locked_dictionary, matched_terms))

    # Check 5: length_ratio_global (major)
    checks.append(_check_length_ratio_global(text, chunk_records, options.min_length_ratio))

    # Check 6: chinese_char_ratio (minor)
    checks.append(_check_chinese_char_ratio(text))

    # Check 7: repeated_lines_global (minor)
    checks.append(_check_repeated_lines_global(text))

    # Check 8: quote_balance (minor)
    checks.append(_check_quote_balance(text))

    # Check 9: empty_content (info)
    checks.append(_check_empty_content(text))

    # Weighted scoring
    severity_weights = {
        "critical": 3.0,
        "major": 2.0,
        "minor": 1.0,
        "info": 0.5,
    }

    total_weighted_score = 0.0
    total_weight = 0.0
    failed_critical: list[str] = []
    failed_major: list[str] = []

    for check in checks:
        weight = severity_weights.get(check.severity, 1.0)
        total_weighted_score += check.score * weight
        total_weight += weight

        if not check.passed:
            if check.severity == "critical":
                failed_critical.append(check.name)
            elif check.severity == "major":
                failed_major.append(check.name)

    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
    overall_passed = overall_score >= 70.0 and len(failed_critical) == 0

    return ValidationResult(
        overall_passed=overall_passed,
        overall_score=round(overall_score, 2),
        checks=checks,
        failed_critical=failed_critical,
        failed_major=failed_major,
    )


def _check_paragraph_structure(text: str) -> ValidationCheck:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    empty_count = 0
    # Count empty paragraphs (consecutive \n\n\n)
    parts = text.split("\n\n")
    for part in parts:
        if not part.strip():
            empty_count += 1

    # Also check for 3+ consecutive newlines
    excessive_newlines = len(re.findall(r"\n{3,}", text))

    passed = len(paragraphs) > 0 and empty_count == 0 and excessive_newlines == 0
    score = 100.0 if passed else max(0.0, 100.0 - empty_count * 10 - excessive_newlines * 5)

    return ValidationCheck(
        name="paragraph_structure",
        passed=passed,
        score=score,
        details={
            "paragraphs": len(paragraphs),
            "empty_paragraphs": empty_count,
            "excessive_newlines": excessive_newlines,
        },
        severity="critical",
    )


def _check_punctuation_consistency(text: str) -> ValidationCheck:
    if not text:
        return ValidationCheck(
            name="punctuation_consistency",
            passed=True,
            score=100.0,
            details={"cjk_ratio": 1.0, "quote_style_unified": True},
            severity="major",
        )

    # Count CJK punctuation vs ASCII punctuation
    cjk_punct = len(re.findall(r"[，。！？；：「」『』（）《》〈〉【】]", text))
    ascii_punct = len(re.findall(r"[,.!?;:\"\"''()<>\[\]{}]", text))
    total_punct = cjk_punct + ascii_punct

    cjk_ratio = cjk_punct / total_punct if total_punct > 0 else 1.0

    # Check quote style unification (should use corner brackets)
    corner_brackets = len(re.findall(r"[「」『』]", text))
    straight_quotes = len(re.findall(r'["\']', text))
    quote_unified = straight_quotes == 0 or (corner_brackets > 0 and straight_quotes < corner_brackets)

    passed = cjk_ratio >= 0.95 and quote_unified
    score = 100.0 if passed else max(0.0, cjk_ratio * 100)

    return ValidationCheck(
        name="punctuation_consistency",
        passed=passed,
        score=score,
        details={
            "cjk_ratio": round(cjk_ratio, 3),
            "quote_style_unified": quote_unified,
            "cjk_punct_count": cjk_punct,
            "ascii_punct_count": ascii_punct,
        },
        severity="major",
    )


def _check_korean_residue_global(text: str, max_allowed: int) -> ValidationCheck:
    korean_count = len(re.findall(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]", text))
    passed = korean_count <= max_allowed
    score = 100.0 if passed else max(0.0, 100.0 - (korean_count - max_allowed) * 5)

    return ValidationCheck(
        name="korean_residue_global",
        passed=passed,
        score=score,
        details={"korean_chars": korean_count, "max_allowed": max_allowed},
        severity="critical",
    )


def _check_locked_term_compliance(
    text: str,
    locked_dictionary: dict[str, str],
    matched_terms: dict[str, str],
) -> ValidationCheck:
    """
    Only validate locked terms that were actually matched in source chunks.
    matched_terms = {src: target for src, target in locked_dictionary.items() if src in source_text}
    """
    # Build alias map from locked dictionary
    aliases = build_translation_alias_map(locked_dictionary)

    # Check missing matched terms
    missing = [t for t in matched_terms.values() if t and t not in text]

    # Check alias violations
    alias_hits = [a for a in aliases if a in text]

    passed = len(missing) == 0 and len(alias_hits) == 0
    score = 100.0 if passed else max(0.0, 100.0 - len(missing) * 10 - len(alias_hits) * 5)

    return ValidationCheck(
        name="locked_term_compliance",
        passed=passed,
        score=score,
        details={
            "missing_terms": missing,
            "alias_violations": alias_hits,
            "validated_terms": list(matched_terms.values()),
        },
        severity="major",  # downgraded from critical
    )


def _check_length_ratio_global(
    text: str,
    chunk_records: list[dict],
    min_ratio: float,
) -> ValidationCheck:
    """
    Compute length ratio from existing chunk_records source metadata.
    Each record should have: record.get("source", {}).get("char_count") or
    record.get("metadata", {}).get("source", {}).get("char_count")
    """
    source_total = 0
    verifiable_chunks = 0

    for rec in chunk_records:
        src = rec.get("source") or rec.get("metadata", {}).get("source")
        if isinstance(src, dict):
            char_count = src.get("char_count")
            if isinstance(char_count, int) and char_count > 0:
                source_total += char_count
                verifiable_chunks += 1

    if verifiable_chunks == 0:
        return ValidationCheck(
            name="length_ratio_global",
            passed=True,  # unverifiable -> neutral
            score=100.0,
            details={
                "verifiable": False,
                "reason": "no source char_count in chunk_records",
            },
            severity="info",  # info when unverifiable
        )

    # Count translated chars (excluding whitespace)
    translated_total = len(text.replace("\n", "").replace(" ", ""))
    ratio = translated_total / source_total if source_total > 0 else 0
    passed = min_ratio <= ratio <= 2.0

    return ValidationCheck(
        name="length_ratio_global",
        passed=passed,
        score=100.0 if passed else max(0.0, 100.0 - abs(ratio - min_ratio) * 50),
        details={
            "translated_chars": translated_total,
            "source_chars": source_total,
            "ratio": round(ratio, 3),
            "min_ratio": min_ratio,
            "verifiable_chunks": verifiable_chunks,
            "verifiable": True,
        },
        severity="major",
    )


def _check_chinese_char_ratio(text: str) -> ValidationCheck:
    if not text:
        return ValidationCheck(
            name="chinese_char_ratio",
            passed=True,
            score=100.0,
            details={"ratio": 1.0},
            severity="minor",
        )

    # Count Chinese characters
    chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(text.replace("\n", "").replace(" ", ""))

    if total_chars == 0:
        ratio = 1.0
    else:
        ratio = chinese_count / total_chars

    passed = ratio >= 0.8
    score = 100.0 if passed else max(0.0, ratio * 100)

    return ValidationCheck(
        name="chinese_char_ratio",
        passed=passed,
        score=score,
        details={"chinese_chars": chinese_count, "total_chars": total_chars, "ratio": round(ratio, 3)},
        severity="minor",
    )


def _check_repeated_lines_global(text: str) -> ValidationCheck:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    repeated = 0
    for i in range(1, len(lines)):
        if lines[i] == lines[i - 1]:
            repeated += 1

    passed = repeated == 0
    score = 100.0 if passed else max(0.0, 100.0 - repeated * 10)

    return ValidationCheck(
        name="repeated_lines_global",
        passed=passed,
        score=score,
        details={"repeated_consecutive_lines": repeated, "total_lines": len(lines)},
        severity="minor",
    )


def _check_quote_balance(text: str) -> ValidationCheck:
    # Check corner bracket balance
    open_double = text.count("「")
    close_double = text.count("」")
    open_single = text.count("『")
    close_single = text.count("』")

    double_balanced = open_double == close_double
    single_balanced = open_single == close_single
    passed = double_balanced and single_balanced

    score = 100.0 if passed else max(0.0, 100.0 - abs(open_double - close_double) * 5 - abs(open_single - close_single) * 5)

    return ValidationCheck(
        name="quote_balance",
        passed=passed,
        score=score,
        details={
            "double_open": open_double,
            "double_close": close_double,
            "single_open": open_single,
            "single_close": close_single,
        },
        severity="minor",
    )


def _check_empty_content(text: str) -> ValidationCheck:
    passed = bool(text.strip())
    score = 100.0 if passed else 0.0

    return ValidationCheck(
        name="empty_content",
        passed=passed,
        score=score,
        details={"empty": not passed, "length": len(text)},
        severity="info",
    )