"""Atomic deterministic Stage 7.4 checkpoint persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from core.controlled_translation_runtime_integration.serialization import canonical_json

from .errors import ControlledMultiChunkCheckpointError
from .models import CheckpointRecord


def write_checkpoint_atomic(checkpoint: CheckpointRecord, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    if temporary.exists():
        raise ControlledMultiChunkCheckpointError("checkpoint temporary path occupied")
    payload = json.loads(canonical_json({
        **checkpoint.__dict__,
        "schema": checkpoint.schema,
        "version": checkpoint.version,
        "checkpoint_fingerprint": checkpoint.checkpoint_fingerprint,
    }))
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(
                payload, stream, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        verified = read_checkpoint(target)
    except (OSError, TypeError, ValueError) as error:
        if temporary.exists():
            temporary.unlink()
        raise ControlledMultiChunkCheckpointError(
            "checkpoint atomic write failed"
        ) from error
    if verified.checkpoint_fingerprint != checkpoint.checkpoint_fingerprint:
        raise ControlledMultiChunkCheckpointError("checkpoint read-back mismatch")


def read_checkpoint(path: str | Path) -> CheckpointRecord:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        fingerprint = payload.pop("checkpoint_fingerprint")
        if (
            payload.pop("schema", None) != "ntpe.controlled_translation_checkpoint"
            or payload.pop("version", None) != "1.0"
        ):
            raise ValueError("unknown checkpoint schema")
        for key in ("completed_chunk_ids", "output_fingerprints", "artifact_paths"):
            payload[key] = tuple(payload[key])
        checkpoint = CheckpointRecord(**payload)
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ControlledMultiChunkCheckpointError("checkpoint invalid") from error
    if checkpoint.checkpoint_fingerprint != fingerprint:
        raise ControlledMultiChunkCheckpointError("checkpoint fingerprint mismatch")
    return checkpoint
