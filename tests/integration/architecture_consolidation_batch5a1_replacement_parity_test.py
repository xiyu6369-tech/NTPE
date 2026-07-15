from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import socket

import pytest


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audits/architecture_consolidation/batch5a1_parity"
SUPPORT_PATH = ROOT / "tests/characterization/batch5a1_parity_support.py"
BENCHMARK_PATH = ROOT / "tests/performance/batch5a1_replacement_parity_benchmark.py"
DOMAIN_MODULES = (ROOT / "core/context", ROOT / "core/narrative", ROOT / "core/voice", ROOT / "core/literary")


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(name: str) -> dict:
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


def hashes() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for base in DOMAIN_MODULES for path in base.rglob("*.py")}


def test_real_legacy_replacement_pairs_are_deterministic_without_mutation_or_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network attempted")))
    support = module_from(SUPPORT_PATH, "batch5a1_support_integration")
    before = hashes()
    for domain in ("context", "narrative", "voice"):
        rows = support.characterize_domain(domain)
        assert len(rows) == 10
        assert rows == support.characterize_domain(domain)
        assert all(not row["input_mutated"] and not row["value_equal"] for row in rows)
    assert hashes() == before


def test_exception_mismatch_and_partial_overlap_are_detected() -> None:
    support = module_from(SUPPORT_PATH, "batch5a1_support_exceptions")
    observations = {domain: support.exception_observation(domain) for domain in ("context", "narrative", "voice")}
    assert observations["context"]["parity"] is False
    assert all(len(row["observations"]) == 2 for row in observations.values())
    voice_rows = support.characterize_domain("voice")
    assert any(row["overlap_names"] for row in voice_rows)
    assert all(row["status"] == "PARITY_PARTIAL" for row in voice_rows)


def test_performance_gate_and_external_compatibility_fail_closed() -> None:
    benchmark = module_from(BENCHMARK_PATH, "batch5a1_benchmark_integration").run_benchmark(iterations=100, warmup_iterations=10)
    assert benchmark["performance_gate_pass"] is True
    external = load("EXTERNAL_COMPATIBILITY_PARITY.json")
    assert all(row["risk"] == "HIGH" and row["legacy_import_path_must_remain"] for row in external["items"])
    plan = load("BATCH5B_PARITY_BASED_PLAN.json")
    assert plan["item_count"] == 0 and plan["batch5b_started"] is False


def test_all_reports_parse_and_status_partition_is_exact() -> None:
    for path in AUDIT.glob("*.json"):
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
    statuses = ("PARITY_PROVEN", "PARITY_PARTIAL", "PARITY_FAILED", "BLOCKED", "NEEDS_EXTERNAL_CONFIRMATION")
    rows = [row for status in statuses for row in load(f"{status}.json")["items"]]
    assert len(rows) == 3
    assert {row["domain"] for row in rows} == {"context", "narrative", "voice"}
