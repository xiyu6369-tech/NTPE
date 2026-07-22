from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath

from core.book_intake import BookIntakeManifest, BookIntakeResult

from .errors import (
    InvalidSegmentationInputError,
    SegmentationInvariantError,
    SourceFingerprintMismatchError,
)
from .models import (
    BookSection,
    BookSegmentationResult,
    ChapterHeading,
    FindingValue,
    SegmentationFinding,
)
from .policy import DEFAULT_POLICY, HeadingPattern, SegmentationPolicy


@dataclass(frozen=True)
class _Line:
    index: int
    start: int
    end: int
    content_end: int
    raw: str
    content: str
    stripped: str


@dataclass(frozen=True)
class _Candidate:
    line: _Line
    heading: ChapterHeading
    family: str
    section_type: str
    number: int | None


_LINE_ENDINGS = "\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029"
_WEAK_PREFIX = re.compile(
    r"^(?:第\s*[0-9〇零一二三四五六七八九十百千]+\s*[章卷回篇]|卷\s*[0-9一二三四五六七八九十]+|"
    r"CHAPTER\s+\S+|(?:제\s*)?[0-9]+\s*장)\b",
    re.IGNORECASE,
)
_ENGLISH_NUMBERS = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
    "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
    "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14,
    "FIFTEEN": 15, "SIXTEEN": 16, "SEVENTEEN": 17, "EIGHTEEN": 18,
    "NINETEEN": 19, "TWENTY": 20,
}


class _FindingCollector:
    def __init__(self, policy: SegmentationPolicy) -> None:
        self._policy = policy
        self._items: dict[tuple[str, int | None, FindingValue], SegmentationFinding] = {}

    def add(
        self,
        code: str,
        message: str,
        section_index: int | None = None,
        observed_value: FindingValue = None,
    ) -> None:
        key = (code, section_index, observed_value)
        self._items.setdefault(
            key,
            SegmentationFinding(
                code, self._policy.finding_severities[code], message,
                section_index, observed_value,
            ),
        )

    def ordered(self) -> tuple[SegmentationFinding, ...]:
        rank = {code: index for index, code in enumerate(self._policy.finding_codes)}
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (
                    rank[item.code],
                    -1 if item.section_index is None else item.section_index,
                    "" if item.observed_value is None else str(item.observed_value),
                ),
            )
        )


class BookStructureSegmenter:
    """Pure, offline, deterministic segmentation of already-decoded book text."""

    def __init__(self, policy: SegmentationPolicy = DEFAULT_POLICY) -> None:
        if not isinstance(policy, SegmentationPolicy):
            raise InvalidSegmentationInputError("policy must be a SegmentationPolicy")
        self._policy = policy

    def segment(
        self,
        intake_result: BookIntakeResult,
        *,
        manifest: BookIntakeManifest | None = None,
    ) -> BookSegmentationResult:
        """Segment a frozen Intake result without rerunning any Intake analyzer."""
        if not isinstance(intake_result, BookIntakeResult):
            raise InvalidSegmentationInputError(
                "intake_result must be a BookIntakeResult"
            )
        if manifest is not None and not isinstance(manifest, BookIntakeManifest):
            raise InvalidSegmentationInputError(
                "manifest must be a BookIntakeManifest or None"
            )
        fingerprint = _source_fingerprint(intake_result.text)
        if manifest is not None and manifest.content_fingerprint != fingerprint:
            raise SourceFingerprintMismatchError(
                "Manifest content fingerprint does not match Intake text."
            )
        return self.segment_text(intake_result.text, source_name=intake_result.file_name)

    def segment_text(self, text: str, *, source_name: str) -> BookSegmentationResult:
        if not isinstance(text, str):
            raise InvalidSegmentationInputError("text must be a str")
        if not isinstance(source_name, str) or not source_name:
            raise InvalidSegmentationInputError("source_name must be a non-empty str")

        safe_name = _safe_source_name(source_name)
        source_fingerprint = _source_fingerprint(text)
        lines = _make_lines(text)
        findings = _FindingCollector(self._policy)
        candidates = self._detect_candidates(lines, findings)
        sections = self._build_sections(text, lines, candidates, findings)
        self._add_structure_findings(candidates, sections, findings)
        ordered_findings = findings.ordered()
        self._validate_invariants(text, sections)

        if not text:
            status = "manual_review"
        elif not candidates:
            status = "manual_review"
        elif any(item.severity == "blocking" for item in ordered_findings):
            status = "blocked"
        elif ordered_findings:
            status = "ready_with_warnings"
        else:
            status = "ready"
        action = self._policy.status_actions[status]
        chapter_count = sum(section.section_type == "chapter" for section in sections)
        covered = sum(section.character_count for section in sections)
        summary = _summary(status, len(sections), len(candidates))
        payload = _fingerprint_payload(
            source_fingerprint=source_fingerprint,
            strategy=self._policy.strategy,
            sections=sections,
            findings=ordered_findings,
            status=status,
            action=action,
            chapter_count=chapter_count,
        )
        segmentation_fingerprint = hashlib.sha256(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        return BookSegmentationResult(
            source_name=safe_name,
            source_content_fingerprint=source_fingerprint,
            strategy=self._policy.strategy,
            sections=sections,
            chapter_count=chapter_count,
            front_matter_count=sum(s.section_type == "front_matter" for s in sections),
            unclassified_count=sum(s.section_type == "unclassified" for s in sections),
            character_count=len(text),
            covered_character_count=covered,
            coverage_ratio=1.0 if not text else covered / len(text),
            status=status,
            action=action,
            findings=ordered_findings,
            summary=summary,
            segmentation_fingerprint=segmentation_fingerprint,
        )

    def _detect_candidates(
        self, lines: tuple[_Line, ...], findings: _FindingCollector
    ) -> tuple[_Candidate, ...]:
        explicit: list[_Candidate] = []
        numeric_lines: list[tuple[_Line, int]] = []
        for line in lines:
            label = line.stripped
            if not label:
                continue
            if len(label) > self._policy.maximum_heading_length:
                continue
            matched = False
            for pattern in self._policy.heading_patterns:
                match = pattern.expression.fullmatch(label)
                if match:
                    explicit.append(self._candidate(line, pattern, match))
                    matched = True
                    break
            if matched:
                continue
            if (
                label.isascii()
                and label.isdigit()
                and len(label) <= self._policy.numeric_maximum_digits
                and self._is_isolated(lines, line.index)
            ):
                numeric_lines.append((line, int(label)))
            elif _WEAK_PREFIX.match(label):
                findings.add(
                    "WEAK_HEADING_CANDIDATE_IGNORED",
                    "A heading-like line did not satisfy the exact heading policy.",
                    observed_value=line.index,
                )

        confirmed_indexes: set[int] = set()
        for left, right in zip(numeric_lines, numeric_lines[1:]):
            if right[1] == left[1] + 1:
                confirmed_indexes.update((left[0].index, right[0].index))
        numeric: list[_Candidate] = []
        for line, number in numeric_lines:
            if line.index in confirmed_indexes:
                heading = ChapterHeading(
                    text=line.content,
                    normalized_label=line.stripped,
                    line_index=line.index,
                    character_start=line.start,
                    character_end=line.content_end,
                    pattern_code="PURE_NUMERIC_SEQUENCE",
                    confidence=self._policy.numeric_confidence,
                )
                numeric.append(_Candidate(line, heading, "pure_numeric", "chapter", number))
            else:
                findings.add(
                    "NUMERIC_HEADING_SEQUENCE_UNCONFIRMED",
                    "An isolated numeric line was ignored because no consecutive sequence confirmed it.",
                    observed_value=line.index,
                )
        return tuple(sorted((*explicit, *numeric), key=lambda item: item.line.start))

    def _candidate(
        self, line: _Line, pattern: HeadingPattern, match: re.Match[str]
    ) -> _Candidate:
        return _Candidate(
            line=line,
            heading=ChapterHeading(
                text=line.content,
                normalized_label=" ".join(line.stripped.casefold().split()),
                line_index=line.index,
                character_start=line.start,
                character_end=line.content_end,
                pattern_code=pattern.code,
                confidence=pattern.confidence,
            ),
            family=pattern.family,
            section_type=pattern.section_type,
            number=_extract_number(pattern.code, match, line.stripped),
        )

    @staticmethod
    def _is_isolated(lines: tuple[_Line, ...], index: int) -> bool:
        before_blank = index == 0 or not lines[index - 1].stripped
        after_blank = index == len(lines) - 1 or not lines[index + 1].stripped
        return before_blank and after_blank

    def _build_sections(
        self,
        text: str,
        lines: tuple[_Line, ...],
        candidates: tuple[_Candidate, ...],
        findings: _FindingCollector,
    ) -> tuple[BookSection, ...]:
        if not text:
            findings.add("EMPTY_CONTENT", "The source content is empty.", observed_value=0)
            return ()
        if not candidates:
            findings.add(
                "NO_CHAPTER_HEADING_DETECTED",
                "No reliable chapter heading was detected.",
                observed_value=0,
            )
            return (self._section(0, "unclassified", None, text, 0, len(text), 0, len(lines)),)

        sections: list[BookSection] = []
        if candidates[0].line.start > 0:
            sections.append(
                self._section(
                    0, "front_matter", None, text, 0, candidates[0].line.start,
                    0, candidates[0].line.index,
                )
            )
            findings.add(
                "FRONT_MATTER_PRESENT",
                "Content before the first reliable heading was preserved as front matter.",
                section_index=0,
                observed_value=candidates[0].line.start,
            )
        for candidate_index, candidate in enumerate(candidates):
            end = (
                candidates[candidate_index + 1].line.start
                if candidate_index + 1 < len(candidates)
                else len(text)
            )
            line_end = (
                candidates[candidate_index + 1].line.index
                if candidate_index + 1 < len(candidates)
                else len(lines)
            )
            sections.append(
                self._section(
                    len(sections), candidate.section_type, candidate.heading, text,
                    candidate.line.start, end, candidate.line.index, line_end,
                )
            )
        return tuple(sections)

    @staticmethod
    def _section(
        index: int,
        section_type: str,
        heading: ChapterHeading | None,
        source: str,
        start: int,
        end: int,
        line_start: int,
        line_end: int,
    ) -> BookSection:
        value = source[start:end]
        return BookSection(
            index=index,
            section_type=section_type,
            heading=heading,
            text=value,
            character_start=start,
            character_end=end,
            line_start=line_start,
            line_end=line_end,
            character_count=len(value),
            non_whitespace_character_count=sum(not char.isspace() for char in value),
        )

    def _add_structure_findings(
        self,
        candidates: tuple[_Candidate, ...],
        sections: tuple[BookSection, ...],
        findings: _FindingCollector,
    ) -> None:
        if len(candidates) == 1:
            findings.add(
                "SINGLE_HEADING_ONLY",
                "Only one reliable heading was detected.",
                observed_value=1,
            )
        families = tuple(dict.fromkeys(candidate.family for candidate in candidates))
        if len(families) > 1:
            findings.add(
                "MIXED_HEADING_STYLES",
                "Multiple heading pattern families were detected.",
                observed_value=len(families),
            )
        numbered = [(index, item.number) for index, item in enumerate(candidates) if item.number is not None]
        seen: set[int] = set()
        for index, number in numbered:
            assert number is not None
            if number in seen:
                findings.add(
                    "DUPLICATE_CHAPTER_NUMBER",
                    "A chapter number occurs more than once.",
                    section_index=self._candidate_section_index(candidates, sections, index),
                    observed_value=number,
                )
            seen.add(number)
        for (left_index, left), (right_index, right) in zip(numbered, numbered[1:]):
            if right != left + 1 and right != left:
                findings.add(
                    "NON_SEQUENTIAL_NUMBERING",
                    "Adjacent numbered headings are not consecutive.",
                    section_index=self._candidate_section_index(candidates, sections, right_index),
                    observed_value=right,
                )
        structured = [section for section in sections if section.heading is not None]
        for section in structured:
            if section.character_count >= self._policy.extreme_section_minimum:
                findings.add(
                    "EXTREME_SECTION_SIZE",
                    "A structured section exceeds the configured size threshold.",
                    section_index=section.index,
                    observed_value=section.character_count,
                )
        positive_sizes = [item.character_count for item in structured if item.character_count > 0]
        if len(positive_sizes) >= 2:
            smallest, largest = min(positive_sizes), max(positive_sizes)
            if (
                largest - smallest >= self._policy.section_size_difference_threshold
                and largest / smallest >= self._policy.section_size_ratio_threshold
            ):
                findings.add(
                    "HIGH_SECTION_SIZE_VARIANCE",
                    "Structured section sizes exceed the configured variance threshold.",
                    observed_value=round(largest / smallest, 3),
                )

    @staticmethod
    def _candidate_section_index(
        candidates: tuple[_Candidate, ...], sections: tuple[BookSection, ...], candidate_index: int
    ) -> int:
        front_offset = int(bool(sections and sections[0].section_type == "front_matter"))
        return candidate_index + front_offset

    @staticmethod
    def _validate_invariants(text: str, sections: tuple[BookSection, ...]) -> None:
        if not text:
            if sections:
                raise SegmentationInvariantError("Empty text cannot contain sections.")
            return
        if not sections or sections[0].character_start != 0:
            raise SegmentationInvariantError("Section coverage must start at offset 0.")
        expected = 0
        for index, section in enumerate(sections):
            if section.index != index:
                raise SegmentationInvariantError("Section indexes must be consecutive.")
            if section.character_start != expected:
                raise SegmentationInvariantError("Section offsets contain a gap or overlap.")
            if section.text != text[section.character_start:section.character_end]:
                raise SegmentationInvariantError("Section text does not match its source slice.")
            expected = section.character_end
        if expected != len(text):
            raise SegmentationInvariantError("Section coverage must end at source length.")
        if "".join(section.text for section in sections) != text:
            raise SegmentationInvariantError("Section reconstruction does not match source text.")


def _make_lines(text: str) -> tuple[_Line, ...]:
    output: list[_Line] = []
    offset = 0
    for index, raw in enumerate(text.splitlines(keepends=True)):
        content = raw.rstrip(_LINE_ENDINGS)
        output.append(
            _Line(index, offset, offset + len(raw), offset + len(content), raw, content, content.strip())
        )
        offset += len(raw)
    return tuple(output)


def _source_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_source_name(value: str) -> str:
    return PurePosixPath(PureWindowsPath(value).name).name


def _extract_number(code: str, match: re.Match[str], label: str) -> int | None:
    if "NUMBERED" not in code:
        return None
    groups = tuple(group for group in match.groups() if group and group not in {"章", "回", "篇", "部", "幕"})
    if not groups:
        return None
    token = groups[0].strip()
    if token.isascii() and token.isdigit():
        return int(token)
    if code == "ENGLISH_NUMBERED_CHAPTER":
        normalized = token.upper().replace("-", " ")
        if normalized in _ENGLISH_NUMBERS:
            return _ENGLISH_NUMBERS[normalized]
        parts = normalized.split()
        if len(parts) == 2 and parts[0] == "TWENTY" and parts[1] in _ENGLISH_NUMBERS:
            return 20 + _ENGLISH_NUMBERS[parts[1]]
        return _roman_number(normalized)
    return _cjk_number(token)


def _cjk_number(value: str) -> int | None:
    normalized = value.translate(str.maketrans({"〇": "0", "零": "0", "一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "兩": "2", "两": "2", "壹": "1", "貳": "2", "贰": "2", "參": "3", "叁": "3", "肆": "4", "伍": "5", "陸": "6", "陆": "6", "柒": "7", "捌": "8", "玖": "9"}))
    if normalized.isdigit() and not any(char in value for char in "十拾百佰千仟"):
        return int(normalized)
    digits = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "兩": 2, "两": 2, "壹": 1, "貳": 2, "贰": 2, "參": 3, "叁": 3, "肆": 4, "伍": 5, "陸": 6, "陆": 6, "柒": 7, "捌": 8, "玖": 9}
    units = {"十": 10, "拾": 10, "百": 100, "佰": 100, "千": 1000, "仟": 1000}
    total, current = 0, 0
    for char in value:
        if char in digits:
            current = digits[char]
        elif char in units:
            total += (current or 1) * units[char]
            current = 0
        else:
            return None
    return total + current


def _roman_number(value: str) -> int | None:
    if not value or any(char not in "IVXLCDM" for char in value):
        return None
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for index, char in enumerate(value):
        amount = values[char]
        total += -amount if index + 1 < len(value) and amount < values[value[index + 1]] else amount
    return total


def _summary(status: str, section_count: int, heading_count: int) -> str:
    return (
        f"Segmentation {status}: {section_count} sections; "
        f"{heading_count} reliable headings; lossless coverage verified."
    )


def _fingerprint_payload(
    *,
    source_fingerprint: str,
    strategy: str,
    sections: tuple[BookSection, ...],
    findings: tuple[SegmentationFinding, ...],
    status: str,
    action: str,
    chapter_count: int,
) -> dict[str, object]:
    return {
        "source_content_fingerprint": source_fingerprint,
        "strategy": strategy,
        "sections": [asdict(section) for section in sections],
        "findings": [asdict(finding) for finding in findings],
        "status": status,
        "action": action,
        "chapter_count": chapter_count,
    }
