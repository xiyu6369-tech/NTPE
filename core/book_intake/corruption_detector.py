from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# Thresholds — centralized, no magic numbers
# =============================================================================

_REPLACEMENT_CHARACTER = "\uFFFD"
_NULL_CHARACTER = "\x00"
_ALLOWED_CONTROL_CHARS = frozenset({"\n", "\r", "\t"})
_PRIVATE_USE_AREA_RANGES = (
    (0xE000, 0xF8FF),   # BMP PUA
    (0xF0000, 0xFFFFD), # Supplementary PUA-A
    (0x100000, 0x10FFFD), # Supplementary PUA-B
)
_NONCHARACTER_CODEPOINTS = frozenset(
    [0xFDD0 + i for i in range(0, 16)]  # U+FDD0..U+FDEF
    + [0xFFFE, 0xFFFF]                   # U+FFFE, U+FFFF
    + [0x1FFFE, 0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE, 0x3FFFF,
       0x4FFFE, 0x4FFFF, 0x5FFFE, 0x5FFFF, 0x6FFFE, 0x6FFFF,
       0x7FFFE, 0x7FFFF, 0x8FFFE, 0x8FFFF, 0x9FFFE, 0x9FFFF,
       0xAFFFE, 0xAFFFF, 0xBFFFE, 0xBFFFF, 0xCFFFE, 0xCFFFF,
       0xDFFFE, 0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE, 0xFFFFF]
)
_SURROGATE_RANGE = (0xD800, 0xDFFF)
_UNPRINTABLE_RATIO_WARN = 0.15
_UNPRINTABLE_RATIO_CRITICAL = 0.30
_LONG_LINE_LENGTH = 20000
_MOJIBAKE_PATTERNS = (
    "\u00C3",   # Ã
    "\u00C2",   # Â
    "\u00A4",   # ¤
    "\u00A5",   # ¥
    "\uFFE6",   # ￦
    "\u00B8",   # ¸
    "\u00A8",   # ¨
    "\u00B4",   # ´
)
_MOJIBAKE_REPEATED_THRESHOLD = 3
_ABNORMAL_REPEAT_CHARS = frozenset({"\uFFFD", "\u25A1", "\u25A0", "\uC73B", "\uC6D0"})
_ABNORMAL_REPEAT_MIN_COUNT = 4

# Score deduction weights
_SCORE_DEDUCTION_REPLACEMENT = 1       # per char (high frequency -> subtract more)
_SCORE_DEDUCTION_NULL = 2              # per char
_SCORE_DEDUCTION_CONTROL = 1           # per char
_SCORE_DEDUCTION_PUA = 1              # per char
_SCORE_DEDUCTION_NONCHARACTER = 3      # per char
_SCORE_DEDUCTION_SURROGATE = 5        # per char
_SCORE_DEDUCTION_UNPRINTABLE_RATIO_WARN = 15
_SCORE_DEDUCTION_UNPRINTABLE_RATIO_CRITICAL = 30
_SCORE_DEDUCTION_MOJIBAKE = 20
_SCORE_DEDUCTION_ABNORMAL_REPEAT = 25
_SCORE_DEDUCTION_LONG_LINE = 10


# =============================================================================
# Immutable Finding
# =============================================================================

@dataclass(frozen=True)
class Finding:
    """A single corruption or quality finding."""

    code: str
    severity: str
    count: int
    message: str


# =============================================================================
# Immutable TextQualityReport
# =============================================================================

@dataclass(frozen=True)
class TextQualityReport:
    """Immutable quality report produced by TextCorruptionDetector."""

    status: str
    findings: tuple[Finding, ...]
    score: int
    recommended_action: str
    summary: str


# =============================================================================
# TextCorruptionDetector
# =============================================================================

class TextCorruptionDetector:
    """Pure offline text quality analyzer — detects corruption / garbled text."""

    def analyze(self, text: str) -> TextQualityReport:
        """Analyze *text* and return a frozen TextQualityReport."""
        if not text:
            return TextQualityReport(
                status="clean",
                findings=(),
                score=100,
                recommended_action="accept",
                summary="Empty input; no corruption detected.",
            )

        findings: list[Finding] = []
        score = 100

        # 1. Replacement character
        f_replacement = _detect_replacement_characters(text)
        if f_replacement:
            findings.append(f_replacement)
            score -= min(score, f_replacement.count * _SCORE_DEDUCTION_REPLACEMENT)

        # 2. NULL character
        f_null = _detect_null_characters(text)
        if f_null:
            findings.append(f_null)
            score -= min(score, f_null.count * _SCORE_DEDUCTION_NULL)

        # 3. Control characters (excluding \n, \r, \t)
        f_control = _detect_control_characters(text)
        if f_control:
            findings.append(f_control)
            score -= min(score, f_control.count * _SCORE_DEDUCTION_CONTROL)

        # 4. Private Use Area
        f_pua = _detect_private_use_area(text)
        if f_pua:
            findings.append(f_pua)
            score -= min(score, f_pua.count * _SCORE_DEDUCTION_PUA)

        # 5. Noncharacter
        f_nonchar = _detect_noncharacters(text)
        if f_nonchar:
            findings.append(f_nonchar)
            score -= min(score, f_nonchar.count * _SCORE_DEDUCTION_NONCHARACTER)

        # 6. Surrogate code points
        f_surrogate = _detect_surrogate_code_points(text)
        if f_surrogate:
            findings.append(f_surrogate)
            score -= min(score, f_surrogate.count * _SCORE_DEDUCTION_SURROGATE)

        # 7. Unprintable character ratio
        f_unprintable = _detect_unprintable_ratio(text)
        if f_unprintable:
            findings.append(f_unprintable)
            if f_unprintable.severity == "error":
                score -= _SCORE_DEDUCTION_UNPRINTABLE_RATIO_CRITICAL
            else:
                score -= _SCORE_DEDUCTION_UNPRINTABLE_RATIO_WARN

        # 8. Mojibake pattern
        f_mojibake = _detect_mojibake(text)
        if f_mojibake:
            findings.append(f_mojibake)
            score -= _SCORE_DEDUCTION_MOJIBAKE

        # 9. Abnormal repeated symbols
        f_repeat = _detect_abnormal_repeated_symbols(text)
        if f_repeat:
            findings.append(f_repeat)
            score -= _SCORE_DEDUCTION_ABNORMAL_REPEAT

        # 10. Long line
        f_longline = _detect_long_lines(text)
        if f_longline:
            findings.append(f_longline)
            score -= _SCORE_DEDUCTION_LONG_LINE

        score = max(score, 0)

        status = _determine_status(findings)
        recommended_action = _determine_action(status)
        summary = _build_summary(findings)

        return TextQualityReport(
            status=status,
            findings=tuple(findings),
            score=score,
            recommended_action=recommended_action,
            summary=summary,
        )


# =============================================================================
# Internal detection helpers
# =============================================================================

def _detect_replacement_characters(text: str) -> Finding | None:
    count = text.count(_REPLACEMENT_CHARACTER)
    if count == 0:
        return None
    return Finding(
        code="replacement_character",
        severity="warning",
        count=count,
        message=f"Found {count} replacement character(s).",
    )


def _detect_null_characters(text: str) -> Finding | None:
    count = text.count(_NULL_CHARACTER)
    if count == 0:
        return None
    return Finding(
        code="null_character",
        severity="error",
        count=count,
        message=f"Found {count} NULL character(s).",
    )


def _detect_control_characters(text: str) -> Finding | None:
    count = 0
    for ch in text:
        cp = ord(ch)
        if cp < 0x20 and ch not in _ALLOWED_CONTROL_CHARS:
            count += 1
    if count == 0:
        return None
    severity = "error" if count > 10 else "warning"
    return Finding(
        code="control_character",
        severity=severity,
        count=count,
        message=f"Found {count} control character(s) (excluding \\n, \\r, \\t).",
    )


def _is_private_use(cp: int) -> bool:
    for lo, hi in _PRIVATE_USE_AREA_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def _detect_private_use_area(text: str) -> Finding | None:
    count = sum(1 for ch in text if _is_private_use(ord(ch)))
    if count == 0:
        return None
    severity = "error" if count > 100 else "warning"
    return Finding(
        code="private_use_area",
        severity=severity,
        count=count,
        message=f"Found {count} Private Use Area character(s).",
    )


def _is_noncharacter(cp: int) -> bool:
    return cp in _NONCHARACTER_CODEPOINTS


def _detect_noncharacters(text: str) -> Finding | None:
    count = sum(1 for ch in text if _is_noncharacter(ord(ch)))
    if count == 0:
        return None
    return Finding(
        code="noncharacter",
        severity="error",
        count=count,
        message=f"Found {count} noncharacter code point(s).",
    )


def _is_surrogate(cp: int) -> bool:
    lo, hi = _SURROGATE_RANGE
    return lo <= cp <= hi


def _detect_surrogate_code_points(text: str) -> Finding | None:
    count = sum(1 for ch in text if _is_surrogate(ord(ch)))
    if count == 0:
        return None
    return Finding(
        code="surrogate_code_point",
        severity="error",
        count=count,
        message=f"Found {count} surrogate code point(s).",
    )


def _is_printable(cp: int) -> bool:
    # Common printable categories: L (Letter), N (Number), P (Punctuation),
    # S (Symbol), Zs (Space separator), plus common whitespace \n \r \t
    # Also allow newline, carriage return, tab as printable.
    import unicodedata
    cat = unicodedata.category(chr(cp))
    if cat.startswith("L") or cat.startswith("N") or cat.startswith("P") or cat.startswith("S"):
        return True
    if cat == "Zs":
        return True
    if chr(cp) in _ALLOWED_CONTROL_CHARS:
        return True
    return False


def _detect_unprintable_ratio(text: str) -> Finding | None:
    total = len(text)
    if total == 0:
        return None
    unprintable = sum(1 for ch in text if not _is_printable(ord(ch)))
    ratio = unprintable / total
    if ratio >= _UNPRINTABLE_RATIO_CRITICAL:
        return Finding(
            code="unprintable_ratio",
            severity="error",
            count=unprintable,
            message=f"High unprintable character ratio: {ratio:.2%} ({unprintable}/{total}).",
        )
    if ratio >= _UNPRINTABLE_RATIO_WARN:
        return Finding(
            code="unprintable_ratio",
            severity="warning",
            count=unprintable,
            message=f"Elevated unprintable character ratio: {ratio:.2%} ({unprintable}/{total}).",
        )
    return None


def _detect_mojibake(text: str) -> Finding | None:
    # Accumulate evidence: count of mojibake-indicator characters
    indicator_count = sum(text.count(p) for p in _MOJIBAKE_PATTERNS)
    if indicator_count == 0:
        return None

    # Check for clustered patterns (repeated + proximity)
    # Use a sliding window approach: if we see > threshold mojibake chars
    # within a short span, it's a strong signal.
    found_patterns: list[str] = []
    total_mojibake_hits = 0
    for i, ch in enumerate(text):
        if ch in _MOJIBAKE_PATTERNS:
            total_mojibake_hits += 1
            # Count consecutive mojibake chars
            consecutive = 1
            j = i + 1
            while j < len(text) and text[j] in _MOJIBAKE_PATTERNS:
                consecutive += 1
                j += 1
            if consecutive >= _MOJIBAKE_REPEATED_THRESHOLD:
                snippet = text[i : i + consecutive]
                found_patterns.append(snippet)

    severity = "error" if found_patterns else ("warning" if indicator_count > 0 else None)
    if severity is None:
        return None

    return Finding(
        code="mojibake_pattern",
        severity=severity,
        count=total_mojibake_hits,
        message=f"Detected mojibake indicators: {total_mojibake_hits} suspicious character(s).",
    )


def _detect_abnormal_repeated_symbols(text: str) -> Finding | None:
    # Look for runs of specific abnormal chars
    found_sequences: list[tuple[str, int]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in _ABNORMAL_REPEAT_CHARS:
            run = 1
            j = i + 1
            while j < len(text) and text[j] == ch:
                run += 1
                j += 1
            if run >= _ABNORMAL_REPEAT_MIN_COUNT:
                found_sequences.append((ch, run))
            i = j
        else:
            i += 1
    if not found_sequences:
        return None
    total_runs = sum(r for _, r in found_sequences)
    return Finding(
        code="abnormal_repeated_symbol",
        severity="warning",
        count=total_runs,
        message=f"Found {len(found_sequences)} run(s) of abnormal repeated symbols.",
    )


def _detect_long_lines(text: str) -> Finding | None:
    lines = text.splitlines(keepends=False)
    long_lines = [ln for ln in lines if len(ln) > _LONG_LINE_LENGTH]
    if not long_lines:
        return None
    return Finding(
        code="long_line",
        severity="warning",
        count=len(long_lines),
        message=f"Found {len(long_lines)} line(s) exceeding {_LONG_LINE_LENGTH} characters.",
    )


def _determine_status(findings: list[Finding]) -> str:
    severities = {f.severity for f in findings}
    if not findings:
        return "clean"
    if "error" in severities:
        return "blocked" if len(findings) >= 3 else "manual_review_required"
    if "warning" in severities:
        return "warning"
    return "clean"


def _determine_action(status: str) -> str:
    mapping = {
        "clean": "accept",
        "warning": "accept_with_warning",
        "manual_review_required": "manual_review",
        "blocked": "reject",
    }
    return mapping.get(status, "accept")


def _build_summary(findings: list[Finding]) -> str:
    if not findings:
        return "No corruption detected."
    parts = [f.message for f in findings]
    if len(parts) > 3:
        return f"Multiple issues detected ({len(parts)} findings)."
    return " ".join(parts)