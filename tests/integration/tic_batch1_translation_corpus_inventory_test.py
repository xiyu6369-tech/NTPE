from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from core.translation_intelligence_corpus import (
    build_inventory,
    build_statistics,
    discover_translation_artifacts,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json"
STATISTICS = ROOT / "artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json"
ARTIFACT_MANIFEST = ROOT / "artifacts/tic_batch1/TRANSLATION_CORPUS_MANIFEST.json"
ROOT_MANIFEST = ROOT / "manifests/tic_batch1_translation_corpus_inventory_manifest.json"
MODULE = ROOT / "core/translation_intelligence_corpus/inventory.py"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repository_scan_covers_every_recognizable_translation_artifact() -> None:
    discovered = {path.relative_to(ROOT).as_posix() for path in discover_translation_artifacts(ROOT)}
    recorded = {row["translation_file"] for row in _json(INVENTORY)["items"]}
    assert discovered == recorded
    assert any(path.endswith("translation.txt") for path in discovered)
    assert any(path.endswith("_zh.txt") for path in discovered)
    assert any(".partial.txt" in path for path in discovered)
    assert any(path.startswith("translation_cache/") for path in discovered)
    assert "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt" in discovered


def test_inventory_is_fresh_and_deterministic() -> None:
    first = build_inventory(ROOT)
    second = build_inventory(ROOT)
    assert first == second == _json(INVENTORY)
    assert first["deterministic"] is True
    assert first["status"] == "TIC Batch 1 Completed"
    assert first["next_batch_status"] == "TIC Batch 2 Not Started"


def test_inventory_metadata_is_complete_and_sha256_is_valid() -> None:
    required = {
        "corpus_id", "source_file", "translation_file", "stage", "version",
        "provider", "model", "chunk_size", "translation_status", "source_sha256",
        "translation_sha256", "has_manual_review", "review_path",
        "usable_for_quality_analysis",
    }
    rows = _json(INVENTORY)["items"]
    assert rows and len({row["corpus_id"] for row in rows}) == len(rows)
    for row in rows:
        assert required <= row.keys()
        assert all(row[key] not in (None, "") for key in required - {"review_path"})
        assert SHA256.fullmatch(row["source_sha256"])
        assert SHA256.fullmatch(row["translation_sha256"])
        assert sha256_file(ROOT / row["source_file"]) == row["source_sha256"]
        assert sha256_file(ROOT / row["translation_file"]) == row["translation_sha256"]


def test_statistics_are_recomputed_from_inventory() -> None:
    inventory = _json(INVENTORY)
    assert build_statistics(inventory) == _json(STATISTICS)
    statistics = _json(STATISTICS)
    assert statistics["historical_translations"] == len(inventory["items"])
    assert statistics["translation_coverage"]["percent"] >= 0
    assert statistics["available_quality_evidence"] <= statistics["historical_translations"]


def test_artifact_and_release_manifests_match_files() -> None:
    for manifest_path in (ARTIFACT_MANIFEST, ROOT_MANIFEST):
        manifest = _json(manifest_path)
        for name, expected in manifest["files"].items():
            assert SHA256.fullmatch(expected)
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_inventory_build_does_not_modify_translations() -> None:
    paths = discover_translation_artifacts(ROOT)
    before = {path: sha256_file(path) for path in paths}
    build_inventory(ROOT)
    after = {path: sha256_file(path) for path in paths}
    assert before == after


def test_module_has_no_runtime_or_provider_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any("runtime" in name.lower() or "provider" in name.lower() for name in imports)


def test_boundary_manifest_proves_inventory_only_scope() -> None:
    boundary = _json(ROOT_MANIFEST)["boundaries"]
    assert boundary["inventory_only"] is True
    assert boundary["provider_calls_added"] == 0
    assert all(value is False for key, value in boundary.items() if key not in {"inventory_only", "provider_calls_added"})


def test_required_scan_locations_are_explicit() -> None:
    locations = {row["path"]: row["present"] for row in _json(INVENTORY)["scan_scope"]["required_locations"]}
    assert {"tests/literary", "tests/literary/outputs", "output", "artifacts", "Golden_Set", "Passion"} <= locations.keys()
    assert locations["tests/literary"] and locations["tests/literary/outputs"] and locations["artifacts"]


def test_status_taxonomy_contains_all_batch1_categories() -> None:
    counts = _json(STATISTICS)["status_counts"]
    assert set(counts) == {
        "Completed Translation", "Partial Translation", "Provider Timeout",
        "Manual Reviewed", "Historical Translation",
    }
    assert all(isinstance(value, int) and value >= 0 for value in counts.values())
