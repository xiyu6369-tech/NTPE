from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .models import HookEvidence


class DisabledEvidenceSink:
    kind = "disabled"

    def write(self, evidence: HookEvidence) -> None:
        return None


class InMemoryEvidenceSink:
    kind = "in_memory"

    def __init__(self) -> None:
        self.records: list[HookEvidence] = []

    def write(self, evidence: HookEvidence) -> None:
        self.records.append(evidence)


class AtomicTestFileEvidenceSink:
    kind = "test_file_sink"

    def __init__(self, path: Path, *, allowed_root: Path) -> None:
        self.allowed_root = allowed_root.resolve()
        self.path = path

    def _resolved_path(self) -> Path:
        target = self.path.resolve()
        try:
            target.relative_to(self.allowed_root)
        except ValueError as exc:
            raise ValueError("evidence path escapes allowed root") from exc
        if self.path.is_symlink() or any(parent.is_symlink() for parent in self.path.parents if parent != self.allowed_root.parent):
            raise ValueError("symlink evidence path is forbidden")
        return target

    def write(self, evidence: HookEvidence) -> None:
        target = self._resolved_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(evidence), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        fd, temporary = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
