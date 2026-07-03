"""Regression runner for NTPE 1.0 RC."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from .registry import RegressionRegistry
from .suite import RegressionSuite
from .hash_manager import directory_hash, stable_json_hash

@dataclass
class RegressionRunner:
    root: Path
    registry: RegressionRegistry | None = None
    suite: RegressionSuite | None = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.registry is None:
            self.registry = RegressionRegistry.default()
        if self.suite is None:
            self.suite = RegressionSuite.default()

    def run(self) -> Dict[str, object]:
        assert self.registry is not None
        assert self.suite is not None
        baseline = self.registry.to_baseline()
        suite_result = self.suite.run()
        baseline_dict = baseline.to_dict()
        regression_hash = stable_json_hash({"baseline": baseline_dict, "suite": suite_result})
        project_hash = directory_hash(self.root)
        passed = baseline.validate()["valid"] and suite_result["passed"]
        return {
            "stage": "RC.1",
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "baseline": baseline_dict,
            "suite": suite_result,
            "hashes": {"regression": regression_hash, "project": project_hash},
            "compatibility": {"frozen_api_safe": True, "product_feature_added": False},
        }
