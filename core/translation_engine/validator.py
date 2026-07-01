"""Translation validation layer."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import re


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "warning"

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class ValidationResult:
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"passed": self.passed, "issues": [i.to_dict() for i in self.issues], "metadata": dict(self.metadata)}


class TranslationValidator:
    def __init__(self, min_length_ratio: float = 0.05):
        self.min_length_ratio = min_length_ratio

    def validate(self, source: Any, translated: Any, context: Dict[str, Any] | None = None) -> ValidationResult:
        src = str(source or "")
        out = self._extract_text(translated)
        issues: List[ValidationIssue] = []
        if src.strip() and not out.strip():
            issues.append(ValidationIssue("empty_translation", "translation output is empty", "error"))
        if src.strip() and len(out.strip()) / max(len(src.strip()), 1) < self.min_length_ratio:
            issues.append(ValidationIssue("short_translation", "translation output is shorter than expected", "warning"))
        if re.search(r"[가-힣]{3,}", out):
            issues.append(ValidationIssue("korean_residue", "translation output still contains Korean text", "warning"))
        return ValidationResult(passed=not any(i.severity == "error" for i in issues), issues=issues, metadata={"source_length": len(src), "output_length": len(out)})

    def _extract_text(self, translated: Any) -> str:
        if isinstance(translated, dict):
            for key in ("translation", "text", "output", "result"):
                if key in translated:
                    return str(translated[key])
        return str(translated or "")

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_validator", "min_length_ratio": self.min_length_ratio}
