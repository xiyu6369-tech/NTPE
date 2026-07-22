from types import MappingProxyType

import pytest

from core.book_segmentation.policy import DEFAULT_POLICY


def test_policy_is_frozen_and_collections_are_immutable() -> None:
    with pytest.raises(AttributeError):
        DEFAULT_POLICY.maximum_heading_length = 100
    assert isinstance(DEFAULT_POLICY.heading_patterns, tuple)
    assert isinstance(DEFAULT_POLICY.supported_section_types, tuple)
    assert isinstance(DEFAULT_POLICY.finding_codes, tuple)
    assert isinstance(DEFAULT_POLICY.finding_severities, MappingProxyType)
    with pytest.raises(TypeError):
        DEFAULT_POLICY.finding_severities["EMPTY_CONTENT"] = "info"


def test_policy_centralizes_required_values() -> None:
    assert set(("front_matter", "chapter", "interlude", "appendix", "unclassified")) <= set(DEFAULT_POLICY.supported_section_types)
    assert DEFAULT_POLICY.status_actions == {
        "ready": "proceed",
        "ready_with_warnings": "proceed_with_warning",
        "manual_review": "manual_review",
        "blocked": "reject",
    }
    required = {
        "EMPTY_CONTENT", "NO_CHAPTER_HEADING_DETECTED", "SINGLE_HEADING_ONLY",
        "FRONT_MATTER_PRESENT", "MIXED_HEADING_STYLES",
        "NON_SEQUENTIAL_NUMBERING", "DUPLICATE_CHAPTER_NUMBER",
        "WEAK_HEADING_CANDIDATE_IGNORED", "NUMERIC_HEADING_SEQUENCE_UNCONFIRMED",
        "EXTREME_SECTION_SIZE", "HIGH_SECTION_SIZE_VARIANCE",
        "RECONSTRUCTION_MISMATCH", "OFFSET_GAP", "OFFSET_OVERLAP",
        "SOURCE_FINGERPRINT_MISMATCH",
    }
    assert required == set(DEFAULT_POLICY.finding_codes)
