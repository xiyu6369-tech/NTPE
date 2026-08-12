# tests/unit/translation_release/test_validator.py

import pytest
from pathlib import Path

from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_release.validator import validate_final_novel, ValidationResult, ValidationCheck


@pytest.fixture
def sample_chunks():
    return [
        "主角走進了房間。",
        "他看到了桌上有一封信。",
        "信上寫著：明天見。",
    ]


@pytest.fixture
def sample_records():
    return [
        {
            "source": {"char_count": 50, "chunk_text": "주인공이 방에 들어갔다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "same_scene"},
                }
            },
        },
        {
            "source": {"char_count": 45, "chunk_text": "그는 책상 위에 편지가 있는 것을 보았다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "same_scene"},
                }
            },
        },
        {
            "source": {"char_count": 48, "chunk_text": "편지에는 내일 보자고 쓰여 있었다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_2",
                    "chapter_id": "chapter_2",
                    "boundary": {"type": "chapter_transition"},
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
        matched_terms = {"主角": "主角"}  # only terms actually in source
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
        text = "안녕하세요\n\n" + "\n\n".join(sample_chunks)  # Korean residue
        locked_dict = {}
        matched_terms = {}
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        assert result.overall_passed is False
        assert "korean_residue_global" in result.failed_critical

    def test_validator_locked_terms_only_validates_matched(self, sample_chunks, sample_records):
        """Glossary entries not in source should not cause FAIL."""
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        locked_dict = {"主角": "主角", "未出現角色": "未出現角色"}  # second term not in source
        matched_terms = {"主角": "主角"}  # only validated term
        text = "主角出現了。"  # only 主角 appears
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
        assert result.overall_passed is True  # should PASS, 未出現角色 not validated

    def test_validator_length_ratio_from_source_metadata(self, sample_chunks, sample_records):
        """Length ratio uses source char_count from chunk_records."""
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
        # source_total = 50+45+48 = 143, translated ≈ 40 chars -> ratio ~0.28 < 0.5 -> should fail major
        check = next(c for c in result.checks if c.name == "length_ratio_global")
        assert check.details["verifiable"] is True
        assert check.details["verifiable_chunks"] == 3

    def test_validator_length_ratio_unverifiable_when_no_source(self, sample_chunks):
        """Length ratio marked unverifiable when no source char_count available."""
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.5,
            strict_lock_terms=True,
        )
        # Records without source.char_count
        records_no_source = [
            {"source": {}, "metadata": {}},
            {"source": {"chunk_text": "test"}, "metadata": {"source": {}}},
        ]
        locked_dict = {}
        matched_terms = {}
        text = "測試文本。"
        result = validate_final_novel(text, locked_dict, records_no_source, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        check = next(c for c in result.checks if c.name == "length_ratio_global")
        assert check.details["verifiable"] is False
        assert check.severity == "info"
        assert check.passed is True  # unverifiable -> neutral (passes)

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
        # Text with empty paragraphs and excessive newlines
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
        # Text with ASCII punctuation
        text = "Hello, world! How are you? \"Quote\"."
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "punctuation_consistency")
        # ASCII punctuation should fail the CJK ratio check
        assert check.details["cjk_ratio"] < 0.95

    def test_validator_chinese_char_ratio(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        # Mostly Chinese text
        text = "這是一段中文文本。包含漢字。"
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
        # Unbalanced quotes
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
        # Using alias for 鄭泰義 (e.g., 定泰義 is an alias)
        locked_dict = {"鄭泰義": "鄭泰義"}
        matched_terms = {"鄭泰義": "鄭泰義"}
        text = "定泰義出現了。"  # alias violation
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
        text = "\n\n".join(sample_chunks)
        result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms=matched_terms)
        # With all checks passing, score should be 100
        assert result.overall_score == 100.0

    def test_validator_failed_critical_blocks_pass(self, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=0,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        text = "안녕하세요"  # Korean residue
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        assert result.overall_passed is False
        assert "korean_residue_global" in result.failed_critical

    def test_validator_korean_threshold_calculation(self, sample_records):
        """max_korean_chars * chunk_total * 0.5 threshold."""
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            max_korean_chars=2,
            min_length_ratio=0.1,
            strict_lock_terms=True,
        )
        # 3 chunks * 2 *  max_korean_chars * 0.5 = 3 allowed Korean chars
        text = "안녕"  # 2 Korean chars - should pass
        result = validate_final_novel(text, {}, sample_records, {"passed": True, "errors": 0}, options, matched_terms={})
        check = next(c for c in result.checks if c.name == "korean_residue_global")
        assert check.details["max_allowed"] == 3
        assert check.passed is True

        text2 = "안녕하세요"  # 5 Korean chars - should fail
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])