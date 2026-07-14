from __future__ import annotations

from dataclasses import dataclass

FREEZE_VERSION = "7.0.0-stage10.8"


@dataclass(frozen=True)
class FakeTransportFreezeContract:
    enabled: bool = False
    authorization_id: str = ""
    session_id: str = ""
    source_fingerprint: str = ""
    chunk_fingerprint: str = ""
    single_chunk_only: bool = True
    single_controlled_session: bool = True

    def validate(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if not self.enabled:
            blockers.append("provider-execution-freeze-explicit-opt-in-required")
        if not self.authorization_id.strip():
            blockers.append("provider-execution-freeze-authorization-id-required")
        if not self.session_id.strip():
            blockers.append("provider-execution-freeze-session-id-required")
        for label, value in (
            ("source", self.source_fingerprint),
            ("chunk", self.chunk_fingerprint),
        ):
            normalized = value.strip().lower()
            if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
                blockers.append(f"provider-execution-freeze-{label}-fingerprint-invalid")
        if not self.single_chunk_only:
            blockers.append("provider-execution-freeze-single-chunk-required")
        if not self.single_controlled_session:
            blockers.append("provider-execution-freeze-single-session-required")
        return tuple(blockers)
