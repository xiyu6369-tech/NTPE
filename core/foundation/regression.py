from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, Any, List

from .compatibility import is_foundation_compatible
from .manifest import validate_foundation_manifest
from .baseline import is_foundation_frozen

@dataclass
class RegressionResult:
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class FoundationRegressionSuite:
    def __init__(self) -> None:
        self._checks: List[tuple[str, Callable[[], bool]]] = []

    def add(self, name: str, check: Callable[[], bool]) -> "FoundationRegressionSuite":
        self._checks.append((name, check))
        return self

    def run(self) -> List[RegressionResult]:
        results: List[RegressionResult] = []
        for name, check in self._checks:
            try:
                passed = bool(check())
                detail = "PASS" if passed else "FAIL"
            except Exception as exc:
                passed = False
                detail = str(exc)
            results.append(RegressionResult(name=name, passed=passed, detail=detail))
        return results


def _path_exists(path: str) -> bool:
    return Path.cwd().joinpath(path).exists()


def build_default_foundation_regression_suite() -> FoundationRegressionSuite:
    suite = FoundationRegressionSuite()
    suite.add("foundation frozen", is_foundation_frozen)
    suite.add("manifest valid", validate_foundation_manifest)
    suite.add("compatibility valid", is_foundation_compatible)
    suite.add("core runtime present", lambda: _path_exists("core/runtime"))
    suite.add("core intelligence present", lambda: _path_exists("core/intelligence"))
    suite.add("core knowledge present", lambda: _path_exists("core/knowledge"))
    suite.add("core plugins present", lambda: _path_exists("core/plugins"))
    return suite


def run_foundation_regression() -> Dict[str, Any]:
    results = build_default_foundation_regression_suite().run()
    return {
        "passed": all(r.passed for r in results),
        "results": [r.to_dict() for r in results],
    }
