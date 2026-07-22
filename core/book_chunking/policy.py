from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .errors import InvalidChunkPolicyError


FINDING_CODES = (
    "EMPTY_CONTENT",
    "SOURCE_FINGERPRINT_MISMATCH",
    "SEGMENTATION_NOT_READY",
    "NO_STRUCTURED_SECTIONS",
    "SECTION_EXCEEDS_MAXIMUM",
    "HARD_SPLIT_REQUIRED",
    "HEADING_PROTECTION_LIMITED",
    "HEADING_SPLIT_DETECTED",
    "CHUNK_BELOW_MINIMUM",
    "CHUNK_EXCEEDS_MAXIMUM",
    "MULTI_SECTION_CHUNK",
    "HIGH_CHUNK_SIZE_VARIANCE",
    "EXCESSIVE_CHUNK_COUNT",
    "OFFSET_GAP",
    "OFFSET_OVERLAP",
    "RECONSTRUCTION_MISMATCH",
    "INVALID_SECTION_REFERENCE",
)

FINDING_SEVERITIES = MappingProxyType(
    {
        "EMPTY_CONTENT": "warning",
        "SOURCE_FINGERPRINT_MISMATCH": "blocking",
        "SEGMENTATION_NOT_READY": "warning",
        "NO_STRUCTURED_SECTIONS": "warning",
        "SECTION_EXCEEDS_MAXIMUM": "warning",
        "HARD_SPLIT_REQUIRED": "warning",
        "HEADING_PROTECTION_LIMITED": "warning",
        "HEADING_SPLIT_DETECTED": "blocking",
        "CHUNK_BELOW_MINIMUM": "warning",
        "CHUNK_EXCEEDS_MAXIMUM": "blocking",
        "MULTI_SECTION_CHUNK": "warning",
        "HIGH_CHUNK_SIZE_VARIANCE": "warning",
        "EXCESSIVE_CHUNK_COUNT": "warning",
        "OFFSET_GAP": "blocking",
        "OFFSET_OVERLAP": "blocking",
        "RECONSTRUCTION_MISMATCH": "blocking",
        "INVALID_SECTION_REFERENCE": "blocking",
    }
)

STATUS_ACTIONS = MappingProxyType(
    {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }
)


@dataclass(frozen=True)
class ChunkingPolicy:
    strategy: str
    minimum_chunk_size: int
    target_chunk_size: int
    maximum_chunk_size: int
    maximum_heading_protection_length: int
    boundary_priority: tuple[str, ...]
    supported_boundary_types: tuple[str, ...]
    isolated_section_types: tuple[str, ...]
    status_actions: Mapping[str, str]
    finding_codes: tuple[str, ...]
    finding_severities: Mapping[str, str]
    hard_split_review_count: int
    excessive_chunk_count: int
    size_variance_ratio: float
    size_variance_difference: int
    protected_closing_characters: str

    def __post_init__(self) -> None:
        validate_chunk_sizes(
            self.minimum_chunk_size,
            self.target_chunk_size,
            self.maximum_chunk_size,
        )
        if self.maximum_heading_protection_length <= 0:
            raise InvalidChunkPolicyError(
                "maximum_heading_protection_length must be positive"
            )
        if self.boundary_priority != ("paragraph", "sentence", "line", "hard_limit"):
            raise InvalidChunkPolicyError("boundary_priority must remain deterministic")
        if set(self.boundary_priority) - set(self.supported_boundary_types):
            raise InvalidChunkPolicyError("boundary_priority contains an unsupported type")
        if not isinstance(self.status_actions, MappingProxyType):
            raise InvalidChunkPolicyError("status_actions must be immutable")
        if not isinstance(self.finding_severities, MappingProxyType):
            raise InvalidChunkPolicyError("finding_severities must be immutable")


def validate_chunk_sizes(minimum: int, target: int, maximum: int) -> None:
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (minimum, target, maximum)):
        raise InvalidChunkPolicyError("chunk sizes must be integers")
    if not 0 < minimum <= target <= maximum:
        raise InvalidChunkPolicyError(
            "chunk sizes must satisfy 0 < minimum <= target <= maximum"
        )


DEFAULT_POLICY = ChunkingPolicy(
    strategy="deterministic_section_aware_chunking_v1",
    minimum_chunk_size=800,
    target_chunk_size=2000,
    maximum_chunk_size=2600,
    maximum_heading_protection_length=400,
    boundary_priority=("paragraph", "sentence", "line", "hard_limit"),
    supported_boundary_types=(
        "section_start", "section_end", "paragraph", "sentence", "line", "hard_limit"
    ),
    isolated_section_types=("front_matter", "unclassified"),
    status_actions=STATUS_ACTIONS,
    finding_codes=FINDING_CODES,
    finding_severities=FINDING_SEVERITIES,
    hard_split_review_count=10,
    excessive_chunk_count=1000,
    size_variance_ratio=10.0,
    size_variance_difference=800,
    protected_closing_characters="」』”’\"'",
)
