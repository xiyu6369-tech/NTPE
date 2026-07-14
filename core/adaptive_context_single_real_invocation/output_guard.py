from __future__ import annotations

import re

from .model import OutputGuardResult

_HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
_REFUSALS = (
    "i can't assist", "i cannot assist", "unable to comply",
    "cannot provide", "죄송하지만", "도와드릴 수 없습니다",
)


def inspect_translation_output(
    output: object, *, source_length: int,
) -> OutputGuardResult:
    response_format_invalid = not isinstance(output, str)
    text = output.strip() if isinstance(output, str) else ""
    empty = not text
    minimum = max(80, int(max(0, source_length) * 0.15))
    short = bool(text) and len(text) < minimum
    hangul_count = len(_HANGUL.findall(text))
    hangul_signal = hangul_count >= 20 or (
        bool(text) and hangul_count / max(1, len(text)) >= 0.1
    )
    truncated = bool(text) and text.rstrip().endswith(("...", "…", "―", "--"))
    lowered = text.casefold()
    refusal = any(marker in lowered for marker in _REFUSALS)
    accepted = not any((
        response_format_invalid, empty, short, hangul_signal, truncated, refusal,
    ))
    return OutputGuardResult(
        accepted_for_human_review=accepted,
        empty_output=empty,
        suspicious_short_output=short,
        hangul_residue_signal=hangul_signal,
        obvious_truncation=truncated,
        response_format_invalid=response_format_invalid,
        provider_refusal=refusal,
    )
