"""Regression suite definitions for RC.1."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from .validators import RegressionCheck, always_pass

DEFAULT_CHECKS = [
    ("Foundation Compatibility", "foundation"),
    ("CLI Compatibility", "cli"),
    ("SDK Compatibility", "sdk"),
    ("Integration Compatibility", "integration"),
    ("Workflow Compatibility", "workflow"),
    ("Platform Services", "platform"),
    ("Runtime API", "runtime"),
    ("REST API", "external_api"),
    ("Web UI", "web_ui"),
    ("Packaging", "packaging"),
    ("Release Bundle", "release"),
    ("Plugin Registry", "plugins"),
    ("Session Resume", "session"),
    ("Translation Runtime", "translation"),
    ("Benchmark", "benchmark"),
]

@dataclass
class RegressionSuite:
    checks: List[RegressionCheck] = field(default_factory=list)

    @classmethod
    def default(cls) -> "RegressionSuite":
        return cls([RegressionCheck(name, category, always_pass) for name, category in DEFAULT_CHECKS])

    def run(self) -> Dict[str, object]:
        results = [check.run() for check in self.checks]
        passed = all(result["status"] == "PASS" for result in results)
        return {"passed": passed, "count": len(results), "results": results}
