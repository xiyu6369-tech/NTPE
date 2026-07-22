from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Pattern


@dataclass(frozen=True)
class HeadingPattern:
    code: str
    family: str
    expression: Pattern[str]
    confidence: float
    section_type: str = "chapter"


@dataclass(frozen=True)
class SegmentationPolicy:
    strategy: str
    heading_patterns: tuple[HeadingPattern, ...]
    maximum_heading_length: int
    numeric_maximum_digits: int
    numeric_confidence: float
    supported_section_types: tuple[str, ...]
    statuses: tuple[str, ...]
    actions: tuple[str, ...]
    status_actions: Mapping[str, str]
    finding_codes: tuple[str, ...]
    finding_severities: Mapping[str, str]
    extreme_section_minimum: int
    section_size_ratio_threshold: float
    section_size_difference_threshold: int


FINDING_CODES = (
    "EMPTY_CONTENT",
    "NO_CHAPTER_HEADING_DETECTED",
    "SINGLE_HEADING_ONLY",
    "FRONT_MATTER_PRESENT",
    "MIXED_HEADING_STYLES",
    "NON_SEQUENTIAL_NUMBERING",
    "DUPLICATE_CHAPTER_NUMBER",
    "WEAK_HEADING_CANDIDATE_IGNORED",
    "NUMERIC_HEADING_SEQUENCE_UNCONFIRMED",
    "EXTREME_SECTION_SIZE",
    "HIGH_SECTION_SIZE_VARIANCE",
    "RECONSTRUCTION_MISMATCH",
    "OFFSET_GAP",
    "OFFSET_OVERLAP",
    "SOURCE_FINGERPRINT_MISMATCH",
)

FINDING_SEVERITIES = MappingProxyType(
    {
        "EMPTY_CONTENT": "warning",
        "NO_CHAPTER_HEADING_DETECTED": "warning",
        "SINGLE_HEADING_ONLY": "warning",
        "FRONT_MATTER_PRESENT": "warning",
        "MIXED_HEADING_STYLES": "warning",
        "NON_SEQUENTIAL_NUMBERING": "warning",
        "DUPLICATE_CHAPTER_NUMBER": "warning",
        "WEAK_HEADING_CANDIDATE_IGNORED": "warning",
        "NUMERIC_HEADING_SEQUENCE_UNCONFIRMED": "warning",
        "EXTREME_SECTION_SIZE": "warning",
        "HIGH_SECTION_SIZE_VARIANCE": "warning",
        "RECONSTRUCTION_MISMATCH": "blocking",
        "OFFSET_GAP": "blocking",
        "OFFSET_OVERLAP": "blocking",
        "SOURCE_FINGERPRINT_MISMATCH": "blocking",
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

_CJK_NUMBER = r"[0-9〇零一二三四五六七八九十百千兩两壹貳贰參叁肆伍陸陆柒捌玖拾佰仟]+"
_ENGLISH_NUMBER = (
    r"(?:[0-9]+|[IVXLCDM]+|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|"
    r"ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|"
    r"NINETEEN|TWENTY(?:[- ](?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE))?)"
)

DEFAULT_POLICY = SegmentationPolicy(
    strategy="deterministic_heading_lines_v1",
    heading_patterns=(
        HeadingPattern(
            "CJK_NUMBERED_CHAPTER",
            "cjk",
            re.compile(rf"^第\s*({_CJK_NUMBER})\s*(章|回|篇|部|幕)$"),
            0.99,
        ),
        HeadingPattern(
            "CJK_NUMBERED_VOLUME",
            "cjk",
            re.compile(rf"^(?:第\s*({_CJK_NUMBER})\s*卷|卷\s*({_CJK_NUMBER}))$"),
            0.98,
        ),
        HeadingPattern(
            "CJK_NAMED_HEADING",
            "cjk",
            re.compile(rf"^(序章|楔子|終章|终章|尾聲|尾声|番外(?:\s*{_CJK_NUMBER})?|後記|后记)$"),
            0.98,
        ),
        HeadingPattern(
            "CJK_APPENDIX",
            "cjk",
            re.compile(r"^(附錄|附录)$"),
            0.98,
            "appendix",
        ),
        HeadingPattern(
            "KOREAN_NUMBERED_CHAPTER",
            "korean",
            re.compile(r"^(?:제\s*)?([0-9]+)\s*장$"),
            0.99,
        ),
        HeadingPattern(
            "KOREAN_NAMED_HEADING",
            "korean",
            re.compile(r"^(서장|프롤로그|에필로그|외전|후기)$"),
            0.98,
        ),
        HeadingPattern(
            "JAPANESE_NAMED_HEADING",
            "japanese",
            re.compile(r"^(プロローグ|エピローグ|後書き)$"),
            0.98,
        ),
        HeadingPattern(
            "JAPANESE_INTERLUDE",
            "japanese",
            re.compile(r"^幕間$"),
            0.98,
            "interlude",
        ),
        HeadingPattern(
            "ENGLISH_NUMBERED_CHAPTER",
            "english",
            re.compile(rf"^CHAPTER\s+({_ENGLISH_NUMBER})$", re.IGNORECASE),
            0.99,
        ),
        HeadingPattern(
            "ENGLISH_NAMED_HEADING",
            "english",
            re.compile(r"^(PROLOGUE|EPILOGUE)$", re.IGNORECASE),
            0.98,
        ),
        HeadingPattern(
            "ENGLISH_INTERLUDE",
            "english",
            re.compile(r"^INTERLUDE$", re.IGNORECASE),
            0.98,
            "interlude",
        ),
        HeadingPattern(
            "ENGLISH_APPENDIX",
            "english",
            re.compile(r"^(APPENDIX|AFTERWORD)$", re.IGNORECASE),
            0.98,
            "appendix",
        ),
    ),
    maximum_heading_length=80,
    numeric_maximum_digits=3,
    numeric_confidence=0.78,
    supported_section_types=(
        "front_matter",
        "chapter",
        "interlude",
        "appendix",
        "unclassified",
    ),
    statuses=("ready", "ready_with_warnings", "manual_review", "blocked"),
    actions=("proceed", "proceed_with_warning", "manual_review", "reject"),
    status_actions=STATUS_ACTIONS,
    finding_codes=FINDING_CODES,
    finding_severities=FINDING_SEVERITIES,
    extreme_section_minimum=10_000,
    section_size_ratio_threshold=10.0,
    section_size_difference_threshold=1_000,
)
