"""
Review Engine Tests

測試審核引擎功能。
"""

import pytest
from uuid import uuid4

from core.knowledge_review.review_engine import (
    ReviewEngine,
    ReviewAction,
    ReviewDecision,
)
from core.knowledge_review.models import ReviewItem, EntityType, ValidationResult
from core.knowledge_review.audit_log import AuditLog
from core.knowledge_review.errors import InvalidReviewStateError


class TestReviewEngine:
    """測試審核引擎。"""

    def setup_method(self):
        """每個測試前的設置。"""
        self.audit_log = AuditLog()
        self.engine = ReviewEngine(audit_log=self.audit_log)

    def create_item(self, state="PENDING", confidence=0.80):
        """建立測試用的 ReviewItem。"""
        return ReviewItem(
            entity_type=EntityType.CHARACTER,
            entity_id=uuid4(),
            confidence_score=confidence,
            review_state=state,
            validation_result=ValidationResult.PASS,
        )

    def test_approve_from_human_review(self):
        """測試從 HUMAN_REVIEW_REQUIRED 通過。"""
        item = self.create_item(state="HUMAN_REVIEW_REQUIRED")
        result = self.engine.submit_review(item, ReviewAction.APPROVE, "審核通過")

        assert result.decision == ReviewDecision.APPROVED
        assert result.new_state == "APPROVED"
        assert result.review_item.review_state == "APPROVED"

    def test_approve_from_pending(self):
        """測試從 PENDING 直接通過。"""
        item = self.create_item(state="PENDING")
        result = self.engine.submit_review(item, ReviewAction.APPROVE, "審核通過")

        assert result.decision == ReviewDecision.APPROVED
        assert result.new_state == "APPROVED"

    def test_reject_from_human_review(self):
        """測試從 HUMAN_REVIEW_REQUIRED 拒絕。"""
        item = self.create_item(state="HUMAN_REVIEW_REQUIRED")
        result = self.engine.submit_review(item, ReviewAction.REJECT, "不符合規範")

        assert result.decision == ReviewDecision.REJECTED
        assert result.new_state == "REJECTED"

    def test_reject_from_pending(self):
        """測試從 PENDING 直接拒絕。"""
        item = self.create_item(state="PENDING")
        result = self.engine.submit_review(item, ReviewAction.REJECT, "不符合規範")

        assert result.decision == ReviewDecision.REJECTED
        assert result.new_state == "REJECTED"

    def test_revise_from_human_review(self):
        """測試從 HUMAN_REVIEW_REQUIRED 要求修訂。"""
        item = self.create_item(state="HUMAN_REVIEW_REQUIRED")
        result = self.engine.submit_review(item, ReviewAction.REVISE, "需要修改")

        assert result.decision == ReviewDecision.REVISED
        assert result.new_state == "HUMAN_REVIEW_REQUIRED"

    def test_revise_from_approved(self):
        """測試從 APPROVED 要求修訂（回到 HUMAN_REVIEW_REQUIRED）。"""
        item = self.create_item(state="APPROVED")
        result = self.engine.submit_review(item, ReviewAction.REVISE, "需要修改")

        assert result.decision == ReviewDecision.REVISED
        assert result.new_state == "HUMAN_REVIEW_REQUIRED"

    def test_approve_from_approved_raises(self):
        """測試從 APPROVED 再次通過應拋出異常。"""
        item = self.create_item(state="APPROVED")
        with pytest.raises(InvalidReviewStateError):
            self.engine.submit_review(item, ReviewAction.APPROVE, "重複通過")

    def test_reject_from_rejected_raises(self):
        """測試從 REJECTED 再次拒絕應拋出異常。"""
        item = self.create_item(state="REJECTED")
        with pytest.raises(InvalidReviewStateError):
            self.engine.submit_review(item, ReviewAction.REJECT, "重複拒絕")

    def test_approve_from_rejected_raises(self):
        """測試從 REJECTED 通過應拋出異常（禁止 REJECTED -> APPROVED）。"""
        item = self.create_item(state="REJECTED")
        with pytest.raises(InvalidReviewStateError):
            self.engine.submit_review(item, ReviewAction.APPROVE, "嘗試從拒絕轉通過")

    def test_revise_from_rejected(self):
        """測試從 REJECTED 要求修訂（回到 HUMAN_REVIEW_REQUIRED）。"""
        item = self.create_item(state="REJECTED")
        result = self.engine.submit_review(item, ReviewAction.REVISE, "重新審核")

        assert result.decision == ReviewDecision.REVISED
        assert result.new_state == "HUMAN_REVIEW_REQUIRED"

    def test_auto_approve(self):
        """測試自動通過（信心度閘控觸發）。"""
        item = self.create_item(state="PENDING", confidence=0.90)
        result = self.engine.auto_approve(item, "高信心度自動通過")

        assert result.decision == ReviewDecision.APPROVED
        assert result.new_state == "AUTO_APPROVED"
        assert result.review_item.review_state == "AUTO_APPROVED"

    def test_auto_approve_not_pending_raises(self):
        """測試非 PENDING 狀態自動通過應拋出異常。"""
        item = self.create_item(state="APPROVED", confidence=0.90)
        with pytest.raises(InvalidReviewStateError):
            self.engine.auto_approve(item)

    def test_supersede_from_approved(self):
        """測試從 APPROVED 標記為 SUPERSEDED。"""
        item = self.create_item(state="APPROVED")
        result = self.engine.supersede(item, "新版本取代")

        assert result.decision == ReviewDecision.NO_CHANGE
        assert result.new_state == "SUPERSEDED"

    def test_supersede_from_auto_approved(self):
        """測試從 AUTO_APPROVED 標記為 SUPERSEDED。"""
        item = self.create_item(state="AUTO_APPROVED")
        result = self.engine.supersede(item, "新版本取代")

        assert result.decision == ReviewDecision.NO_CHANGE
        assert result.new_state == "SUPERSEDED"

    def test_supersede_from_pending_raises(self):
        """測試從 PENDING 標記為 SUPERSEDED 應拋出異常。"""
        item = self.create_item(state="PENDING")
        with pytest.raises(InvalidReviewStateError):
            self.engine.supersede(item)

    def test_audit_log_recorded(self):
        """測試審計日誌記錄。"""
        item = self.create_item(state="HUMAN_REVIEW_REQUIRED")
        self.engine.submit_review(item, ReviewAction.APPROVE, "測試通過", "test_user")

        history = self.audit_log.get_history(item.review_id)
        assert len(history) == 1
        assert history[0].action == "APPROVE"
        assert history[0].actor == "test_user"
        assert history[0].reason == "測試通過"
        assert history[0].previous_state == "HUMAN_REVIEW_REQUIRED"
        assert history[0].new_state == "APPROVED"

    def test_auto_approve_audit_log(self):
        """測試自動通過審計日誌。"""
        item = self.create_item(state="PENDING", confidence=0.90)
        self.engine.auto_approve(item, "自動通過", "confidence_gate")

        history = self.audit_log.get_history(item.review_id)
        assert len(history) == 1
        assert history[0].action == "AUTO_APPROVE"
        assert history[0].actor == "confidence_gate"

    def test_no_audit_log_when_none(self):
        """測試無審計日誌實例時不記錄。"""
        engine = ReviewEngine(audit_log=None)
        item = self.create_item(state="HUMAN_REVIEW_REQUIRED")
        result = engine.submit_review(item, ReviewAction.APPROVE, "測試")

        assert result.decision == ReviewDecision.APPROVED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
