from dataclasses import FrozenInstanceError, replace
from types import MappingProxyType

import pytest

from core.book_chunking import BookChunkPlanner
from core.book_chunking.errors import InvalidChunkPolicyError
from core.book_chunking.policy import DEFAULT_POLICY
from core.book_segmentation import BookStructureSegmenter


def test_default_policy_values_and_order_are_fixed() -> None:
    assert DEFAULT_POLICY.minimum_chunk_size == 800
    assert DEFAULT_POLICY.target_chunk_size == 2000
    assert DEFAULT_POLICY.maximum_chunk_size == 2600
    assert DEFAULT_POLICY.boundary_priority == (
        "paragraph", "sentence", "line", "hard_limit"
    )
    assert DEFAULT_POLICY.status_actions == {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }


def test_policy_and_finding_collections_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        DEFAULT_POLICY.target_chunk_size = 10
    assert isinstance(DEFAULT_POLICY.finding_codes, tuple)
    assert isinstance(DEFAULT_POLICY.finding_severities, MappingProxyType)
    with pytest.raises(TypeError):
        DEFAULT_POLICY.finding_severities["EMPTY_CONTENT"] = "info"


@pytest.mark.parametrize(
    ("minimum", "target", "maximum"),
    [(0, 1, 2), (2, 1, 3), (1, 4, 3), (-1, 1, 1), (True, 2, 3), (1.0, 2, 3)],
)
def test_invalid_sizes_are_rejected(minimum, target, maximum) -> None:
    segmentation = BookStructureSegmenter().segment_text(
        "Chapter 1\nText", source_name="book.txt"
    )
    with pytest.raises(InvalidChunkPolicyError):
        BookChunkPlanner().plan(
            segmentation,
            minimum_chunk_size=minimum,
            target_chunk_size=target,
            maximum_chunk_size=maximum,
        )


def test_invalid_custom_policy_is_rejected() -> None:
    with pytest.raises(InvalidChunkPolicyError):
        replace(DEFAULT_POLICY, minimum_chunk_size=3000)


def test_required_finding_codes_are_centralized() -> None:
    assert set(DEFAULT_POLICY.finding_codes) == {
        "EMPTY_CONTENT", "SOURCE_FINGERPRINT_MISMATCH", "SEGMENTATION_NOT_READY",
        "NO_STRUCTURED_SECTIONS", "SECTION_EXCEEDS_MAXIMUM", "HARD_SPLIT_REQUIRED",
        "HEADING_PROTECTION_LIMITED", "HEADING_SPLIT_DETECTED", "CHUNK_BELOW_MINIMUM",
        "CHUNK_EXCEEDS_MAXIMUM", "MULTI_SECTION_CHUNK", "HIGH_CHUNK_SIZE_VARIANCE",
        "EXCESSIVE_CHUNK_COUNT", "OFFSET_GAP", "OFFSET_OVERLAP",
        "RECONSTRUCTION_MISMATCH", "INVALID_SECTION_REFERENCE",
    }
