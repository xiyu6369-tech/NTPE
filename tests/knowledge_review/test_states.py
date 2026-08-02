"""
State Transition Tests

測試審核狀態轉換規則。
"""

import pytest

from core.knowledge_review.states import (
    ReviewState,
    STATE_TRANSITIONS,
    validate_transition,
    get_valid_transitions,
)
from core.knowledge_review.errors import InvalidStateTransition


class TestStateTransitions:
    """測試狀態轉換規則。"""

    def test_pending_to_auto_approved(self):
        """PENDING -> AUTO_APPROVED 應該合法。"""
        validate_transition(ReviewState.PENDING, ReviewState.AUTO_APPROVED)

    def test_pending_to_human_review_required(self):
        """PENDING -> HUMAN_REVIEW_REQUIRED 應該合法。"""
        validate_transition(ReviewState.PENDING, ReviewState.HUMAN_REVIEW_REQUIRED)

    def test_pending_to_approved_direct(self):
        """PENDING -> APPROVED 直接通過現在允許。"""
        validate_transition(ReviewState.PENDING, ReviewState.APPROVED)

    def test_pending_to_rejected_direct(self):
        """PENDING -> REJECTED 直接拒絕現在允許。"""
        validate_transition(ReviewState.PENDING, ReviewState.REJECTED)

    def test_auto_approved_to_superseded(self):
        """AUTO_APPROVED -> SUPERSEDED 應該合法。"""
        validate_transition(ReviewState.AUTO_APPROVED, ReviewState.SUPERSEDED)

    def test_human_review_to_approved(self):
        """HUMAN_REVIEW_REQUIRED -> APPROVED 應該合法。"""
        validate_transition(ReviewState.HUMAN_REVIEW_REQUIRED, ReviewState.APPROVED)

    def test_human_review_to_rejected(self):
        """HUMAN_REVIEW_REQUIRED -> REJECTED 應該合法。"""
        validate_transition(ReviewState.HUMAN_REVIEW_REQUIRED, ReviewState.REJECTED)

    def test_human_review_to_human_review(self):
        """HUMAN_REVIEW_REQUIRED -> HUMAN_REVIEW_REQUIRED (REVISE) 應該合法。"""
        validate_transition(ReviewState.HUMAN_REVIEW_REQUIRED, ReviewState.HUMAN_REVIEW_REQUIRED)

    def test_approved_to_superseded(self):
        """APPROVED -> SUPERSEDED 應該合法。"""
        validate_transition(ReviewState.APPROVED, ReviewState.SUPERSEDED)

    def test_approved_to_human_review(self):
        """APPROVED -> HUMAN_REVIEW_REQUIRED (REVISE) 應該合法。"""
        validate_transition(ReviewState.APPROVED, ReviewState.HUMAN_REVIEW_REQUIRED)

    def test_rejected_to_human_review(self):
        """REJECTED -> HUMAN_REVIEW_REQUIRED (REVISE) 應該合法。"""
        validate_transition(ReviewState.REJECTED, ReviewState.HUMAN_REVIEW_REQUIRED)

    def test_superseded_no_transitions(self):
        """SUPERSEDED 不應該有任何輸出轉換。"""
        assert get_valid_transitions(ReviewState.SUPERSEDED) == frozenset()

        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.SUPERSEDED, ReviewState.APPROVED)

        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.SUPERSEDED, ReviewState.HUMAN_REVIEW_REQUIRED)

        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.SUPERSEDED, ReviewState.AUTO_APPROVED)

    def test_rejected_to_approved_forbidden(self):
        """REJECTED -> APPROVED 仍然禁止。"""
        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.REJECTED, ReviewState.APPROVED)

    def test_invalid_pending_to_superseded(self):
        """PENDING 不能直接轉到 SUPERSEDED。"""
        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.PENDING, ReviewState.SUPERSEDED)

    def test_invalid_human_review_to_auto_approved(self):
        """HUMAN_REVIEW_REQUIRED 不能轉到 AUTO_APPROVED。"""
        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.HUMAN_REVIEW_REQUIRED, ReviewState.AUTO_APPROVED)

    def test_invalid_human_review_to_superseded(self):
        """HUMAN_REVIEW_REQUIRED 不能直接轉到 SUPERSEDED。"""
        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.HUMAN_REVIEW_REQUIRED, ReviewState.SUPERSEDED)

    def test_invalid_approved_to_auto_approved(self):
        """APPROVED 不能轉到 AUTO_APPROVED。"""
        with pytest.raises(InvalidStateTransition):
            validate_transition(ReviewState.APPROVED, ReviewState.AUTO_APPROVED)

    def test_state_properties(self):
        """測試狀態屬性。"""
        assert ReviewState.PENDING.is_active is True
        assert ReviewState.PENDING.is_terminal is False
        assert ReviewState.PENDING.requires_human_review is False

        assert ReviewState.AUTO_APPROVED.is_active is True
        assert ReviewState.AUTO_APPROVED.is_terminal is False
        assert ReviewState.AUTO_APPROVED.requires_human_review is False

        assert ReviewState.HUMAN_REVIEW_REQUIRED.is_active is True
        assert ReviewState.HUMAN_REVIEW_REQUIRED.is_terminal is False
        assert ReviewState.HUMAN_REVIEW_REQUIRED.requires_human_review is True

        # APPROVED 和 REJECTED 現在是 active（可繼續處理 REVISE）
        assert ReviewState.APPROVED.is_active is True
        assert ReviewState.APPROVED.is_terminal is False
        assert ReviewState.APPROVED.requires_human_review is False

        assert ReviewState.REJECTED.is_active is True
        assert ReviewState.REJECTED.is_terminal is False
        assert ReviewState.REJECTED.requires_human_review is False

        # 只有 SUPERSEDED 是終態
        assert ReviewState.SUPERSEDED.is_active is False
        assert ReviewState.SUPERSEDED.is_terminal is True
        assert ReviewState.SUPERSEDED.requires_human_review is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])