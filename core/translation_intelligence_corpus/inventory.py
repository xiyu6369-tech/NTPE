from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "tic.batch1.inventory.v1"
INVENTORY_PATH = Path("artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json")
STATISTICS_PATH = Path("artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json")
ARTIFACT_MANIFEST_PATH = Path("artifacts/tic_batch1/TRANSLATION_CORPUS_MANIFEST.json")
ROOT_MANIFEST_PATH = Path("manifests/tic_batch1_translation_corpus_inventory_manifest.json")
ROOT_MANIFEST_FILES = (
    "core/translation_intelligence_corpus/__init__.py",
    "core/translation_intelligence_corpus/__main__.py",
    "core/translation_intelligence_corpus/inventory.py",
    "artifacts/tic_batch1/TRANSLATION_CORPUS_INVENTORY.json",
    "artifacts/tic_batch1/TRANSLATION_CORPUS_STATISTICS.json",
    "artifacts/tic_batch1/TRANSLATION_CORPUS_MANIFEST.json",
    "docs/translation_intelligence/TIC_BATCH1_HISTORICAL_TRANSLATION_CORPUS.md",
    "ntpe_tic_batch1_translation_corpus_inventory_test.py",
    "tests/integration/tic_batch1_translation_corpus_inventory_test.py",
)

UNKNOWN = "unknown (historical metadata unavailable)"
REQUIRED_SCAN_LOCATIONS = (
    "tests/literary",
    "tests/literary/outputs",
    "output",
    "artifacts",
    "Golden_Set",
    "Passion",
    "translated",
    "translation_cache",
)
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ntpe_test_sandbox"}
TRANSLATION_RE = re.compile(r"_zh(?:\.partial)?\.txt$", re.IGNORECASE)
VERSION_RE = re.compile(r"(?:TE|TER)-v(\d+(?:\.\d+)*)", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def discover_translation_artifacts(root: str | Path) -> tuple[Path, ...]:
    """Return recognizable historical translation artifacts without modifying them."""
    base = Path(root).resolve()
    found: list[Path] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(base)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts[:2] == ("artifacts", "tic_batch1"):
            continue
        name = path.name.lower()
        if name == "translation.txt" or TRANSLATION_RE.search(name):
            found.append(path)
        elif relative.parts and relative.parts[0] == "translation_cache" and name.endswith("_result.json"):
            found.append(path)
        elif relative.as_posix() == "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt":
            found.append(path)
    return tuple(sorted(found, key=lambda item: _relative(item, base).casefold()))


def _artifact_kind(path: Path, root: Path) -> str:
    relative = _relative(path, root)
    name = path.name.lower()
    if relative.startswith("translation_cache/"):
        return "provider_result_cache"
    if relative.endswith("TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"):
        return "manual_review_translation"
    if name == "translation.txt":
        return "provider_translation_output"
    if ".partial." in name:
        return "partial_translation_output"
    if "_chunks/" in relative:
        return "chunk_translation_output"
    return "translation_output"


def _nearest_manifest(path: Path, root: Path) -> Path | None:
    current = path.parent
    while current != root.parent and current.is_relative_to(root):
        candidates = sorted(current.glob("*_translation_manifest.json"))
        candidates += sorted(current.glob("*_partial_manifest.json"))
        if candidates:
            return candidates[0]
        if current == root:
            break
        current = current.parent
    return None


def _execution_metadata(path: Path) -> Path | None:
    candidate = path.parent / "execution_metadata.json"
    return candidate if candidate.is_file() else None


def _metadata(path: Path, root: Path) -> tuple[dict[str, Any], Path | None]:
    relative = _relative(path, root)
    if relative.startswith("translation_cache/"):
        return _load_json(path), path
    if relative.startswith("translated/"):
        cache_name = re.sub(r"_zh\.txt$", "_result.json", path.name, flags=re.IGNORECASE)
        cache = root / "translation_cache" / cache_name
        if cache.is_file():
            return _load_json(cache), cache
    if relative.endswith("TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"):
        controlled = root / "artifacts/te_v7_stage10101/TE_V7_STAGE10101_CONTROLLED_RETRY.json"
        if controlled.is_file():
            return _load_json(controlled), controlled
    execution = _execution_metadata(path)
    if execution:
        return _load_json(execution), execution
    manifest = _nearest_manifest(path, root)
    return _load_json(manifest), manifest


def _source_path(path: Path, root: Path) -> Path:
    relative = _relative(path, root)
    if relative.startswith("artifacts/te_v72_stage1223/"):
        excerpt = root / "artifacts/te_v72_stage1223/TE_V72_STAGE1223_SOURCE_EXCERPT_FREEZE.json"
        if excerpt.is_file():
            return excerpt
    set_names = ("Golden_Set", "Smoke_Set", "Test_Set_0", "Passion")
    for set_name in set_names:
        if set_name in path.parts:
            canonical = root / "tests" / "literary" / set_name / "original_ko.txt"
            if canonical.is_file():
                return canonical
            ancestor = path
            while ancestor != root:
                candidate = ancestor / "original_ko.txt"
                if candidate.is_file():
                    return candidate
                ancestor = ancestor.parent
            historical = sorted((root / "tests/literary/outputs").glob(f"*/{set_name}/original_ko.txt"))
            if historical:
                return historical[0]
    if relative.startswith(("translation_cache/", "translated/", "artifacts/")):
        canonical = root / "tests/literary/Golden_Set/original_ko.txt"
        if canonical.is_file():
            return canonical
    stem = re.sub(r"_zh(?:\.partial)?$", "", path.stem, flags=re.IGNORECASE)
    sibling = path.with_name(stem + ".txt")
    if sibling.is_file():
        return sibling
    raise FileNotFoundError(f"No source file can be resolved for {relative}")


def _deep_values(value: Any, key: str) -> Iterable[Any]:
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                yield current_value
            yield from _deep_values(current_value, key)
    elif isinstance(value, list):
        for item in value:
            yield from _deep_values(item, key)


def _first_text(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        for value in _deep_values(metadata, key):
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _first_number(metadata: dict[str, Any], *keys: str) -> int | float | None:
    for key in keys:
        for value in _deep_values(metadata, key):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
    return None


def _stage_version(path: Path, root: Path, metadata: dict[str, Any]) -> tuple[str, str]:
    stage = _first_text(metadata, "stage")
    relative = _relative(path, root)
    if not stage and relative.startswith("tests/literary/outputs/"):
        stage = Path(relative).parts[3]
    if not stage and relative.startswith("artifacts/"):
        stage = Path(relative).parts[1]
    stage = stage or "Historical Translation"
    version = _first_text(metadata, "version", "package_version")
    if not version:
        match = VERSION_RE.search(stage)
        version = match.group(1) if match else UNKNOWN
    return stage, version


def _provider_model(metadata: dict[str, Any]) -> tuple[str, str]:
    provider = _first_text(metadata, "provider", "provider_type", "engine")
    model = _first_text(metadata, "model", "provider_model")
    dry_run = next((value for value in _deep_values(metadata, "dry_run") if isinstance(value, bool)), False)
    if dry_run:
        provider = "none (dry-run)"
    elif provider and provider.lower() in {"nvidia", "nvidia_api", "nvidia_client"}:
        provider = "nvidia"
    elif not provider and model and "llama" in model.lower():
        provider = "nvidia"
    return provider or UNKNOWN, model or UNKNOWN


def _review_evidence(path: Path, root: Path) -> tuple[bool, str | None]:
    relative = _relative(path, root)
    if relative.endswith("TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"):
        return True, relative
    for parent in (path.parent, path.parent.parent):
        if not parent.is_relative_to(root):
            continue
        reviews = sorted(parent.glob("*MANUAL*REVIEW*.json"))
        if reviews:
            payload = _load_json(reviews[0])
            return payload.get("manual_review_completed") is True, _relative(reviews[0], root)
        evaluation = parent / "evaluation.md"
        if evaluation.is_file():
            return False, _relative(evaluation, root)
    return False, None


def _translation_status(path: Path, root: Path, metadata: dict[str, Any], has_review: bool) -> tuple[str, list[str]]:
    tags = ["Historical Translation"]
    if has_review:
        tags.append("Manual Reviewed")
    status_values = " ".join(
        str(value).lower()
        for key in ("status", "error", "exception_category")
        for value in _deep_values(metadata, key)
        if value is not None
    )
    partial = ".partial." in path.name.lower() or "partial_failed" in status_values
    timeout = "timeout" in status_values
    if partial:
        tags.append("Partial Translation")
    if timeout:
        primary = "Provider Timeout"
        tags.append("Provider Timeout")
    elif has_review:
        primary = "Manual Reviewed"
    elif partial:
        primary = "Partial Translation"
    elif path.stat().st_size > 0:
        primary = "Completed Translation"
        tags.append("Completed Translation")
    else:
        primary = "Historical Translation"
    return primary, sorted(set(tags))


def _corpus_id(relative: str) -> str:
    suffix = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20].upper()
    return f"TIC-B1-{suffix}"


def _record(path: Path, root: Path) -> dict[str, Any]:
    relative = _relative(path, root)
    metadata, metadata_path = _metadata(path, root)
    source = _source_path(path, root)
    has_review, review_path = _review_evidence(path, root)
    status, tags = _translation_status(path, root, metadata, has_review)
    stage, version = _stage_version(path, root, metadata)
    provider, model = _provider_model(metadata)
    chunk_size = _first_number(metadata, "chunk_size")
    usable = bool(path.stat().st_size and source.is_file() and status != "Historical Translation")
    return {
        "corpus_id": _corpus_id(relative),
        "source_file": _relative(source, root),
        "translation_file": relative,
        "artifact_kind": _artifact_kind(path, root),
        "stage": stage,
        "version": version,
        "provider": provider,
        "model": model,
        "chunk_size": chunk_size if chunk_size is not None else UNKNOWN,
        "translation_status": status,
        "status_tags": tags,
        "source_sha256": sha256_file(source),
        "translation_sha256": sha256_file(path),
        "has_manual_review": has_review,
        "review_path": review_path,
        "metadata_evidence_path": _relative(metadata_path, root) if metadata_path else None,
        "usable_for_quality_analysis": usable,
    }


def build_inventory(root: str | Path) -> dict[str, Any]:
    base = Path(root).resolve()
    items = [_record(path, base) for path in discover_translation_artifacts(base)]
    return {
        "schema_version": SCHEMA_VERSION,
        "corpus": "NTPE Translation Intelligence Corpus",
        "batch": "Batch 1 - Historical Translation Corpus Inventory",
        "status": "TIC Batch 1 Completed",
        "next_batch_status": "TIC Batch 2 Not Started",
        "deterministic": True,
        "scan_scope": {
            "repository_root": ".",
            "required_locations": [
                {"path": location, "present": (base / location).exists()}
                for location in REQUIRED_SCAN_LOCATIONS
            ],
            "candidate_rules": [
                "all translation.txt",
                "all *_zh.txt and *_zh.partial.txt",
                "translation_cache/*_result.json",
                "human-reviewed translation TXT",
            ],
            "excluded_generated_path": "artifacts/tic_batch1",
        },
        "items": items,
    }


def build_statistics(inventory: dict[str, Any]) -> dict[str, Any]:
    items = inventory["items"]
    successful = sum(item["translation_status"] in {"Completed Translation", "Manual Reviewed"} for item in items)
    partial = sum("Partial Translation" in item["status_tags"] for item in items)
    timeout = sum(item["translation_status"] == "Provider Timeout" for item in items)
    reviewed = sum(item["has_manual_review"] for item in items)
    golden = sum("/Golden_Set/" in f"/{item['translation_file']}/" for item in items)
    regression = sum(item["translation_file"].startswith("tests/literary/outputs/") for item in items)
    provider = sum(item["provider"] not in {UNKNOWN, "none (dry-run)"} for item in items)
    available = sum(item["usable_for_quality_analysis"] for item in items)
    denominator = sum(item["translation_status"] != "Historical Translation" for item in items)
    coverage = round((successful / denominator * 100.0), 2) if denominator else 0.0
    return {
        "schema_version": "tic.batch1.statistics.v1",
        "historical_translations": len(items),
        "successful_translations": successful,
        "partial_translations": partial,
        "timeout_translations": timeout,
        "manual_reviews": reviewed,
        "golden_outputs": golden,
        "regression_outputs": regression,
        "provider_outputs": provider,
        "translation_coverage": {
            "successful_numerator": successful,
            "attempted_denominator": denominator,
            "percent": coverage,
        },
        "available_quality_evidence": available,
        "status_counts": {
            status: sum(item["translation_status"] == status for item in items)
            for status in (
                "Completed Translation",
                "Partial Translation",
                "Provider Timeout",
                "Manual Reviewed",
                "Historical Translation",
            )
        },
    }


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def generate_batch1_artifacts(root: str | Path) -> tuple[Path, Path, Path]:
    base = Path(root).resolve()
    inventory = build_inventory(base)
    statistics = build_statistics(inventory)
    inventory_path = base / INVENTORY_PATH
    statistics_path = base / STATISTICS_PATH
    manifest_path = base / ARTIFACT_MANIFEST_PATH
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_bytes(_canonical_json(inventory))
    statistics_path.write_bytes(_canonical_json(statistics))
    artifact_manifest = {
        "schema_version": "tic.batch1.artifact-manifest.v1",
        "batch": "TIC Batch 1",
        "status": "completed",
        "files": {
            INVENTORY_PATH.as_posix(): sha256_file(inventory_path),
            STATISTICS_PATH.as_posix(): sha256_file(statistics_path),
        },
        "boundaries": {
            "inventory_only": True,
            "network_requests": 0,
            "provider_executed": False,
            "new_translation_generated": False,
            "translation_files_modified": False,
            "runtime_modified": False,
            "prompt_modified": False,
            "stage_11_modified": False,
            "stage_12_modified": False,
            "batch_2_started": False,
        },
        "self_hash_excluded": True,
    }
    manifest_path.write_bytes(_canonical_json(artifact_manifest))
    return inventory_path, statistics_path, manifest_path


def generate_root_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    missing = [name for name in ROOT_MANIFEST_FILES if not (base / name).is_file()]
    if missing:
        raise FileNotFoundError(f"TIC Batch 1 manifest inputs missing: {missing}")
    payload = {
        "schema_version": "tic.batch1.release-manifest.v1",
        "corpus": "NTPE Translation Intelligence Corpus",
        "batch": "Batch 1 - Historical Translation Corpus Inventory",
        "status": "TIC Batch 1 Completed",
        "next_batch_status": "TIC Batch 2 Not Started",
        "files": {name: sha256_file(base / name) for name in ROOT_MANIFEST_FILES},
        "tests": {
            "root": "ntpe_tic_batch1_translation_corpus_inventory_test.py",
            "focused_integration": "tests/integration/tic_batch1_translation_corpus_inventory_test.py",
        },
        "boundaries": {
            "inventory_only": True,
            "provider_calls_added": 0,
            "provider_executed": False,
            "new_translation_generated": False,
            "failure_classification_created": False,
            "quality_scoring_performed": False,
            "prompt_modified": False,
            "runtime_modified": False,
            "batch_2_started": False,
        },
        "sha256": {"algorithm": "sha256", "self_hash_excluded": True},
    }
    target = base / ROOT_MANIFEST_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canonical_json(payload))
    return target
