from __future__ import annotations

from dataclasses import dataclass

KOREAN_MARKER = "\u3010Korean\u3011"
OUTPUT_MARKER = "\u3010Output\u3011"
REFERENCE_START = "[Translation Reference - Do Not Output]"
REFERENCE_END = "[End Translation Reference]"
_FORBIDDEN = (("korean-marker", KOREAN_MARKER), ("output-marker", OUTPUT_MARKER), ("translation-label", "\u8b6f\u6587\uff1a"), ("source-label", "source:"), ("translation-label-ascii", "translation:"), ("role-system", "<system"), ("role-user", "<user"), ("role-assistant", "<assistant"))

@dataclass(frozen=True)
class PromptContractVerification:
    valid: bool
    violations: tuple[str, ...]
    source_marker_present: bool
    output_marker_present: bool
    source_exactly_preserved: bool
    source_immediately_follows_korean_marker: bool
    output_immediately_follows_source: bool
    no_dynamic_section_inside_source_boundary: bool
    translation_contract_present: bool
    reference_container_before_source: bool
    reference_container_closed_before_korean_marker: bool
    no_forbidden_output_label_in_prompt_template: bool
    def to_dict(self) -> dict[str, object]:
        data = {key: getattr(self, key) for key in self.__dataclass_fields__}
        data["violations"] = list(self.violations)
        return data

def render_reference_container(section: str) -> str:
    return "\n".join((REFERENCE_START, "The following information is reference-only.", "Do not quote, copy, explain, summarize, or reproduce it.", "Do not output section labels or source-language text.", "Use it only to improve the Traditional Chinese translation.", "", section, REFERENCE_END))

def scan_dynamic_section(section: str, source_text: str) -> tuple[str, ...]:
    lowered = section.casefold()
    violations = [name for name, token in _FORBIDDEN if token.casefold() in lowered]
    if source_text and source_text in section:
        violations.append("exact-source-in-reference")
    return tuple(violations)

def serialize_candidate_prompt(base_prompt: str, source_text: str, reference_section: str) -> tuple[str, PromptContractVerification]:
    violations = list(scan_dynamic_section(reference_section, source_text))
    boundary = f"{KOREAN_MARKER}\n{source_text}\n{OUTPUT_MARKER}"
    if base_prompt.count(boundary) != 1:
        violations.append("source-boundary-unavailable")
        return base_prompt, _verify(base_prompt, source_text, tuple(violations), reference_expected=False)
    candidate = base_prompt.replace(boundary, f"{render_reference_container(reference_section)}\n{boundary}", 1)
    return candidate, _verify(candidate, source_text, tuple(violations), reference_expected=True)

def verify_candidate_prompt(prompt: str, source_text: str) -> PromptContractVerification:
    return _verify(prompt, source_text, (), reference_expected=True)

def _verify(prompt: str, source_text: str, initial: tuple[str, ...], *, reference_expected: bool) -> PromptContractVerification:
    source_boundary = f"{KOREAN_MARKER}\n{source_text}\n{OUTPUT_MARKER}"
    source_at = prompt.find(source_boundary)
    reference_start = prompt.find(REFERENCE_START)
    reference_end = prompt.find(REFERENCE_END)
    values = {
        "source_marker_present": KOREAN_MARKER in prompt,
        "output_marker_present": OUTPUT_MARKER in prompt,
        "source_exactly_preserved": prompt.count(source_text) == 1,
        "source_immediately_follows_korean_marker": source_boundary in prompt,
        "output_immediately_follows_source": source_boundary in prompt,
        "no_dynamic_section_inside_source_boundary": source_boundary in prompt,
        "translation_contract_present": "\u53ea\u8f38\u51fa\u7e41\u9ad4\u4e2d\u6587\u8b6f\u6587" in prompt,
        "reference_container_before_source": reference_start >= 0 and reference_start < source_at,
        "reference_container_closed_before_korean_marker": reference_end >= 0 and reference_end < source_at,
        "no_forbidden_output_label_in_prompt_template": not any(token in prompt for _, token in _FORBIDDEN[2:5]),
    }
    checks = dict(values)
    if not reference_expected:
        checks.pop("reference_container_before_source")
        checks.pop("reference_container_closed_before_korean_marker")
    names = {"source_marker_present": "source-marker-missing", "output_marker_present": "output-marker-missing", "source_exactly_preserved": "source-not-exactly-preserved", "source_immediately_follows_korean_marker": "source-boundary-not-contiguous", "output_immediately_follows_source": "output-not-contiguous", "no_dynamic_section_inside_source_boundary": "dynamic-content-inside-source-boundary", "translation_contract_present": "translation-contract-missing", "reference_container_before_source": "reference-not-before-source", "reference_container_closed_before_korean_marker": "reference-not-closed-before-source", "no_forbidden_output_label_in_prompt_template": "forbidden-output-label"}
    violations = tuple(dict.fromkeys((*initial, *(names[key] for key, passed in checks.items() if not passed))))
    return PromptContractVerification(valid=not violations, violations=violations, **values)
