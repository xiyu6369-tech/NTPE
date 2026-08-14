# tests/unit/translation_release/test_validator.py

import pytest
from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_release.validator import (
    validate_final_novel,
    ValidationResult,
    ValidationCheck,
    _check_narrative_pov_continuity,
    _check_tense_voice_consistency,
)


def _make_narrative(
    perspective: str = "unknown",
    voice: str = "neutral",
    tense: str = "undetermined",
    emotional_tone: str = "neutral",
    focus: str = "",
    transitions: list[str] | None = None,
    updates: int = 0,
) -> dict:
    """Create a narrative dict matching NarrativeState.to_prompt_context() exactly."""
    return {
        "perspective": perspective,
        "voice": voice,
        "tense": tense,
        "emotional_tone": emotional_tone,
        "focus": focus,
        "transitions": transitions if transitions is not None else [],
        "metadata": {"updates": updates},
    }


def _make_context_state(
    scene_id: str = "scene_1",
    chapter_id: str = "chapter_1",
    boundary_type: str = "same_scene",
    narrative: dict | None = None,
) -> dict:
    """Create a context_state dict matching RM-8.2 chunk_record.metadata.context_state exactly."""
    if narrative is None:
        narrative = _make_narrative()
    return {
        "scene_id": scene_id,
        "scene_version": 1,
        "chapter_id": chapter_id,
        "boundary": {
            "type": boundary_type,
            "scene_id": scene_id if boundary_type == "scene_transition" else None,
            "chapter_id": chapter_id if boundary_type == "chapter_transition" else None,
            "confidence": 1.0,
            "metadata": {},
        },
        "narrative": narrative,
        "context_selection_fingerprint": "test_fingerprint",
        "selected_context_ids": ("ctx_1",),
    }


def _make_chunk_record(
    scene_id: str = "scene_1",
    chapter_id: str = "chapter_1",
    boundary_type: str = "same_scene",
    narrative: dict | None = None,
    char_count: int = 50,
) -> dict:
    """Create a chunk_record matching production structure."""
    return {
        "source": {"char_count": char_count, "chunk_text": "test" * 10},
        "metadata": {"context_state": _make_context_state(scene_id, chapter_id, boundary_type, narrative)},
    }


@pytest.fixture
def sample_chunks():
    return [
        "主角走進了房間。",
        "他看到了��上有一封信。",
        "信上��著：明天見。",
    ]


@pytest.fixture
def sample_records():
    return [
        {
            "source": {"char_count": 50, "chunk_text": "주인공이 방에 들어갔다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "scene_version": 1,
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "same_scene", "scene_id": None, "chapter_id": None, "confidence": 1.0, "metadata": {}},
                    "narrative": _make_narrative("third_person", "neutral", "past"),
                    "context_selection_fingerprint": "fp1",
                    "selected_context_ids": ("ctx_1",),
                }
            },
        },
        {
            "source": {"char_count": 45, "chunk_text": "그는 책상 위에 편지가 있는 것을 보았다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "scene_version": 1,
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "same_scene", "scene_id": None, "chapter_id": None, "confidence": 1.0, "metadata": {}},
                    "narrative": _make_narrative("third_person", "neutral", "past"),
                    "context_selection_fingerprint": "fp2",
                    "selected_context_ids": ("ctx_2",),
                }
            },
        },
        {
            "source": {"char_count": 48, "chunk_text": "편지에는 내일 보자고 쓰여 있었다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_2",
                    "scene_version": 1,
                    "chapter_id": "chapter_2",
                    "boundary": {"type": "chapter_transition", "scene_id": "scene_2", "chapter_id": "chapter_2", "confidence": 1.0, "metadata": {}},
                    "narrative": _make_narrative("third_person", "neutral", "past"),
                    "context_selection_fingerprint": "fp3",
                    "selected_context_ids": ("ctx_3",),
                }
            },
        },
    ]


class TestValidateFinalNovel:
    """Tests for validate_final_novel function."""

    def test_validator_passes_clean_text(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        locked_dict = {"主角": "主角"}
        matched_terms = {"主角": "主角"}
        text = "\n\n".join(sample_chunks)
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        assert isinstance(result, ValidationResult)
        assert result.overall_passed is True
        assert result.overall_score >= 70.0
        assert len(result.failed_critical) == 0

    def test_validator_fails_korean_residue(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=0,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "안녕하세요\n\n" + "\n\n".join(sample_chunks)
        locked_dict = {}
        matched_terms = {}
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        assert result.overall_passed is False
        assert "korean_residue_global" in result.failed_critical

    def test_validator_locked_terms_only_validates_matched(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        locked_dict = {"主角": "主角", "未出現角色": "未出現角色"}
        matched_terms = {"主角": "主角"}
        text = "主角出現了。"
        records = [
            {
                "source": {"char_count": 10, "chunk_text": "主角出現了。"},
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_1",
                        "chapter_id": "chapter_1",
                        "boundary": {"type": "same_scene"},
                    }
                },
            }
        ]
        result = validate_final_novel(text, locked_dict, records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        assert result.overall_passed is True

    def test_validator_length_ratio_from_source_metadata(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.5,
            strict_lock_terms=True,
        )
        locked_dict = {}
        matched_terms = {}
        text = "\n\n".join(sample_chunks)
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        check = next(c for c in result.checks if c.name == "length_ratio_global")
        assert check.details["verifiable"] is True
        assert check.details["verifiable_chunks"] == 3

    def test_validator_length_ratio_unverifiable_when_no_source(self, sample_chunks):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.5,
            strict_lock_terms=True,
        )
        records_no_source = [
            {"source": {}, "metadata": {}},
            {"source": {"chunk_text": "test"}, "metadata": {"source": {}}},
        ]
        locked_dict = {}
        matched_terms = {}
        text = "��試文本。"
        result = validate_final_novel(text, locked_dict, records_no_source, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        check = next(c for c in result.checks if c.name == "length_ratio_global")
        assert check.details["verifiable"] is False
        assert check.severity == "info"
        assert check.passed is True

    def test_validator_empty_text_fails(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        result = validate_final_novel("", {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        assert result.overall_passed is False
        empty_check = next(c for c in result.checks if c.name == "empty_content")
        assert empty_check.passed is False

    def test_validator_paragraph_structure_critical(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "段落一。\n\n\n\n段落二。\n\n\n\n\n段落三。"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "paragraph_structure")
        assert check.passed is False
        assert check.severity == "critical"
        assert "paragraph_structure" in result.failed_critical

    def test_validator_punctuation_consistency(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "Hello, world! How are you? \"Quote\"."
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "punctuation_consistency")
        assert check.details["cjk_ratio"] < 0.95

    def test_validator_chinese_char_ratio(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "這是一段很長的中文文本內容。包含很多��字字符。這��中文字符比例就會超過百分之八十了。"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "chinese_char_ratio")
        assert check.details["ratio"] >= 0.8
        assert check.passed is True

    def test_validator_repeated_lines(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "第一行。\n第一行。\n第二行。"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "repeated_lines_global")
        assert check.details["repeated_consecutive_lines"] == 1
        assert check.passed is False

    def test_validator_quote_balance(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "「你好"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "quote_balance")
        assert check.details["double_open"] == 1
        assert check.details["double_close"] == 0
        assert check.passed is False

    def test_validator_locked_term_alias_violation(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        # 鄭泰義 has alias 定泰義 in DEFAULT_LOCKED_TRANSLATION_ALIASES
        locked_dict = {"鄭泰義": "鄭泰義"}
        matched_terms = {"鄭泰義": "鄭泰義"}
        text = "定泰義出現了。"
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        check = next(c for c in result.checks if c.name == "locked_term_compliance")
        assert "定泰義" in check.details["alias_violations"]
        assert check.passed is False

    def test_validator_overall_score_weighted(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        locked_dict = {"主角": "主角"}
        matched_terms = {"主角": "主角"}
        text = "主角走進了房間。這是一段很長的中文文本內容。包含很多��字字符。這��中文字符比例就會超過百分之八十了。"
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        assert result.overall_score == 100.0

    def test_validator_failed_critical_blocks_pass(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=0,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "안녕하세요"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        assert result.overall_passed is False
        assert "korean_residue_global" in result.failed_critical

    def test_validator_korean_threshold_calculation(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "안녕"
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "korean_residue_global")
        assert check.details["max_allowed"] == 3
        assert check.passed is True

        text2 = "안녕하세요"
        result2 = validate_final_novel(text2, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check2 = next(c for c in result2.checks if c.name == "korean_residue_global")
        assert check2.passed is False

    def test_validator_return_type(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        result = validate_final_novel(
            "\n\n".join(sample_chunks), {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={}
        )
        assert isinstance(result, ValidationResult)
        assert isinstance(result.overall_passed, bool)
        assert isinstance(result.overall_score, float)
        assert isinstance(result.checks, list)
        assert isinstance(result.failed_critical, list)
        assert isinstance(result.failed_major, list)
        for check in result.checks:
            assert isinstance(check, ValidationCheck)
            assert hasattr(check, "name")
            assert hasattr(check, "passed")
            assert hasattr(check, "score")
            assert hasattr(check, "details")
            assert hasattr(check, "severity")


class TestRM85SemanticChecks:
    """Tests for RM-8.5 cross-chunk semantic validation checks using production-shaped fixtures."""

    @pytest.fixture
    def same_scene_chunks(self):
        narrative = _make_narrative("third_person", "balanced", "past", "neutral", "mode=narration_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def first_person_chunks(self):
        narrative = _make_narrative("first_person", "neutral", "past", "neutral", "mode=narration_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def second_person_chunks(self):
        narrative = _make_narrative("second_person", "neutral", "past", "neutral", "mode=narration_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def scene_transition_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "scene_transition",
                _make_narrative("third_person", "neutral", "past", "neutral", "mode=narration_heavy", ["nar_1"]),
                50
            ),
            _make_chunk_record(
                "scene_2", "chapter_1", "same_scene",
                _make_narrative("first_person", "dialogue_driven", "present", "tense", "mode=dialogue_heavy", ["nar_2"]),
                45
            ),
        ]

    @pytest.fixture
    def chapter_transition_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "chapter_transition",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_2", "same_scene",
                _make_narrative("first_person", "dialogue_driven", "present"),
                45
            ),
        ]

    @pytest.fixture
    def unknown_perspective_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("unknown", "neutral", "past"),
                45
            ),
        ]

    @pytest.fixture
    def unknown_tense_voice_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "unknown", "unknown"),
                45
            ),
        ]

    @pytest.fixture
    def missing_context_chunks(self):
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", _make_narrative("third_person", "neutral", "past"), 50),
            {"metadata": {}},
        ]

    @pytest.fixture
    def pov_violation_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("first_person", "neutral", "past"),
                45
            ),
        ]

    @pytest.fixture
    def tense_violation_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "present"),
                45
            ),
        ]

    @pytest.fixture
    def voice_violation_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "dialogue_driven", "past"),
                45
            ),
        ]

    @pytest.fixture
    def third_person_chunks(self):
        narrative = _make_narrative("third_person", "neutral", "past", "neutral", "mode=narration_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def dialogue_driven_chunks(self):
        narrative = _make_narrative("third_person", "dialogue_driven", "past", "tense", "mode=dialogue_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def descriptive_chunks(self):
        narrative = _make_narrative("third_person", "descriptive", "past", "neutral", "mode=description_heavy", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def balanced_chunks(self):
        narrative = _make_narrative("third_person", "balanced", "past", "neutral", "mode=balanced", ["nar_1"])
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    @pytest.fixture
    def first_to_second_person_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("first_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("second_person", "neutral", "past"),
                45
            ),
        ]

    @pytest.fixture
    def second_to_third_person_chunks(self):
        return [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("second_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                45
            ),
        ]

    @pytest.fixture
    def undetermined_tense_chunks(self):
        narrative = _make_narrative("third_person", "neutral", "undetermined")
        return [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]

    # ===== narrative_pov_continuity tests =====

    def test_narrative_pov_continuity_first_person(self, first_person_chunks):
        text = "我走了進來。\n\n我看到了她。"
        result = _check_narrative_pov_continuity(text, first_person_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.severity == "minor"
        assert result.details["unauthorized_changes"] == 0

    def test_narrative_pov_continuity_second_person(self, second_person_chunks):
        text = "你走了進來。\n\n你看到了她。"
        result = _check_narrative_pov_continuity(text, second_person_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details["unauthorized_changes"] == 0

    def test_narrative_pov_continuity_third_person(self, third_person_chunks):
        text = "他走了進來。\n\n他看到了她。"
        result = _check_narrative_pov_continuity(text, third_person_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details["unauthorized_changes"] == 0

    def test_narrative_pov_continuity_first_to_second_person(self, first_to_second_person_chunks):
        result = _check_narrative_pov_continuity("text", first_to_second_person_chunks)
        assert result.passed is False
        assert result.score == 75.0
        assert result.details["unauthorized_changes"] == 1

    def test_narrative_pov_continuity_second_to_third_person(self, second_to_third_person_chunks):
        result = _check_narrative_pov_continuity("text", second_to_third_person_chunks)
        assert result.passed is False
        assert result.score == 75.0
        assert result.details["unauthorized_changes"] == 1

    def test_narrative_pov_continuity_unknown_is_no_false_positive(self, unknown_perspective_chunks):
        result = _check_narrative_pov_continuity("text", unknown_perspective_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details.get("unknown_skipped") is True

    def test_narrative_pov_continuity_allows_at_scene_transition(self, scene_transition_chunks):
        result = _check_narrative_pov_continuity("text", scene_transition_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details["unauthorized_changes"] == 0

    def test_narrative_pov_continuity_allows_at_chapter_transition(self, chapter_transition_chunks):
        result = _check_narrative_pov_continuity("text", chapter_transition_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_narrative_pov_continuity_missing_context_is_fail_open(self, missing_context_chunks):
        result = _check_narrative_pov_continuity("text", missing_context_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_narrative_pov_continuity_empty_records(self):
        result = _check_narrative_pov_continuity("text", [])
        assert result.passed is True
        assert result.score == 100.0

    def test_narrative_pov_continuity_exception_is_fail_open(self):
        bad_chunks = [{"metadata": {"context_state": "not_a_dict"}}]
        result = _check_narrative_pov_continuity("text", bad_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details.get("fail_open") is True

    # ===== tense_voice_consistency tests =====

    def test_tense_voice_consistency_past(self, same_scene_chunks):
        text = "他走了進來。\n\n他看到了她。"
        result = _check_tense_voice_consistency(text, same_scene_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.severity == "minor"
        assert result.details["tense_violations"] == 0
        assert result.details["voice_violations"] == 0

    def test_tense_voice_consistency_present(self):
        narrative = _make_narrative("third_person", "neutral", "present")
        chunks = [
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 50),
            _make_chunk_record("scene_1", "chapter_1", "same_scene", narrative, 45),
        ]
        result = _check_tense_voice_consistency("text", chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_undetermined(self, undetermined_tense_chunks):
        result = _check_tense_voice_consistency("text", undetermined_tense_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_neutral_voice(self, same_scene_chunks):
        result = _check_tense_voice_consistency("text", same_scene_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_dialogue_driven_voice(self, dialogue_driven_chunks):
        result = _check_tense_voice_consistency("text", dialogue_driven_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_descriptive_voice(self, descriptive_chunks):
        result = _check_tense_voice_consistency("text", descriptive_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_balanced_voice(self, balanced_chunks):
        result = _check_tense_voice_consistency("text", balanced_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_fails_unauthorized_tense_change(self, tense_violation_chunks):
        result = _check_tense_voice_consistency("text", tense_violation_chunks)
        assert result.passed is False
        assert result.score == 85.0
        assert result.details["tense_violations"] == 1
        assert result.details["voice_violations"] == 0

    def test_tense_voice_consistency_fails_unauthorized_voice_change(self, voice_violation_chunks):
        result = _check_tense_voice_consistency("text", voice_violation_chunks)
        assert result.passed is False
        assert result.score == 90.0
        assert result.details["tense_violations"] == 0
        assert result.details["voice_violations"] == 1

    def test_tense_voice_consistency_fails_both_tense_and_voice(self):
        chunks = [
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "neutral", "past"),
                50
            ),
            _make_chunk_record(
                "scene_1", "chapter_1", "same_scene",
                _make_narrative("third_person", "dialogue_driven", "present"),
                45
            ),
        ]
        result = _check_tense_voice_consistency("text", chunks)
        assert result.passed is False
        assert result.score == 75.0
        assert result.details["tense_violations"] == 1
        assert result.details["voice_violations"] == 1

    def test_tense_voice_consistency_allows_at_scene_transition(self, scene_transition_chunks):
        result = _check_tense_voice_consistency("text", scene_transition_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_allows_at_chapter_transition(self, chapter_transition_chunks):
        result = _check_tense_voice_consistency("text", chapter_transition_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_unknown_is_no_false_positive(self, unknown_tense_voice_chunks):
        result = _check_tense_voice_consistency("text", unknown_tense_voice_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details.get("unknown_skipped") is True

    def test_tense_voice_consistency_missing_context_is_fail_open(self, missing_context_chunks):
        result = _check_tense_voice_consistency("text", missing_context_chunks)
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_empty_records(self):
        result = _check_tense_voice_consistency("text", [])
        assert result.passed is True
        assert result.score == 100.0

    def test_tense_voice_consistency_exception_is_fail_open(self):
        bad_chunks = [{"metadata": {"context_state": "not_a_dict"}}]
        result = _check_tense_voice_consistency("text", bad_chunks)
        assert result.passed is True
        assert result.score == 100.0
        assert result.details.get("fail_open") is True


class TestRM85FeatureFlag:
    """Tests for quality_delivery_v83 feature flag behavior."""

    @pytest.fixture
    def options_v83_false(self):
        return TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
            quality_delivery_v83=False,
        )

    @pytest.fixture
    def options_v83_true(self):
        return TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
            quality_delivery_v83=True,
        )

    def test_quality_delivery_v83_false_zero_execution(self, options_v83_false, sample_chunks, sample_records):
        text = "\n\n".join(sample_chunks)
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options_v83_false, matched_terms={})

        check_names = [c.name for c in result.checks]
        assert "narrative_pov_continuity" not in check_names
        assert "tense_voice_consistency" not in check_names
        assert len(result.checks) == 9

    def test_quality_delivery_v83_true_executes_checks(self, options_v83_true, sample_chunks, sample_records):
        for rec in sample_records:
            if "metadata" not in rec:
                rec["metadata"] = {}
            if "context_state" not in rec["metadata"]:
                rec["metadata"]["context_state"] = {}
            rec["metadata"]["context_state"]["narrative"] = _make_narrative("third_person", "neutral", "past")
            rec["metadata"]["context_state"]["boundary"] = {
                "type": "same_scene", "scene_id": None, "chapter_id": None, "confidence": 1.0, "metadata": {}
            }

        text = "\n\n".join(sample_chunks)
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options_v83_true, matched_terms={})

        check_names = [c.name for c in result.checks]
        assert "narrative_pov_continuity" in check_names
        assert "tense_voice_consistency" in check_names
        assert len(result.checks) == 11

        pov_check = next(c for c in result.checks if c.name == "narrative_pov_continuity")
        tense_check = next(c for c in result.checks if c.name == "tense_voice_consistency")
        assert pov_check.passed is True
        assert tense_check.passed is True


class TestRM85ProductionShapedFixtures:
    """Tests verifying production-shaped fixtures match NarrativeState.to_prompt_context() exactly."""

    def test_fixture_includes_all_narrative_fields(self):
        narrative = _make_narrative("third_person", "balanced", "past", "neutral", "mode=test", ["t1"], 5)
        assert narrative["perspective"] == "third_person"
        assert narrative["voice"] == "balanced"
        assert narrative["tense"] == "past"
        assert narrative["emotional_tone"] == "neutral"
        assert narrative["focus"] == "mode=test"
        assert narrative["transitions"] == ["t1"]
        assert narrative["metadata"] == {"updates": 5}

    def test_fixture_includes_all_context_state_fields(self):
        ctx = _make_context_state("scene_1", "chapter_1", "same_scene", _make_narrative())
        assert "scene_id" in ctx
        assert "scene_version" in ctx
        assert "chapter_id" in ctx
        assert "boundary" in ctx
        assert "narrative" in ctx
        assert "context_selection_fingerprint" in ctx
        assert "selected_context_ids" in ctx

    def test_fixture_boundary_has_correct_structure(self):
        ctx = _make_context_state("scene_1", "chapter_1", "scene_transition")
        boundary = ctx["boundary"]
        assert boundary["type"] == "scene_transition"
        assert boundary["scene_id"] == "scene_1"
        assert boundary["chapter_id"] is None
        assert "confidence" in boundary
        assert "metadata" in boundary

    def test_chunk_record_has_source_and_metadata(self):
        rec = _make_chunk_record("scene_1", "chapter_1", "same_scene", _make_narrative(), 100)
        assert "source" in rec
        assert "metadata" in rec
        assert rec["source"]["char_count"] == 100
        assert "context_state" in rec["metadata"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])