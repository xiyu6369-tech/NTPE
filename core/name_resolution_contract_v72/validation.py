from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .models import NameResolutionRecord
from .normalization import contains_hangul, contains_han, contains_latin


@dataclass(frozen=True)
class NameValidationResult:
    classifications: tuple[str, ...]
    failure_subtypes: tuple[str, ...]
    residuals: tuple[str, ...]
    approved_name_violations: tuple[dict[str, str], ...]
    mixed_language_inline_output: bool
    validate_only: bool = True
    repair_applied: bool = False
    provider_request: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "classifications": list(self.classifications),
            "failure_subtypes": list(self.failure_subtypes),
            "residuals": list(self.residuals),
            "approved_name_violations": list(self.approved_name_violations),
            "mixed_language_inline_output": self.mixed_language_inline_output,
            "validate_only": self.validate_only, "repair_applied": self.repair_applied,
            "provider_request": self.provider_request,
        }


def validate_name_output(
    output: str,
    *,
    source_text: str,
    records: Iterable[NameResolutionRecord],
) -> NameValidationResult:
    classifications: list[str] = []
    subtypes: list[str] = []
    residuals = re.findall(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]+", output)
    if source_text.strip() and source_text.strip() in output:
        classifications.append("source_echo")
    record_tuple = tuple(records)
    full_names = [item.source_name for item in record_tuple if item.source_name and item.source_name in output]
    if residuals:
        classifications.append("lexical_hangul_residual")
    if full_names:
        classifications.append("proper_name_hangul_residual")
        subtypes.append("full_hangul_proper_name_residual")
    mixed_tokens = re.findall(
        r"(?:[\u3400-\u9fffA-Za-z]+[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]+|"
        r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]+[\u3400-\u9fffA-Za-z]+)",
        output,
    )
    if mixed_tokens:
        classifications.extend(("partial_name_normalization", "mixed_script_proper_name"))
        for token in mixed_tokens:
            if contains_han(token) and contains_hangul(token): subtypes.append("mixed_han_hangul_name")
            if contains_latin(token) and contains_hangul(token): subtypes.append("mixed_latin_hangul_name")
    violations: list[dict[str, str]] = []
    for record in record_tuple:
        if record.prompt_eligible and record.approved_zh_hant_name:
            if record.source_name in output or (
                record.source_name in source_text and record.approved_zh_hant_name not in output
            ):
                violations.append({
                    "source_name": record.source_name,
                    "approved_name": record.approved_zh_hant_name,
                    "reason": "approved_name_mapping_violation",
                })
    if violations: classifications.append("approved_name_mapping_violation")
    unsafe_unresolved = [
        item.source_name for item in record_tuple
        if not item.prompt_eligible and any(residual in item.source_name for residual in residuals)
    ]
    if unsafe_unresolved: classifications.append("unresolved_name_unsafe_rendering")
    return NameValidationResult(
        tuple(dict.fromkeys(classifications)), tuple(dict.fromkeys(subtypes)),
        tuple(residuals), tuple(violations), bool(residuals and re.search(r"[\u3400-\u9fff]", output)),
    )
