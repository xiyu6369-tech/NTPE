from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Set


@dataclass
class CheckpointValidationResult:
    valid: bool
    processed: int = 0
    missing: int = 0
    duplicates: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "processed": int(self.processed),
            "missing": int(self.missing),
            "duplicates": int(self.duplicates),
        }


class CheckpointValidator:
    def build_checkpoint(self, processed_ids: Iterable[str]) -> Dict[str, Any]:
        items = list(processed_ids)
        return {"processed_ids": items, "processed_count": len(items)}

    def validate(self, checkpoint: Dict[str, Any], expected_ids: Iterable[str] | None = None) -> CheckpointValidationResult:
        processed_ids = list(checkpoint.get("processed_ids", []))
        unique: Set[str] = set(processed_ids)
        duplicates = len(processed_ids) - len(unique)
        missing = 0
        if expected_ids is not None:
            expected = set(expected_ids)
            missing = len(expected - unique)
        return CheckpointValidationResult(
            valid=(duplicates == 0 and missing == 0 and checkpoint.get("processed_count", len(processed_ids)) == len(processed_ids)),
            processed=len(processed_ids),
            missing=missing,
            duplicates=duplicates,
        )


def validate_checkpoint(checkpoint: Dict[str, Any], expected_ids: Iterable[str] | None = None) -> CheckpointValidationResult:
    return CheckpointValidator().validate(checkpoint, expected_ids=expected_ids)
