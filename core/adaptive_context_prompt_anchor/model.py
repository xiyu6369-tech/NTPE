from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptContextAnchor:
    version: str
    strategy: str
    addressable: bool
    reason: str
    start: int
    end: int
    content_sha256: str
    source_sha256: str

    @property
    def length(self) -> int:
        return max(0, self.end - self.start)

    def to_metadata(self) -> dict[str, object]:
        return {
            "version": self.version,
            "strategy": self.strategy,
            "addressable": self.addressable,
            "reason": self.reason,
            "start": self.start,
            "end": self.end,
            "length": self.length,
            "content_sha256": self.content_sha256,
            "source_sha256": self.source_sha256,
            "content_redacted": True,
        }
