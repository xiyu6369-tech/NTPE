from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from cli.main import run_cli
from cli.result import CLIResult

from .baseline import expected_commands


class CLIRegressionSuite:
    """Small deterministic regression suite for the frozen CLI command surface."""

    def __init__(self, root: Path | None = None) -> None:
        self._tmp = None
        if root is None:
            self._tmp = tempfile.TemporaryDirectory()
            root = Path(self._tmp.name)
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, CLIResult] = {}

    def close(self) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()

    def _run(self, name: str, argv: List[str]) -> CLIResult:
        result = run_cli(["--root", str(self.root), *argv])
        self.results[name] = result
        return result

    def run_core(self) -> bool:
        # Doctor expects an NTPE-like project root, so create the minimal
        # directories required for a deterministic compatibility check.
        for name in ("core", "runtime", "translation"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        version = self._run("version", ["version"])
        doctor = self._run("doctor", ["doctor"])
        return version.ok and doctor.ok

    def run_translate(self) -> bool:
        source = self.root / "sample.txt"
        source.write_text("hello", encoding="utf-8")
        result = self._run("translate", ["translate", str(source), "--dry-run", "--provider", "mock", "--quality", "standard"])
        return result.ok

    def run_project(self) -> bool:
        project_dir = self.root / "project_a"
        create = self._run("project_create", ["project", "create", str(project_dir), "--name", "Project A", "--force"])
        info = self._run("project_info", ["project", "info", str(project_dir)])
        validate = self._run("project_validate", ["project", "validate", str(project_dir)])
        return create.ok and info.ok and validate.ok

    def run_benchmark(self) -> bool:
        output = self.root / "bench"
        result = self._run("benchmark_runtime", ["benchmark", "runtime", "--segments", "2", "--output", str(output)])
        return result.ok

    def run_quality(self) -> bool:
        target = self.root / "translated.txt"
        target.write_text("這是一段繁體中文譯文。", encoding="utf-8")
        result = self._run("quality_rules", ["quality", "rules"])
        score = self._run("quality_score", ["quality", "score", str(target)])
        return result.ok and score.ok

    def run_session(self) -> bool:
        session_dir = self.root / "sessions"
        create = self._run("session_create", ["session", "create", "sess-a", "--session-dir", str(session_dir)])
        info = self._run("session_info", ["session", "info", "sess-a", "--session-dir", str(session_dir)])
        checkpoint = self._run("session_checkpoint", ["session", "checkpoint", "sess-a", "--segment", "1", "--session-dir", str(session_dir)])
        return create.ok and info.ok and checkpoint.ok

    def run_config(self) -> bool:
        config_dir = self.root / ".ntpe"
        set_result = self._run("config_set", ["config", "set", "provider.default", "mock", "--config-dir", str(config_dir)])
        get_result = self._run("config_get", ["config", "get", "provider.default", "--config-dir", str(config_dir)])
        validate = self._run("config_validate", ["config", "validate", "--config-dir", str(config_dir)])
        return set_result.ok and get_result.ok and validate.ok

    def run_plugin(self) -> bool:
        plugin_dir = self.root / "plugins"
        package = self.root / "demo_plugin.json"
        package.write_text(json.dumps({"name": "demo_plugin", "version": "1.0.0", "kind": "demo"}), encoding="utf-8")
        install = self._run("plugin_install", ["plugin", "install", str(package), "--plugin-dir", str(plugin_dir), "--replace"])
        list_result = self._run("plugin_list", ["plugin", "list", "--plugin-dir", str(plugin_dir)])
        validate = self._run("plugin_validate", ["plugin", "validate", "--plugin-dir", str(plugin_dir)])
        return install.ok and list_result.ok and validate.ok

    def run_json_stability(self) -> bool:
        result = self._run("json_version", ["version"])
        payload = result.to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)
        decoded = json.loads(encoded)
        return sorted(decoded.keys()) == ["data", "errors", "exit_code", "message", "ok"]

    def run_all(self) -> Dict[str, bool]:
        checks = {
            "core": self.run_core(),
            "translate": self.run_translate(),
            "project": self.run_project(),
            "benchmark": self.run_benchmark(),
            "quality": self.run_quality(),
            "session": self.run_session(),
            "config": self.run_config(),
            "plugin": self.run_plugin(),
            "json_stability": self.run_json_stability(),
        }
        checks["expected_commands"] = all(command in expected_commands() for command in expected_commands())
        return checks


def run_cli_regression_suite(root: Path | None = None) -> Dict[str, bool]:
    suite = CLIRegressionSuite(root=root)
    try:
        return suite.run_all()
    finally:
        suite.close()
