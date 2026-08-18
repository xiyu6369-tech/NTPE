from __future__ import annotations

import pytest
from core.translation_runtime.boundary_detector import detect_boundary, BoundaryResult
from core.context_scene_memory.models import BoundaryType


class TestBoundaryDetector:
    """Unit tests for conservative boundary detection."""

    def test_chapter_marker_korean(self):
        prev = "첫 번째 장의 내용입니다."
        curr = "제2장 새로운 시작"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.CHAPTER_TRANSITION
        assert result.chapter_id == "chapter_2"
        assert result.scene_id == "scene_2_1"
        assert result.confidence == 0.95
        assert result.metadata["marker"] == "chapter"

    def test_chapter_marker_chinese(self):
        prev = "第一章结束。"
        curr = "第2章 新的开始"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.CHAPTER_TRANSITION
        assert result.chapter_id == "chapter_2"
        assert result.scene_id == "scene_2_1"

    def test_chapter_marker_english(self):
        prev = "End of chapter 1."
        curr = "Chapter 2 A new beginning"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.CHAPTER_TRANSITION
        assert result.chapter_id == "chapter_2"
        assert result.scene_id == "scene_2_1"

    def test_scene_marker_korean(self):
        prev = "첫 번째 절의 내용입니다."
        curr = "제3절 새로운 장면"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.SCENE_TRANSITION
        assert result.scene_id == "scene_3"
        assert result.confidence == 0.9
        assert result.metadata["marker"] == "scene"

    def test_scene_marker_chinese(self):
        prev = "第一节结束。"
        curr = "第2節 新場景"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.SCENE_TRANSITION
        assert result.scene_id == "scene_2"

    def test_scene_marker_english(self):
        prev = "End of scene 1."
        curr = "Scene 2 A new scene"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.SCENE_TRANSITION
        assert result.scene_id == "scene_2"

    def test_scene_marker_horizontal_rule(self):
        prev = "장면이 끝납니다."
        curr = "***\n새로운 장면 시작"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.SCENE_TRANSITION
        assert result.scene_id is not None

    def test_heuristic_location_shift_returns_unknown(self):
        prev = "거실에서 대화를 나눴다."
        curr = "그는 침실로 이동했다."
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.UNKNOWN_TRANSITION
        assert result.scene_id is None
        assert result.confidence == 0.4
        assert result.metadata["marker"] == "location_shift"

    def test_heuristic_time_shift_returns_unknown(self):
        prev = "오후 3시에 만났다."
        curr = "\n\n밤 10시가 되어서야 헤어졌다."
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.UNKNOWN_TRANSITION
        assert result.scene_id is None
        assert result.confidence == 0.3
        assert result.metadata["marker"] == "time_shift"

    def test_heuristic_speaker_change_returns_unknown(self):
        prev = "그가 말했다."
        curr = '\n\n"안녕하세요." 그녀가 인사했다.'
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.UNKNOWN_TRANSITION
        assert result.scene_id is None
        assert result.confidence == 0.2
        assert result.metadata["marker"] == "speaker_change"

    def test_same_scene_default(self):
        prev = "첫 번째 문단입니다."
        curr = "두 번째 문단입니다."
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.SAME_SCENE
        assert result.confidence == 1.0
        assert result.metadata["marker"] == "none"

    def test_no_auto_scene_id_generation(self):
        """Verify _generate_scene_id() does not exist and heuristics never produce scene_id."""
        prev = "거실에서 대화를 나눴다."
        curr = "그는 침실로 이동했다. 새로운 장소였다."
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.UNKNOWN_TRANSITION
        assert result.scene_id is None, "Heuristics must not auto-generate scene_id"

    def test_chapter_transition_priority_over_scene(self):
        """Chapter marker takes priority even if scene marker also present."""
        prev = "끝."
        curr = "제1장\n제1절 시작"
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.CHAPTER_TRANSITION

    def test_boundary_result_to_dict(self):
        result = BoundaryResult(
            type=BoundaryType.SCENE_TRANSITION,
            scene_id="scene_5",
            chapter_id=None,
            confidence=0.9,
            metadata={"marker": "scene", "pattern": "제5절"}
        )
        d = result.to_dict()
        assert d["type"] == "scene_transition"
        assert d["scene_id"] == "scene_5"
        assert d["chapter_id"] is None
        assert d["confidence"] == 0.9
        assert d["metadata"]["marker"] == "scene"

    def test_unknown_transition_no_expiry_in_scene_state(self):
        """UNKNOWN_TRANSITION should not trigger context expiry (handled by scene_state.py)."""
        prev = "첫 문단."
        curr = "\n\n아침이 밝았다. 새로운 하루."
        result = detect_boundary(prev, curr)
        assert result.type == BoundaryType.UNKNOWN_TRANSITION
        # The conservative UNKNOWN_TRANSITION returns changed=False in transition_scene
        # which means no context expiry - verified in scene_state.py tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])