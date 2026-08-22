from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.context_scene_memory.models import BoundaryType


CHAPTER_PATTERNS = [
    r"^제\s*\d+\s*장\b",
    r"^第\s*\d+\s*章\b",
    r"^Chapter\s+\d+\b",
    r"^CHAPTER\s+\d+\b",
]

SCENE_PATTERNS = [
    r"^제\s*\d+\s*절\b",
    r"^第\s*\d+\s*節\b",
    r"^Scene\s+\d+\b",
    r"^SCENE\s+\d+\b",
    r"^\s*[*─=]{3,}\s*$",
]

LOCATION_SHIFT_PATTERNS = [
    r"(도착|도착했다|도착해|도착함)",
    r"(이동|이동했다|이동해|이동함)",
    r"(새로운\s+장소|다른\s+장소|장소\s*변경)",
    r"(현관|거실|침실|주방|옥상|지하|사무실|학교|병원|공원|역|공항)",
]

TIME_SHIFT_PATTERNS = [
    r"(아침|오전|정오|오후|저녁|밤|새벽|한밤중)",
    r"(\d{1,2}\s*시\s*\d{0,2}\s*분)",
    r"(시간이\s*지나|시간이\s*흐르|며칠\s*후|몇\s*시간\s*후)",
]

SPEAKER_CHANGE_PATTERN = re.compile(r"^\s*[「『\"]")


@dataclass(frozen=True)
class BoundaryResult:
    """Result of scene/chapter boundary detection between two chunks.

    Conservative: only explicit markers produce SCENE_TRANSITION/CHAPTER_TRANSITION.
    Heuristics (location/time/speaker) return UNKNOWN_TRANSITION.
    """
    type: BoundaryType
    scene_id: Optional[str] = None
    chapter_id: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "scene_id": self.scene_id,
            "chapter_id": self.chapter_id,
            "confidence": self.confidence,
            "metadata": self.metadata or {}
        }


def detect_boundary(prev_chunk: str, curr_chunk: str) -> BoundaryResult:
    """
    Detect scene/chapter boundary between two consecutive chunks.

    CONSERVATIVE RULE:
    - Only EXPLICIT markers (CHAPTER_PATTERNS, SCENE_PATTERNS) produce
      CHAPTER_TRANSITION / SCENE_TRANSITION with scene_id/chapter_id.
    - All heuristics (location/time/speaker) return UNKNOWN_TRANSITION.
    - Default: SAME_SCENE.
    """
    curr_stripped = curr_chunk.lstrip()

    # 1. Chapter markers (highest priority) — EXPLICIT ONLY
    for pattern in CHAPTER_PATTERNS:
        if re.search(pattern, curr_stripped, re.MULTILINE):
            chapter_num = _extract_number(curr_stripped, pattern)
            return BoundaryResult(
                type=BoundaryType.CHAPTER_TRANSITION,
                chapter_id=f"chapter_{chapter_num}",
                scene_id=f"scene_{chapter_num}_1",
                confidence=0.95,
                metadata={"marker": "chapter", "pattern": pattern}
            )

    # 2. Scene markers — EXPLICIT ONLY
    for pattern in SCENE_PATTERNS:
        if re.search(pattern, curr_stripped, re.MULTILINE):
            scene_num = _extract_number(curr_stripped, pattern)
            return BoundaryResult(
                type=BoundaryType.SCENE_TRANSITION,
                scene_id=f"scene_{scene_num}",
                confidence=0.9,
                metadata={"marker": "scene", "pattern": pattern}
            )

    # 3. Heuristics — return UNKNOWN_TRANSITION (conservative)
    # Location shift
    for pattern in LOCATION_SHIFT_PATTERNS:
        if re.search(pattern, curr_chunk):
            if _location_changed(prev_chunk, curr_chunk):
                return BoundaryResult(
                    type=BoundaryType.UNKNOWN_TRANSITION,
                    scene_id=None,
                    confidence=0.4,
                    metadata={"marker": "location_shift", "pattern": pattern}
                )

    # Time shift + paragraph break
    for pattern in TIME_SHIFT_PATTERNS:
        if re.search(pattern, curr_chunk):
            if _paragraph_break(prev_chunk, curr_chunk):
                return BoundaryResult(
                    type=BoundaryType.UNKNOWN_TRANSITION,
                    scene_id=None,
                    confidence=0.3,
                    metadata={"marker": "time_shift", "pattern": pattern}
                )

    # Speaker change at paragraph boundary
    if SPEAKER_CHANGE_PATTERN.search(curr_stripped[:50]):
        if _paragraph_break(prev_chunk, curr_chunk):
            return BoundaryResult(
                type=BoundaryType.UNKNOWN_TRANSITION,
                scene_id=None,
                confidence=0.2,
                metadata={"marker": "speaker_change"}
            )

    # 4. Conservative default
    return BoundaryResult(
        type=BoundaryType.SAME_SCENE,
        confidence=1.0,
        metadata={"marker": "none"}
    )


def _extract_number(text: str, pattern: str) -> int:
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 1


def _location_changed(prev: str, curr: str) -> bool:
    prev_locs = set(re.findall(r"(현관|거실|침실|주방|옥상|지하|사무실|학교|병원|공원|역|공항)", prev))
    curr_locs = set(re.findall(r"(현관|거실|침실|주방|옥상|지하|사무실|학교|병원|공원|역|공항)", curr))
    return bool(curr_locs - prev_locs)


def _paragraph_break(prev: str, curr: str) -> bool:
    return prev.rstrip().endswith("\n\n") or curr.startswith("\n\n")


# REMOVED: _generate_scene_id() — NO auto scene ID generation from chunk hash
# Scene IDs ONLY come from explicit markers via transition_scene()/transition_chapter()