from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QualityIssue:
    code: str
    message: str
    severity: str = "warning"
    position: Optional[int] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "position": self.position,
            "suggestion": self.suggestion,
            "metadata": dict(self.metadata),
        }


@dataclass
class QualityContext:
    source_text: str = ""
    translated_text: str = ""
    glossary: Dict[str, str] = field(default_factory=dict)
    character_names: Dict[str, str] = field(default_factory=dict)
    style: str = "zh-TW"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityResult:
    passed: bool = True
    score: float = 1.0
    text: str = ""
    issues: List[QualityIssue] = field(default_factory=list)
    repairs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: QualityIssue) -> None:
        self.issues.append(issue)
        if issue.severity in {"error", "critical"}:
            self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "text": self.text,
            "issues": [issue.to_dict() for issue in self.issues],
            "repairs": list(self.repairs),
            "metadata": dict(self.metadata),
        }


class QualityComponent:
    name = "quality_component"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        return result
