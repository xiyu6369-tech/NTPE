from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass

from core.book_segmentation import BookSection, BookSegmentationResult

from .errors import (
    ChunkPlanningInvariantError,
    InvalidChunkPolicyError,
    SegmentationConsistencyError,
)
from .models import (
    BookChunkPlan,
    ChunkPlanningFinding,
    FindingThreshold,
    FindingValue,
    TranslationChunk,
)
from .policy import DEFAULT_POLICY, ChunkingPolicy, validate_chunk_sizes


_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_PARAGRAPH_BOUNDARY = re.compile(r"(?:\r\n|\r|\n)[ \t]*(?:\r\n|\r|\n)")
_SENTENCE_BOUNDARY = re.compile(r"[。！？.!?…]+[」』”’\"']*")
_LINE_BOUNDARY = re.compile(r"\r\n|\r|\n")
_PUNCTUATION_OR_QUOTE = frozenset("。！？….!?,，；;：:」』”’\"'）)]】》〉")


@dataclass(frozen=True)
class _Piece:
    start: int
    end: int
    reason: str
    first_section_index: int
    last_section_index: int

    @property
    def size(self) -> int:
        return self.end - self.start


class _FindingCollector:
    def __init__(self, policy: ChunkingPolicy) -> None:
        self._policy = policy
        self._items: dict[
            tuple[str, int | None, int | None, FindingValue, FindingThreshold],
            ChunkPlanningFinding,
        ] = {}

    def add(
        self,
        code: str,
        message: str,
        *,
        chunk_index: int | None = None,
        section_index: int | None = None,
        observed_value: FindingValue = None,
        threshold: FindingThreshold = None,
    ) -> None:
        key = (code, chunk_index, section_index, observed_value, threshold)
        self._items.setdefault(
            key,
            ChunkPlanningFinding(
                code=code,
                severity=self._policy.finding_severities[code],
                message=message,
                chunk_index=chunk_index,
                section_index=section_index,
                observed_value=observed_value,
                threshold=threshold,
            ),
        )

    def ordered(self) -> tuple[ChunkPlanningFinding, ...]:
        rank = {code: index for index, code in enumerate(self._policy.finding_codes)}
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (
                    rank[item.code],
                    -1 if item.chunk_index is None else item.chunk_index,
                    -1 if item.section_index is None else item.section_index,
                    "" if item.observed_value is None else str(item.observed_value),
                ),
            )
        )


class BookChunkPlanner:
    """Build an immutable, lossless chunk plan without translation or I/O."""

    def __init__(self, policy: ChunkingPolicy = DEFAULT_POLICY) -> None:
        if not isinstance(policy, ChunkingPolicy):
            raise InvalidChunkPolicyError("policy must be a ChunkingPolicy")
        self._policy = policy

    def plan(
        self,
        segmentation_result: BookSegmentationResult,
        *,
        target_chunk_size: int | None = None,
        maximum_chunk_size: int | None = None,
        minimum_chunk_size: int | None = None,
    ) -> BookChunkPlan:
        if not isinstance(segmentation_result, BookSegmentationResult):
            raise SegmentationConsistencyError(
                "segmentation_result must be a BookSegmentationResult"
            )
        minimum = (
            self._policy.minimum_chunk_size
            if minimum_chunk_size is None
            else minimum_chunk_size
        )
        target = (
            self._policy.target_chunk_size
            if target_chunk_size is None
            else target_chunk_size
        )
        maximum = (
            self._policy.maximum_chunk_size
            if maximum_chunk_size is None
            else maximum_chunk_size
        )
        validate_chunk_sizes(minimum, target, maximum)

        source = self._validate_segmentation(segmentation_result)
        findings = _FindingCollector(self._policy)
        if not source:
            findings.add(
                "EMPTY_CONTENT",
                "The segmentation source content is empty.",
                observed_value=0,
            )
            if segmentation_result.status not in {"ready", "ready_with_warnings"}:
                findings.add(
                    "SEGMENTATION_NOT_READY",
                    "The segmentation result is not ready for automatic processing.",
                    observed_value=segmentation_result.status,
                )
            return self._build_plan(
                segmentation_result, source, (), findings, minimum, target, maximum
            )

        pieces: list[_Piece] = []
        for section in segmentation_result.sections:
            if section.character_count <= maximum:
                pieces.append(
                    _Piece(
                        section.character_start,
                        section.character_end,
                        "section_end",
                        section.index,
                        section.index,
                    )
                )
            else:
                findings.add(
                    "SECTION_EXCEEDS_MAXIMUM",
                    "A section exceeds the configured maximum chunk size.",
                    section_index=section.index,
                    observed_value=section.character_count,
                    threshold=maximum,
                )
                pieces.extend(
                    self._split_section(
                        section, minimum, target, maximum, findings
                    )
                )

        merged = self._merge_pieces(
            tuple(pieces), segmentation_result.sections, minimum, target, maximum
        )
        chunks = self._materialize_chunks(
            source, merged, segmentation_result.sections
        )
        self._add_chunk_findings(chunks, findings, minimum, maximum)
        self._validate_chunks(
            source, chunks, segmentation_result.sections, maximum
        )
        return self._build_plan(
            segmentation_result,
            source,
            chunks,
            findings,
            minimum,
            target,
            maximum,
        )

    def _split_section(
        self,
        section: BookSection,
        minimum: int,
        target: int,
        maximum: int,
        findings: _FindingCollector,
    ) -> tuple[_Piece, ...]:
        text = section.text
        boundary_positions = {
            "paragraph": tuple(match.end() for match in _PARAGRAPH_BOUNDARY.finditer(text)),
            "sentence": tuple(match.end() for match in _SENTENCE_BOUNDARY.finditer(text)),
            "line": tuple(match.end() for match in _LINE_BOUNDARY.finditer(text)),
        }
        protected_end = 0
        if section.heading is not None:
            protected_end = section.heading.character_end - section.character_start
            if protected_end > maximum:
                raise SegmentationConsistencyError(
                    "A heading is longer than maximum_chunk_size and cannot be split safely."
                )
            heading_length = section.heading.character_end - section.heading.character_start
            if heading_length > self._policy.maximum_heading_protection_length:
                findings.add(
                    "HEADING_PROTECTION_LIMITED",
                    "A heading exceeds the configured protection review range.",
                    section_index=section.index,
                    observed_value=heading_length,
                    threshold=self._policy.maximum_heading_protection_length,
                )
            body_start = protected_end
            while body_start < len(text) and text[body_start] in "\r\n":
                body_start += 1
            if body_start < len(text):
                protected_end = body_start + 1
            if protected_end > maximum:
                raise SegmentationConsistencyError(
                    "A heading and its first body character cannot fit within maximum_chunk_size."
                )
            if protected_end > target:
                findings.add(
                    "HEADING_PROTECTION_LIMITED",
                    "Heading protection requires the first chunk to extend beyond target size.",
                    section_index=section.index,
                    observed_value=protected_end,
                    threshold=target,
                )

        output: list[_Piece] = []
        start = 0
        first_piece = True
        while len(text) - start > maximum:
            preferred_start = min(start + minimum, start + maximum)
            if first_piece:
                preferred_start = max(preferred_start, protected_end)
            maximum_end = start + maximum
            target_end = min(start + target, maximum_end)
            cut = 0
            reason = ""
            for boundary_type in self._policy.boundary_priority[:-1]:
                options = tuple(
                    position
                    for position in boundary_positions[boundary_type]
                    if preferred_start <= position <= maximum_end
                )
                if options:
                    cut = min(
                        options,
                        key=lambda position: (
                            abs(position - target_end),
                            position > target_end,
                            -position,
                        ),
                    )
                    reason = boundary_type
                    break
            if not cut:
                for boundary_type in self._policy.boundary_priority[:-1]:
                    options = tuple(
                        position
                        for position in boundary_positions[boundary_type]
                        if start < position <= maximum_end
                        and (not first_piece or position >= protected_end)
                    )
                    if options:
                        cut = max(options)
                        reason = boundary_type
                        break
            if not cut:
                cut = self._safe_hard_limit(text, start, maximum_end)
                reason = "hard_limit"
                findings.add(
                    "HARD_SPLIT_REQUIRED",
                    "No safe textual boundary was available before the hard limit.",
                    section_index=section.index,
                    observed_value=section.character_start + cut,
                    threshold=maximum,
                )
            if cut <= start or cut > maximum_end:
                raise ChunkPlanningInvariantError("A safe forward chunk boundary could not be produced.")
            output.append(
                _Piece(
                    section.character_start + start,
                    section.character_start + cut,
                    reason,
                    section.index,
                    section.index,
                )
            )
            start = cut
            first_piece = False
        output.append(
            _Piece(
                section.character_start + start,
                section.character_end,
                "section_end",
                section.index,
                section.index,
            )
        )
        return tuple(output)

    def _safe_hard_limit(self, text: str, start: int, maximum_end: int) -> int:
        cut = maximum_end
        if cut < len(text) and cut > start and text[cut - 1] == "\r" and text[cut] == "\n":
            cut -= 1
        while cut > start and cut < len(text) and unicodedata.combining(text[cut]):
            cut -= 1
        while (
            cut > start + 1
            and cut < len(text)
            and text[cut - 1] in _PUNCTUATION_OR_QUOTE
            and text[cut] in _PUNCTUATION_OR_QUOTE
        ):
            cut -= 1
        if cut == start:
            raise ChunkPlanningInvariantError(
                "maximum_chunk_size cannot preserve an indivisible CRLF or combining sequence"
            )
        return cut

    def _merge_pieces(
        self,
        pieces: tuple[_Piece, ...],
        sections: tuple[BookSection, ...],
        minimum: int,
        target: int,
        maximum: int,
    ) -> tuple[_Piece, ...]:
        if not pieces:
            return ()
        merged: list[_Piece] = []
        current = pieces[0]
        for following in pieces[1:]:
            combined_size = following.end - current.start
            should_merge = (
                self._can_merge(current, following, sections)
                and combined_size <= maximum
                and (combined_size <= target or current.size < minimum)
            )
            if should_merge:
                current = _Piece(
                    current.start,
                    following.end,
                    following.reason,
                    current.first_section_index,
                    following.last_section_index,
                )
            else:
                merged.append(current)
                current = following
        merged.append(current)

        index = len(merged) - 1
        while index > 0:
            item = merged[index]
            previous = merged[index - 1]
            if (
                item.size < minimum
                and item.end - previous.start <= maximum
                and self._can_merge(previous, item, sections)
            ):
                merged[index - 1] = _Piece(
                    previous.start,
                    item.end,
                    item.reason,
                    previous.first_section_index,
                    item.last_section_index,
                )
                del merged[index]
            index -= 1
        return tuple(merged)

    def _can_merge(
        self,
        left: _Piece,
        right: _Piece,
        sections: tuple[BookSection, ...],
    ) -> bool:
        if left.end != right.start:
            return False
        if left.last_section_index == right.first_section_index:
            return True
        left_type = sections[left.last_section_index].section_type
        right_type = sections[right.first_section_index].section_type
        return not (
            left_type in self._policy.isolated_section_types
            or right_type in self._policy.isolated_section_types
        )

    @staticmethod
    def _materialize_chunks(
        source: str,
        pieces: tuple[_Piece, ...],
        sections: tuple[BookSection, ...],
    ) -> tuple[TranslationChunk, ...]:
        section_starts = {section.character_start for section in sections}
        section_ends = {section.character_end for section in sections}
        output: list[TranslationChunk] = []
        for index, piece in enumerate(pieces):
            references = tuple(
                section.index
                for section in sections
                if section.character_start < piece.end
                and section.character_end > piece.start
            )
            if not references:
                raise ChunkPlanningInvariantError("A chunk has no intersecting section.")
            value = source[piece.start:piece.end]
            headings = tuple(
                section.heading.text
                for section in sections
                if section.index in references
                and section.heading is not None
                and piece.start <= section.heading.character_start
                and section.heading.character_end <= piece.end
            )
            output.append(
                TranslationChunk(
                    index=index,
                    text=value,
                    source_character_start=piece.start,
                    source_character_end=piece.end,
                    first_section_index=references[0],
                    last_section_index=references[-1],
                    section_indices=references,
                    starts_at_section_boundary=piece.start in section_starts,
                    ends_at_section_boundary=piece.end in section_ends,
                    character_count=len(value),
                    non_whitespace_character_count=sum(not char.isspace() for char in value),
                    heading_text=headings[0] if headings else None,
                    boundary_reason=piece.reason,
                    content_fingerprint=hashlib.sha256(value.encode("utf-8")).hexdigest(),
                )
            )
        return tuple(output)

    def _add_chunk_findings(
        self,
        chunks: tuple[TranslationChunk, ...],
        findings: _FindingCollector,
        minimum: int,
        maximum: int,
    ) -> None:
        for chunk in chunks:
            if chunk.character_count < minimum:
                findings.add(
                    "CHUNK_BELOW_MINIMUM",
                    "A chunk remains below minimum size after deterministic merge attempts.",
                    chunk_index=chunk.index,
                    observed_value=chunk.character_count,
                    threshold=minimum,
                )
            if chunk.character_count > maximum:
                findings.add(
                    "CHUNK_EXCEEDS_MAXIMUM",
                    "A chunk exceeds the configured maximum size.",
                    chunk_index=chunk.index,
                    observed_value=chunk.character_count,
                    threshold=maximum,
                )
            if len(chunk.section_indices) > 1:
                findings.add(
                    "MULTI_SECTION_CHUNK",
                    "A chunk contains multiple complete or partial sections.",
                    chunk_index=chunk.index,
                    observed_value=len(chunk.section_indices),
                )
        sizes = [chunk.character_count for chunk in chunks if chunk.character_count]
        if len(sizes) >= 2:
            smallest, largest = min(sizes), max(sizes)
            if (
                largest - smallest >= self._policy.size_variance_difference
                and largest / smallest >= self._policy.size_variance_ratio
            ):
                findings.add(
                    "HIGH_CHUNK_SIZE_VARIANCE",
                    "Chunk sizes exceed the configured deterministic variance threshold.",
                    observed_value=round(largest / smallest, 3),
                    threshold=self._policy.size_variance_ratio,
                )
        if len(chunks) > self._policy.excessive_chunk_count:
            findings.add(
                "EXCESSIVE_CHUNK_COUNT",
                "Chunk count exceeds the configured review threshold.",
                observed_value=len(chunks),
                threshold=self._policy.excessive_chunk_count,
            )

    def _build_plan(
        self,
        segmentation: BookSegmentationResult,
        source: str,
        chunks: tuple[TranslationChunk, ...],
        findings: _FindingCollector,
        minimum: int,
        target: int,
        maximum: int,
    ) -> BookChunkPlan:
        structured = any(section.heading is not None for section in segmentation.sections)
        if segmentation.status not in {"ready", "ready_with_warnings"}:
            findings.add(
                "SEGMENTATION_NOT_READY",
                "The segmentation result is not ready for automatic processing.",
                observed_value=segmentation.status,
            )
        if source and not structured:
            findings.add(
                "NO_STRUCTURED_SECTIONS",
                "The source has no reliable structured section headings.",
                observed_value=len(segmentation.sections),
            )
        ordered_findings = findings.ordered()
        hard_split_count = sum(item.code == "HARD_SPLIT_REQUIRED" for item in ordered_findings)
        if segmentation.status == "blocked":
            status = "blocked"
        elif not source or segmentation.status == "manual_review" or not structured:
            status = "manual_review"
        elif hard_split_count >= self._policy.hard_split_review_count:
            status = "manual_review"
        elif ordered_findings:
            status = "ready_with_warnings"
        else:
            status = "ready"
        action = self._policy.status_actions[status]
        payload = {
            "source_content_fingerprint": segmentation.source_content_fingerprint,
            "segmentation_fingerprint": segmentation.segmentation_fingerprint,
            "strategy": self._policy.strategy,
            "minimum_chunk_size": minimum,
            "target_chunk_size": target,
            "maximum_chunk_size": maximum,
            "chunks": [
                {
                    "index": chunk.index,
                    "source_character_start": chunk.source_character_start,
                    "source_character_end": chunk.source_character_end,
                    "section_indices": chunk.section_indices,
                    "starts_at_section_boundary": chunk.starts_at_section_boundary,
                    "ends_at_section_boundary": chunk.ends_at_section_boundary,
                    "boundary_reason": chunk.boundary_reason,
                    "content_fingerprint": chunk.content_fingerprint,
                }
                for chunk in chunks
            ],
            "findings": [asdict(item) for item in ordered_findings],
            "status": status,
            "action": action,
        }
        plan_fingerprint = hashlib.sha256(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        covered = sum(chunk.character_count for chunk in chunks)
        return BookChunkPlan(
            source_name=segmentation.source_name,
            source_content_fingerprint=segmentation.source_content_fingerprint,
            segmentation_fingerprint=segmentation.segmentation_fingerprint,
            strategy=self._policy.strategy,
            target_chunk_size=target,
            maximum_chunk_size=maximum,
            minimum_chunk_size=minimum,
            chunks=chunks,
            chunk_count=len(chunks),
            section_count=len(segmentation.sections),
            character_count=len(source),
            covered_character_count=covered,
            coverage_ratio=1.0 if not source else covered / len(source),
            status=status,
            action=action,
            findings=ordered_findings,
            summary=(
                f"Chunk planning {status}: {len(chunks)} chunks; "
                f"{len(segmentation.sections)} sections; lossless coverage verified."
            ),
            chunk_plan_fingerprint=plan_fingerprint,
        )

    @staticmethod
    def _validate_segmentation(segmentation: BookSegmentationResult) -> str:
        source = segmentation.reconstruct_text()
        actual_fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if segmentation.source_content_fingerprint != actual_fingerprint:
            raise SegmentationConsistencyError(
                "Segmentation source fingerprint does not match reconstructed text."
            )
        if not _HEX_64.fullmatch(segmentation.segmentation_fingerprint):
            raise SegmentationConsistencyError(
                "Segmentation fingerprint must be lowercase SHA-256 hex."
            )
        if segmentation.character_count != len(source):
            raise SegmentationConsistencyError(
                "Segmentation character_count does not match reconstructed text."
            )
        if not source:
            if segmentation.sections:
                raise SegmentationConsistencyError(
                    "Empty segmentation text cannot contain sections."
                )
            return source
        if not segmentation.sections:
            raise SegmentationConsistencyError(
                "Non-empty segmentation text must contain sections."
            )
        expected = 0
        for index, section in enumerate(segmentation.sections):
            if section.index != index:
                raise SegmentationConsistencyError("Section indexes must be consecutive.")
            if section.character_start != expected:
                raise SegmentationConsistencyError(
                    "Section offsets contain a gap or overlap."
                )
            if section.character_end < section.character_start:
                raise SegmentationConsistencyError("Section offsets are reversed.")
            if section.text != source[section.character_start:section.character_end]:
                raise SegmentationConsistencyError(
                    "Section text does not match its source slice."
                )
            if section.heading is not None:
                heading = section.heading
                if not (
                    section.character_start <= heading.character_start
                    <= heading.character_end <= section.character_end
                ):
                    raise SegmentationConsistencyError(
                        "Heading coordinates fall outside their section."
                    )
                if heading.character_start != section.character_start:
                    raise SegmentationConsistencyError(
                        "A section heading must begin at its section boundary."
                    )
                if heading.text != source[heading.character_start:heading.character_end]:
                    raise SegmentationConsistencyError(
                        "Heading text does not match its source slice."
                    )
            expected = section.character_end
        if expected != len(source):
            raise SegmentationConsistencyError(
                "Section coverage does not reach the end of the source."
            )
        if segmentation.covered_character_count != len(source):
            raise SegmentationConsistencyError(
                "Segmentation covered_character_count is inconsistent."
            )
        if segmentation.coverage_ratio != 1.0:
            raise SegmentationConsistencyError(
                "Segmentation coverage_ratio must equal 1.0."
            )
        return source

    @staticmethod
    def _validate_chunks(
        source: str,
        chunks: tuple[TranslationChunk, ...],
        sections: tuple[BookSection, ...],
        maximum: int,
    ) -> None:
        if not source:
            if chunks:
                raise ChunkPlanningInvariantError("Empty source cannot produce chunks.")
            return
        if not chunks or chunks[0].source_character_start != 0:
            raise ChunkPlanningInvariantError("Chunk coverage must start at offset 0.")
        expected = 0
        for index, chunk in enumerate(chunks):
            if chunk.index != index:
                raise ChunkPlanningInvariantError("Chunk indexes must be consecutive.")
            if chunk.source_character_start != expected:
                raise ChunkPlanningInvariantError("Chunk offsets contain a gap or overlap.")
            if chunk.source_character_end - chunk.source_character_start > maximum:
                raise ChunkPlanningInvariantError("A chunk exceeds maximum_chunk_size.")
            if chunk.text != source[chunk.source_character_start:chunk.source_character_end]:
                raise ChunkPlanningInvariantError("Chunk text does not match its source slice.")
            actual_references = tuple(
                section.index
                for section in sections
                if section.character_start < chunk.source_character_end
                and section.character_end > chunk.source_character_start
            )
            if chunk.section_indices != actual_references:
                raise ChunkPlanningInvariantError("Chunk section references are invalid.")
            expected = chunk.source_character_end
        if expected != len(source):
            raise ChunkPlanningInvariantError("Chunk coverage does not reach source end.")
        if "".join(chunk.text for chunk in chunks) != source:
            raise ChunkPlanningInvariantError("Chunk reconstruction does not match source.")
        for section in sections:
            if section.heading is None:
                continue
            containing = tuple(
                chunk
                for chunk in chunks
                if chunk.source_character_start <= section.heading.character_start
                and section.heading.character_end <= chunk.source_character_end
            )
            if len(containing) != 1:
                raise ChunkPlanningInvariantError(
                    "A heading was split, omitted, or duplicated across chunks."
                )
