"""RM-7.3.2 P3b — Entity Form-Aware Matching Policy Regression Tests.

Tests the Form-Aware Matching Policy for:
- FULL / GIVEN / FAMILY / FORMAL / INTIMATE matching semantics
- FORMAL supports both "姓氏＋先生" and "全名＋先生"
- INTIMATE only matches "given_name + suffix", NOT "full_name + suffix"
- GIVEN must NOT match FULL expansion
- FAMILY must NOT match FULL expansion
- CJK variant normalization in comparison layer only
"""

from __future__ import annotations

import pytest

from core.entity_consistency import (
    ConsistencyChecker,
    FormAwareMatchingPolicy,
    MatchResult,
    NameFormType,
    create_matching_policy,
)
from core.entity_consistency.matching_policy import FormMatchSpec
from core.knowledge_evolution.models import EntityType


# ---------------------------------------------------------------------------
# Test entity form translations (matching the RM-7.3.1 canary fixture)
# ---------------------------------------------------------------------------
ENTITY_FORMS = {
    NameFormType.FULL_NAME: "鄭泰義",
    NameFormType.GIVEN_NAME: "泰義",
    NameFormType.FAMILY_NAME: "鄭",
    NameFormType.FORMAL: "鄭先生",
    NameFormType.INTIMATE: "泰義啊",
}


def _make_policy() -> FormAwareMatchingPolicy:
    return create_matching_policy(
        full_name="鄭泰義",
        given_name="泰義",
        family_name="鄭",
        formal="鄭先生",
        intimate="泰義啊",
    )


# ---------------------------------------------------------------------------
# 1. FormMatchSpec construction tests
# ---------------------------------------------------------------------------

class TestFormMatchSpecConstruction:
    def test_full_name_spec(self):
        policy = _make_policy()
        spec = policy.get_spec(NameFormType.FULL_NAME)
        assert spec is not None
        assert spec.form_type == NameFormType.FULL_NAME
        assert "鄭泰義" in spec.allowed_patterns
        assert spec.requires_exact is True

    def test_given_name_spec_forbids_full_expansion(self):
        policy = _make_policy()
        spec = policy.get_spec(NameFormType.GIVEN_NAME)
        assert spec is not None
        assert "泰義" in spec.allowed_patterns
        assert "鄭泰義" in spec.forbidden_patterns

    def test_family_name_spec_forbids_full_expansion(self):
        policy = _make_policy()
        spec = policy.get_spec(NameFormType.FAMILY_NAME)
        assert spec is not None
        assert "鄭" in spec.allowed_patterns
        assert "鄭泰義" in spec.forbidden_patterns

    def test_formal_spec_allows_both_patterns(self):
        policy = _make_policy()
        spec = policy.get_spec(NameFormType.FORMAL)
        assert spec is not None
        # Should allow both family+honorific and full+honorific
        assert "鄭先生" in spec.allowed_patterns
        assert "鄭泰義先生" in spec.allowed_patterns

    def test_intimate_spec_forbids_full_expansion(self):
        policy = _make_policy()
        spec = policy.get_spec(NameFormType.INTIMATE)
        assert spec is not None
        assert "泰義啊" in spec.allowed_patterns
        assert "鄭泰義啊" in spec.forbidden_patterns


# ---------------------------------------------------------------------------
# 2. Policy check_match tests - MATCH cases
# ---------------------------------------------------------------------------

class TestPolicyMatchCases:
    def test_full_name_match(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.FULL_NAME, "這是鄭泰義的故事")
        assert result == MatchResult.MATCH

    def test_given_name_match(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.GIVEN_NAME, "泰義走了")
        assert result == MatchResult.MATCH

    def test_family_name_match(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.FAMILY_NAME, "鄭先生說")
        assert result == MatchResult.MATCH

    def test_formal_match_family_honorific(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.FORMAL, "鄭先生走了")
        assert result == MatchResult.MATCH

    def test_formal_match_full_honorific(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.FORMAL, "鄭泰義先生走了")
        assert result == MatchResult.MATCH

    def test_intimate_match(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.INTIMATE, "泰義啊，過來")
        assert result == MatchResult.MATCH


# ---------------------------------------------------------------------------
# 3. Policy check_match tests - MISMATCH cases (forbidden patterns)
# ---------------------------------------------------------------------------

class TestPolicyMismatchCases:
    def test_intimate_mismatch_on_full_expansion(self):
        """鄭泰義啊 must NOT match INTIMATE."""
        policy = _make_policy()
        result = policy.check_match(NameFormType.INTIMATE, "鄭泰義啊，過來")
        assert result == MatchResult.MISMATCH

    def test_given_mismatch_on_full_expansion(self):
        """GIVEN must NOT match when only FULL is present."""
        policy = _make_policy()
        # Text contains only full name, not given name standalone
        result = policy.check_match(NameFormType.GIVEN_NAME, "鄭泰義走了")
        assert result == MatchResult.MISMATCH

    def test_family_mismatch_on_full_expansion(self):
        """FAMILY must NOT match when only FULL is present."""
        policy = _make_policy()
        # Text contains only full name, not family name standalone
        result = policy.check_match(NameFormType.FAMILY_NAME, "鄭泰義走了")
        assert result == MatchResult.MISMATCH


# ---------------------------------------------------------------------------
# 4. CJK variant normalization tests
# ---------------------------------------------------------------------------

class TestCJKVariantNormalization:
    def test_cjk_variant_in_translation_matches(self):
        """CJK variant in translation should match via normalization."""
        policy = _make_policy()
        # U+912D is variant of 鄭 (U+9109)
        variant_text = "這是\u912d泰義的故事"  # Variant 鄭 + 泰義
        result = policy.check_match(NameFormType.FULL_NAME, variant_text)
        assert result == MatchResult.MATCH

    def test_cjk_variant_in_given_name(self):
        policy = _make_policy()
        # Given name doesn't have variants typically, but test anyway
        result = policy.check_match(NameFormType.GIVEN_NAME, "泰義走了")
        assert result == MatchResult.MATCH

    def test_cjk_variant_in_formal(self):
        policy = _make_policy()
        variant_formal = "\u912d先生"  # Variant 鄭 + 先生
        result = policy.check_match(NameFormType.FORMAL, variant_formal)
        assert result == MatchResult.MATCH


# ---------------------------------------------------------------------------
# 5. ConsistencyChecker form-aware integration tests
# ---------------------------------------------------------------------------

class TestConsistencyCheckerFormAware:
    def setup_method(self):
        self.checker = ConsistencyChecker()
        self.policy = _make_policy()
        self.checker.set_form_policy(self.policy)

    def test_check_one_form_aware_full_match(self):
        mismatch = self.checker.check_one_form_aware(
            source="정태의",
            expected="鄭泰義",
            translated_text="這是鄭泰義的故事",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1
        assert self.checker.matches[0].expected == "鄭泰義"
        assert self.checker.matches[0].found == "鄭泰義"

    def test_check_one_form_aware_given_match(self):
        mismatch = self.checker.check_one_form_aware(
            source="태의",
            expected="泰義",
            translated_text="泰義走了",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1
        assert self.checker.matches[0].expected == "泰義"
        assert self.checker.matches[0].found == "泰義"

    def test_check_one_form_aware_family_match(self):
        mismatch = self.checker.check_one_form_aware(
            source="鄭",
            expected="鄭",
            translated_text="鄭先生說",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1
        assert self.checker.matches[0].expected == "鄭"

    def test_check_one_form_aware_formal_family_honorific(self):
        mismatch = self.checker.check_one_form_aware(
            source="鄭先生",
            expected="鄭先生",
            translated_text="鄭先生走了",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1

    def test_check_one_form_aware_formal_full_honorific(self):
        mismatch = self.checker.check_one_form_aware(
            source="鄭泰義先生",
            expected="鄭泰義先生",
            translated_text="鄭泰義先生走了",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1

    def test_check_one_form_aware_intimate_match(self):
        mismatch = self.checker.check_one_form_aware(
            source="泰義啊",
            expected="泰義啊",
            translated_text="泰義啊，過來",
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1
        assert self.checker.matches[0].found == "泰義啊"

    def test_check_one_form_aware_intimate_mismatch_on_full_expansion(self):
        """鄭泰義啊 must be detected as MISMATCH for INTIMATE."""
        mismatch = self.checker.check_one_form_aware(
            source="泰義啊",
            expected="泰義啊",
            translated_text="鄭泰義啊，過來",  # WRONG: full name + intimate suffix
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is not None
        assert mismatch.severity.name == "HIGH"
        assert "FORBIDDEN" in mismatch.found or "鄭泰義啊" in mismatch.found
        assert len(self.checker.mismatches) == 1

    def test_check_one_form_aware_given_mismatch_on_full_only(self):
        """GIVEN must mismatch when only FULL is present in text."""
        mismatch = self.checker.check_one_form_aware(
            source="태의",
            expected="泰義",
            translated_text="鄭泰義走了",  # Only full name, no standalone given
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is not None
        assert len(self.checker.mismatches) == 1

    def test_check_one_form_aware_family_mismatch_on_full_only(self):
        """FAMILY must mismatch when only FULL is present in text."""
        mismatch = self.checker.check_one_form_aware(
            source="鄭",
            expected="鄭",
            translated_text="鄭泰義走了",  # Only full name, no standalone family
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is not None
        assert len(self.checker.mismatches) == 1

    def test_check_entries_form_aware_all_pass(self):
        """All five forms present correctly should pass."""
        knowledge_entries = [
            {"source": "정태의", "canonical": "鄭泰義", "entity_type": "CHARACTER", "entity_id": "char_1"},
            {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "char_1"},
            {"source": "鄭", "canonical": "鄭", "entity_type": "CHARACTER", "entity_id": "char_1"},
            {"source": "鄭先生", "canonical": "鄭先生", "entity_type": "CHARACTER", "entity_id": "char_1"},
            {"source": "泰義啊", "canonical": "泰義啊", "entity_type": "CHARACTER", "entity_id": "char_1"},
        ]
        translated = "鄭泰義和泰義還有鄭，鄭先生說泰義啊"
        self.checker.check_entries_form_aware(knowledge_entries, translated)
        assert self.checker.pass_count == 5
        assert self.checker.mismatch_count == 0

    def test_check_entries_form_aware_intimate_mismatch(self):
        """INTIMATE mismatch should be caught."""
        knowledge_entries = [
            {"source": "泰義啊", "canonical": "泰義啊", "entity_type": "CHARACTER", "entity_id": "char_1"},
        ]
        translated = "鄭泰義啊"  # Wrong: full name + intimate suffix
        self.checker.check_entries_form_aware(knowledge_entries, translated)
        assert self.checker.pass_count == 0
        assert self.checker.mismatch_count == 1

    def test_check_entries_form_aware_given_mismatch(self):
        """GIVEN mismatch when only FULL present."""
        knowledge_entries = [
            {"source": "태의", "canonical": "泰義", "entity_type": "CHARACTER", "entity_id": "char_1"},
        ]
        translated = "鄭泰義"  # Only full name
        self.checker.check_entries_form_aware(knowledge_entries, translated)
        assert self.checker.pass_count == 0
        assert self.checker.mismatch_count == 1

    def test_check_entries_form_aware_family_mismatch(self):
        """FAMILY mismatch when only FULL present."""
        knowledge_entries = [
            {"source": "鄭", "canonical": "鄭", "entity_type": "CHARACTER", "entity_id": "char_1"},
        ]
        translated = "鄭泰義"  # Only full name
        self.checker.check_entries_form_aware(knowledge_entries, translated)
        assert self.checker.pass_count == 0
        assert self.checker.mismatch_count == 1

    def test_cjk_variant_in_form_aware_check(self):
        """CJK variant should match in form-aware check."""
        mismatch = self.checker.check_one_form_aware(
            source="정태의",
            expected="鄭泰義",
            translated_text="這是\u912d泰義的故事",  # Variant 鄭
            entity_type=EntityType.CHARACTER,
        )
        assert mismatch is None
        assert len(self.checker.matches) == 1


# ---------------------------------------------------------------------------
# 6. Edge cases and boundary conditions
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_policy_without_form_defined(self):
        """Policy should handle missing form definitions gracefully."""
        policy = create_matching_policy(full_name="鄭泰義")  # Only full name
        result = policy.check_match(NameFormType.GIVEN_NAME, "泰義")
        assert result == MatchResult.NO_EXPECTED_FORM

    def test_policy_with_empty_translation(self):
        policy = _make_policy()
        result = policy.check_match(NameFormType.FULL_NAME, "")
        assert result == MatchResult.MISMATCH

    def test_formal_without_family_or_full_defined(self):
        """FORMAL spec should work even if only formal is defined."""
        policy = create_matching_policy(formal="鄭先生")
        spec = policy.get_spec(NameFormType.FORMAL)
        assert spec is not None
        assert "鄭先生" in spec.allowed_patterns

    def test_source_inference_from_korean_suffixes(self):
        """_get_form_type_from_source should infer from Korean suffixes."""
        checker = ConsistencyChecker()
        # FORMAL inference
        assert checker._get_form_type_from_source("정 씨", EntityType.CHARACTER) == NameFormType.FORMAL
        assert checker._get_form_type_from_source("정 선생", EntityType.CHARACTER) == NameFormType.FORMAL
        # INTIMATE inference
        assert checker._get_form_type_from_source("태의야", EntityType.CHARACTER) == NameFormType.INTIMATE
        assert checker._get_form_type_from_source("태의아", EntityType.CHARACTER) == NameFormType.INTIMATE
        # Length-based inference
        assert checker._get_form_type_from_source("鄭", EntityType.CHARACTER) == NameFormType.FAMILY_NAME
        assert checker._get_form_type_from_source("泰義", EntityType.CHARACTER) == NameFormType.GIVEN_NAME
        assert checker._get_form_type_from_source("鄭泰義", EntityType.CHARACTER) == NameFormType.FULL_NAME
        # Non-character entity types return None
        assert checker._get_form_type_from_source("鄭泰義", EntityType.LOCATION) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])