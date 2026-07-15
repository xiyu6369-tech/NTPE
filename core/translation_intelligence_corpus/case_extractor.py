from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .case_index import build_case_index
from .statistics import build_case_statistics

BATCH1_INVENTORY = Path("artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json")
BATCH1_STATISTICS = Path("artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json")
BATCH2_CASES = Path("artifacts/tic_batch2/TRANSLATION_CASES.json")
BATCH2_INDEX = Path("artifacts/tic_batch2/TRANSLATION_CASE_INDEX.json")
BATCH2_STATISTICS = Path("artifacts/tic_batch2/TRANSLATION_CASE_STATISTICS.json")
BATCH2_ARTIFACT_MANIFEST = Path("artifacts/tic_batch2/TRANSLATION_CASE_MANIFEST.json")
BATCH2_ROOT_MANIFEST = Path("manifests/tic_batch2_translation_case_extraction_manifest.json")
BATCH2_ROOT_MANIFEST_FILES = (
    "core/translation_intelligence_corpus/case_extractor.py",
    "core/translation_intelligence_corpus/case_index.py",
    "core/translation_intelligence_corpus/statistics.py",
    "artifacts/tic_batch2/TRANSLATION_CASES.json",
    "artifacts/tic_batch2/TRANSLATION_CASE_INDEX.json",
    "artifacts/tic_batch2/TRANSLATION_CASE_STATISTICS.json",
    "artifacts/tic_batch2/TRANSLATION_CASE_MANIFEST.json",
    "docs/translation_intelligence/TIC_BATCH2_TRANSLATION_CASE_EXTRACTION.md",
    "ntpe_tic_batch2_translation_case_extraction_test.py",
    "tests/integration/tic_batch2_translation_case_extraction_test.py",
)

ALLOWED_PRIMARY_STATUSES = {
    "Completed Translation",
    "Partial Translation",
    "Manual Reviewed",
}
CHUNK_RE = re.compile(r"chunk_(\d+)", re.IGNORECASE)
UNKNOWN = "unknown (historical metadata unavailable)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def load_batch1_inputs(root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    base = Path(root).resolve()
    inventory = _load_json(base / BATCH1_INVENTORY)
    statistics = _load_json(base / BATCH1_STATISTICS)
    if inventory.get("schema_version") != "tic.batch1.inventory.v1":
        raise ValueError("unsupported TIC Batch 1 inventory schema")
    if statistics.get("schema_version") != "tic.batch1.statistics.v1":
        raise ValueError("unsupported TIC Batch 1 statistics schema")
    if statistics.get("historical_translations") != len(inventory.get("items", [])):
        raise ValueError("TIC Batch 1 inventory/statistics count mismatch")
    return inventory, statistics


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _translation_text(path: Path, artifact_kind: str) -> tuple[str, dict[str, Any]]:
    if artifact_kind == "provider_result_cache":
        payload = _load_json(path)
        text = payload.get("translation")
        return (text if isinstance(text, str) else ""), payload
    return _read_text(path), {}


def _split_source_with_offsets(text: str, chunk_size: int) -> list[tuple[str, int, int]]:
    if not text:
        return []
    size = max(1, chunk_size)
    blocks: list[str] = []
    current = ""
    for item in re.split(r"(\n{2,})", text):
        if not item:
            continue
        candidate = current + item
        if len(candidate) <= size:
            current = candidate
            continue
        if current.strip():
            blocks.extend(_split_oversized(current, size))
        current = item
    if current.strip():
        blocks.extend(_split_oversized(current, size))

    spans: list[tuple[str, int, int]] = []
    cursor = 0
    for block in blocks:
        if not block.strip():
            continue
        start = text.find(block, cursor)
        if start < 0:
            raise ValueError("source chunk offset could not be preserved")
        end = start + len(block)
        spans.append((block, start, end))
        cursor = end
    return spans


def _split_oversized(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    pieces: list[str] = []
    start = 0
    boundaries = ("。", "！", "？", ".", "!", "?", "\n")
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(mark) for mark in boundaries)
            if cut > chunk_size * 0.45:
                end = start + cut + 1
        pieces.append(text[start:end])
        start = end
    return pieces


def _chunk_size(item: dict[str, Any]) -> int:
    value = item.get("chunk_size")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return int(value)
    return 600


def _metadata(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    reference = item.get("metadata_evidence_path")
    if not isinstance(reference, str) or not reference:
        return {}
    path = root / reference
    return _load_json(path) if path.is_file() else {}


def _number(metadata: Any, key: str) -> int | None:
    if isinstance(metadata, dict):
        value = metadata.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        for nested in metadata.values():
            found = _number(nested, key)
            if found is not None:
                return found
    elif isinstance(metadata, list):
        for nested in metadata:
            found = _number(nested, key)
            if found is not None:
                return found
    return None


def _source_context(
    root: Path,
    item: dict[str, Any],
    translation_payload: dict[str, Any],
    embedded_cursors: dict[str, int],
    inferred_chunk_total: int,
) -> tuple[str, int, int, str, int, int, str]:
    source_path = root / item["source_file"]
    source_text = _read_text(source_path)
    translation_file = item["translation_file"]
    chunk_match = CHUNK_RE.search(translation_file)
    chunk_index = int(chunk_match.group(1)) if chunk_match else 0
    metadata = _metadata(root, item)

    embedded = translation_payload.get("package", {}).get("source", {}).get("chunk_text")
    if isinstance(embedded, str) and embedded:
        stream = f"{item['source_file']}|provider_result_cache"
        start = embedded_cursors.get(stream, 0)
        end = start + len(embedded)
        embedded_cursors[stream] = end
        return embedded, start, end, "embedded_translation_artifact", chunk_index, chunk_index, f"chunk-{chunk_index:06d}"

    if source_path.suffix.lower() == ".json":
        source_payload = _load_json(source_path)
        parent = source_payload.get("parent_source_reference")
        start = source_payload.get("excerpt_start_offset")
        end = source_payload.get("excerpt_end_offset")
        if isinstance(parent, str) and isinstance(start, int) and isinstance(end, int):
            parent_text = _read_text(root / parent)
            return parent_text[start:end], start, end, "inventory_source_reference", 1, 1, "chunk-000001"

    if chunk_index:
        chunks = _split_source_with_offsets(source_text, _chunk_size(item))
        if chunk_index > len(chunks):
            raise ValueError(f"chunk index exceeds inventory source: {translation_file}")
        text, start, end = chunks[chunk_index - 1]
        return text, start, end, "inventory_source_file", chunk_index, chunk_index, f"chunk-{chunk_index:06d}"

    completed_chunks = _number(metadata, "completed_chunks")
    chunk_total = (
        _number(metadata, "chunk_total")
        or _number(metadata, "chunks_total")
        or inferred_chunk_total
    )
    if ".partial." in translation_file.lower():
        completed_chunks = completed_chunks or inferred_chunk_total
        chunks = _split_source_with_offsets(source_text, _chunk_size(item))
        selected = chunks[:completed_chunks]
        end = selected[-1][2] if selected else 0
        return source_text[:end], 0, end, "inventory_source_file", 0, completed_chunks, "partial-document"
    number = chunk_total or 1
    return source_text, 0, len(source_text), "inventory_source_file", 0, number, "document"


def _case_id(item: dict[str, Any], chunk_id: str) -> str:
    identity = f"{item['corpus_id']}|{item['translation_sha256']}|{chunk_id}"
    return "TIC-CASE-B2-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper()


def _stream_key(item: dict[str, Any]) -> str:
    path = Path(item["translation_file"])
    parent = path.parent.parent if path.parent.name.lower().endswith("_chunks") else path.parent
    return f"{parent.as_posix()}|{item['stage']}|{item['source_file']}"


def extract_translation_cases(
    root: str | Path,
    *,
    inventory: dict[str, Any] | None = None,
    batch1_statistics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = Path(root).resolve()
    if inventory is None or batch1_statistics is None:
        inventory, batch1_statistics = load_batch1_inputs(base)
    cases: list[dict[str, Any]] = []
    execution_evidence: list[dict[str, Any]] = []
    excluded = 0
    embedded_cursors: dict[str, int] = {}
    inferred_chunk_totals: dict[str, int] = {}
    for item in inventory["items"]:
        match = CHUNK_RE.search(item["translation_file"])
        if match:
            key = _stream_key(item)
            inferred_chunk_totals[key] = max(
                inferred_chunk_totals.get(key, 0), int(match.group(1))
            )

    for inventory_order, item in enumerate(inventory["items"]):
        translation_path = base / item["translation_file"]
        source_path = base / item["source_file"]
        if sha256_file(translation_path) != item["translation_sha256"]:
            raise ValueError(f"translation SHA mismatch: {item['translation_file']}")
        if sha256_file(source_path) != item["source_sha256"]:
            raise ValueError(f"source SHA mismatch: {item['source_file']}")
        translation_text, translation_payload = _translation_text(
            translation_path, item["artifact_kind"]
        )
        tags = item.get("status_tags", [])
        allowed = (
            item["translation_status"] in ALLOWED_PRIMARY_STATUSES
            or "Partial Translation" in tags
        )
        if item["translation_status"] == "Provider Timeout" and not translation_text:
            execution_evidence.append(
                {
                    "corpus_id": item["corpus_id"],
                    "source_file": item["source_file"],
                    "translation_file": item["translation_file"],
                    "stage": item["stage"],
                    "version": item["version"],
                    "provider": item["provider"],
                    "model": item["model"],
                    "translation_status": item["translation_status"],
                    "source_sha256": item["source_sha256"],
                    "translation_sha256": item["translation_sha256"],
                    "metadata_evidence_path": item.get("metadata_evidence_path"),
                    "translation_text_present": False,
                    "translation_case_created": False,
                    "reason": "provider_timeout_without_translation",
                }
            )
            continue
        if not allowed or not translation_text:
            excluded += 1
            continue

        source_text, start, end, offset_basis, chunk_index, chunk_number, chunk_id = _source_context(
            base,
            item,
            translation_payload,
            embedded_cursors,
            inferred_chunk_totals.get(_stream_key(item), 0),
        )
        cases.append(
            {
                "case_id": _case_id(item, chunk_id),
                "corpus_id": item["corpus_id"],
                "inventory_order": inventory_order,
                "source_file": item["source_file"],
                "translation_file": item["translation_file"],
                "stage": item["stage"],
                "version": item["version"],
                "provider": item["provider"],
                "model": item["model"],
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "chunk_order": chunk_index,
                "chunk_number": chunk_number,
                "chunk_offset": {"start": start, "end": end, "unit": "unicode_codepoint"},
                "chunk_offset_basis": offset_basis,
                "source_text": source_text,
                "translation_text": translation_text,
                "source_sha256": item["source_sha256"],
                "translation_sha256": item["translation_sha256"],
                "translation_status": item["translation_status"],
                "status_tags": list(tags),
                "has_manual_review": item["has_manual_review"],
                "review_reference": item.get("review_path"),
            }
        )

    return {
        "schema_version": "tic.batch2.translation-cases.v1",
        "corpus": "NTPE Translation Intelligence Corpus",
        "batch": "Batch 2 - Translation Case Extraction",
        "status": "TIC Batch 2 Completed",
        "next_batch_status": "TIC Batch 3 Not Started",
        "selection_source": {
            "inventory": BATCH1_INVENTORY.as_posix(),
            "statistics": BATCH1_STATISTICS.as_posix(),
            "inventory_sha256": sha256_file(base / BATCH1_INVENTORY),
            "statistics_sha256": sha256_file(base / BATCH1_STATISTICS),
            "inventory_items": len(inventory["items"]),
        },
        "translation_cases": cases,
        "execution_evidence": execution_evidence,
        "excluded_without_case_or_execution": excluded,
        "boundaries": {
            "inventory_rebuilt": False,
            "repository_rescanned": False,
            "provider_executed": False,
            "new_translation_generated": False,
            "historical_translation_modified": False,
            "quality_judgement_performed": False,
            "failure_or_excellence_classification_performed": False,
            "batch_3_started": False,
        },
    }


def generate_batch2_artifacts(root: str | Path) -> tuple[Path, Path, Path, Path]:
    base = Path(root).resolve()
    inventory, batch1_statistics = load_batch1_inputs(base)
    cases = extract_translation_cases(
        base, inventory=inventory, batch1_statistics=batch1_statistics
    )
    index = build_case_index(cases)
    statistics = build_case_statistics(cases, inventory_count=len(inventory["items"]))
    targets = {
        BATCH2_CASES: cases,
        BATCH2_INDEX: index,
        BATCH2_STATISTICS: statistics,
    }
    for relative, payload in targets.items():
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_canonical_json(payload))
    manifest = {
        "schema_version": "tic.batch2.artifact-manifest.v1",
        "batch": "TIC Batch 2",
        "status": "completed",
        "batch1_inputs": {
            BATCH1_INVENTORY.as_posix(): sha256_file(base / BATCH1_INVENTORY),
            BATCH1_STATISTICS.as_posix(): sha256_file(base / BATCH1_STATISTICS),
        },
        "files": {
            relative.as_posix(): sha256_file(base / relative) for relative in targets
        },
        "boundaries": cases["boundaries"],
        "self_hash_excluded": True,
    }
    manifest_path = base / BATCH2_ARTIFACT_MANIFEST
    manifest_path.write_bytes(_canonical_json(manifest))
    return tuple(base / path for path in (*targets, BATCH2_ARTIFACT_MANIFEST))


def generate_batch2_root_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    missing = [name for name in BATCH2_ROOT_MANIFEST_FILES if not (base / name).is_file()]
    if missing:
        raise FileNotFoundError(f"TIC Batch 2 manifest inputs missing: {missing}")
    payload = {
        "schema_version": "tic.batch2.release-manifest.v1",
        "corpus": "NTPE Translation Intelligence Corpus",
        "batch": "Batch 2 - Translation Case Extraction",
        "status": "TIC Batch 2 Completed",
        "next_batch_status": "TIC Batch 3 Not Started",
        "batch1_inputs": {
            BATCH1_INVENTORY.as_posix(): sha256_file(base / BATCH1_INVENTORY),
            BATCH1_STATISTICS.as_posix(): sha256_file(base / BATCH1_STATISTICS),
        },
        "files": {
            name: sha256_file(base / name) for name in BATCH2_ROOT_MANIFEST_FILES
        },
        "tests": {
            "root": "ntpe_tic_batch2_translation_case_extraction_test.py",
            "focused_integration": "tests/integration/tic_batch2_translation_case_extraction_test.py",
        },
        "boundaries": {
            "inventory_rebuilt": False,
            "repository_rescanned": False,
            "provider_executed": False,
            "new_translation_generated": False,
            "historical_translation_modified": False,
            "runtime_modified": False,
            "prompt_modified": False,
            "stage_11_modified": False,
            "stage_12_modified": False,
            "golden_corpus_modified": False,
            "quality_judgement_performed": False,
            "failure_or_excellence_classification_performed": False,
            "batch_3_started": False,
        },
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    target = base / BATCH2_ROOT_MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canonical_json(payload))
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TIC Batch 2 translation cases")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    for path in generate_batch2_artifacts(args.root):
        print(path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
