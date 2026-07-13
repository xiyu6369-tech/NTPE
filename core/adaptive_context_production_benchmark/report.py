from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .model import BenchmarkComparison, BenchmarkContract, BenchmarkRun, ChunkEvidence

FORBIDDEN_KEYS = {"text", "source_text", "translation", "prompt", "previous_context", "api_key", "provider_response", "response_body", "chunks"}


def _canonical(payload: Mapping[str, Any]) -> bytes:
    clean = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    return json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _assert_redacted(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_KEYS or normalized.endswith("_text"):
                raise ValueError(f"forbidden benchmark field: {'.'.join((*path, str(key)))}")
            _assert_redacted(child, (*path, str(key)))
    elif isinstance(value, (list, tuple)):
        for child in value: _assert_redacted(child, path)


def write_artifact(value: BenchmarkRun | BenchmarkComparison | Mapping[str, Any], path: str | Path) -> Path:
    payload = value.to_dict() if hasattr(value, "to_dict") else dict(value)
    payload["content_redacted"] = True
    _assert_redacted(payload)
    payload["artifact_sha256"] = {"algorithm": "sha256", "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest()}
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_run(path: str | Path) -> BenchmarkRun:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("artifact_sha256", {})
    if integrity.get("payload_sha256") != hashlib.sha256(_canonical(payload)).hexdigest():
        raise ValueError("benchmark artifact integrity failure")
    _assert_redacted(payload)
    contract = BenchmarkContract(**payload.pop("contract"))
    chunks = tuple(ChunkEvidence(**row) for row in payload.pop("chunk_evidence", ()))
    payload.pop("version", None)
    return BenchmarkRun(contract=contract, chunks=chunks, **payload)
