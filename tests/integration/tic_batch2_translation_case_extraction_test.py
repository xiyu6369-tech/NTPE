from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from core.translation_intelligence_corpus.case_extractor import (
    BATCH1_INVENTORY,
    BATCH1_STATISTICS,
    extract_translation_cases,
    load_batch1_inputs,
    sha256_file,
)
from core.translation_intelligence_corpus.case_index import build_case_index
from core.translation_intelligence_corpus.statistics import build_case_statistics

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "artifacts/tic_batch2/TRANSLATION_CASES.json"
INDEX_PATH = ROOT / "artifacts/tic_batch2/TRANSLATION_CASE_INDEX.json"
STATISTICS_PATH = ROOT / "artifacts/tic_batch2/TRANSLATION_CASE_STATISTICS.json"
ARTIFACT_MANIFEST = ROOT / "artifacts/tic_batch2/TRANSLATION_CASE_MANIFEST.json"
ROOT_MANIFEST = ROOT / "manifests/tic_batch2_translation_case_extraction_manifest.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_inventory_to_case_extraction_uses_frozen_batch1_inputs() -> None:
    inventory, statistics = load_batch1_inputs(ROOT)
    cases = _json(CASES_PATH)
    assert cases == extract_translation_cases(
        ROOT, inventory=inventory, batch1_statistics=statistics
    )
    assert cases["selection_source"]["inventory"] == BATCH1_INVENTORY.as_posix()
    assert cases["selection_source"]["statistics"] == BATCH1_STATISTICS.as_posix()
    assert cases["selection_source"]["inventory_items"] == 130


def test_translation_cases_and_timeout_execution_evidence_are_separated() -> None:
    payload = _json(CASES_PATH)
    assert len(payload["translation_cases"]) == 125
    assert len(payload["execution_evidence"]) == 4
    assert payload["excluded_without_case_or_execution"] == 1
    assert all(not row["translation_text_present"] for row in payload["execution_evidence"])
    assert all(not row["translation_case_created"] for row in payload["execution_evidence"])
    assert all(row["reason"] == "provider_timeout_without_translation" for row in payload["execution_evidence"])


def test_case_metadata_and_sha_preservation_are_complete() -> None:
    required = {
        "case_id", "corpus_id", "source_file", "translation_file", "stage",
        "version", "provider", "model", "chunk_id", "chunk_index", "chunk_order",
        "chunk_number", "chunk_offset", "source_text", "translation_text",
        "source_sha256", "translation_sha256", "translation_status",
        "has_manual_review", "review_reference",
    }
    cases = _json(CASES_PATH)["translation_cases"]
    assert len({case["case_id"] for case in cases}) == len(cases)
    for case in cases:
        assert required <= case.keys()
        assert all(case[key] not in (None, "") for key in required - {"review_reference"})
        assert SHA256.fullmatch(case["source_sha256"])
        assert SHA256.fullmatch(case["translation_sha256"])
        assert sha256_file(ROOT / case["source_file"]) == case["source_sha256"]
        assert sha256_file(ROOT / case["translation_file"]) == case["translation_sha256"]


def test_translation_text_is_preserved_without_retranslation() -> None:
    for case in _json(CASES_PATH)["translation_cases"]:
        path = ROOT / case["translation_file"]
        if path.suffix.lower() == ".json":
            expected = _json(path)["translation"]
        else:
            expected = path.read_text(encoding="utf-8-sig")
        assert case["translation_text"] == expected


def test_chunk_order_number_and_offsets_are_preserved() -> None:
    cases = _json(CASES_PATH)["translation_cases"]
    assert [case["inventory_order"] for case in cases] == sorted(
        case["inventory_order"] for case in cases
    )
    streams: defaultdict[str, list[int]] = defaultdict(list)
    for case in cases:
        offset = case["chunk_offset"]
        assert offset["unit"] == "unicode_codepoint"
        assert offset["start"] >= 0 and offset["end"] >= offset["start"]
        assert len(case["source_text"]) == offset["end"] - offset["start"]
        if case["chunk_index"] > 0:
            key = f"{Path(case['translation_file']).parent}|{case['stage']}"
            streams[key].append(case["chunk_index"])
            assert case["chunk_order"] == case["chunk_index"]
            assert case["chunk_number"] == case["chunk_index"]
    assert all(indexes == sorted(indexes) for indexes in streams.values())
    assert any(case["chunk_id"] == "partial-document" for case in cases)


def test_metadata_search_index_covers_every_case() -> None:
    cases_payload = _json(CASES_PATH)
    index = _json(INDEX_PATH)
    assert index == build_case_index(cases_payload)
    case_ids = {case["case_id"] for case in cases_payload["translation_cases"]}
    assert set(index["by_case_id"]) == case_ids
    assert index["full_text_search"] is False
    for key in (
        "by_corpus_id", "by_stage", "by_provider", "by_model",
        "by_translation_status", "by_source_file",
    ):
        assert set().union(*map(set, index[key].values())) == case_ids


def test_case_statistics_recompute_exactly() -> None:
    cases = _json(CASES_PATH)
    expected = build_case_statistics(cases, inventory_count=130)
    assert _json(STATISTICS_PATH) == expected
    assert expected["total_translation_cases"] == 125
    assert expected["cases_with_review"] == 1
    assert expected["corpus_coverage"]["percent"] == 96.15


def test_artifact_and_root_manifests_match_sha256() -> None:
    for manifest_path in (ARTIFACT_MANIFEST, ROOT_MANIFEST):
        manifest = _json(manifest_path)
        for name, expected in manifest["files"].items():
            assert SHA256.fullmatch(expected)
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        for name, expected in manifest["batch1_inputs"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_extraction_is_deterministic() -> None:
    inventory, statistics = load_batch1_inputs(ROOT)
    first = extract_translation_cases(ROOT, inventory=inventory, batch1_statistics=statistics)
    second = extract_translation_cases(ROOT, inventory=inventory, batch1_statistics=statistics)
    assert first == second == _json(CASES_PATH)


def test_extraction_does_not_modify_historical_translations() -> None:
    inventory, statistics = load_batch1_inputs(ROOT)
    before = {
        item["translation_file"]: sha256_file(ROOT / item["translation_file"])
        for item in inventory["items"]
    }
    extract_translation_cases(ROOT, inventory=inventory, batch1_statistics=statistics)
    after = {
        item["translation_file"]: sha256_file(ROOT / item["translation_file"])
        for item in inventory["items"]
    }
    assert before == after


def test_module_has_no_runtime_or_provider_import_and_no_rescan() -> None:
    modules = [
        ROOT / "core/translation_intelligence_corpus/case_extractor.py",
        ROOT / "core/translation_intelligence_corpus/case_index.py",
        ROOT / "core/translation_intelligence_corpus/statistics.py",
    ]
    for module in modules:
        source = module.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any("runtime" in name.lower() or "provider" in name.lower() for name in imports)
        assert ".rglob(" not in source and ".glob(" not in source
        assert "build_inventory" not in source and "generate_batch1_artifacts" not in source


def test_batch2_boundaries_and_stop_point_are_explicit() -> None:
    payload = _json(CASES_PATH)
    boundary = payload["boundaries"]
    assert payload["status"] == "TIC Batch 2 Completed"
    assert payload["next_batch_status"] == "TIC Batch 3 Not Started"
    assert all(value is False for value in boundary.values())
