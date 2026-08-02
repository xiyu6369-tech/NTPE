"""
Confidence Gate Tests

測試信心度閘控邏輯。
"""

import pytest

from core.knowledge_review.confidence_gate import (
    ConfidenceGate,
    ConfidenceGateResult,
    ConfidenceGateDecision,
)
from core.knowledge_review.models import ReviewItem, EntityType, ValidationResult
from core.knowledge_review.errors import InvalidConfidenceScoreError


class TestConfidenceGate:
    """測試信心度閘控。"""

    def setup_method(self):
        """每個測試前的設置。"""
        self.gate = ConfidenceGate(auto_approve_threshold=0.85)

    def test_high_confidence_auto_approve(self):
        """高信心度且驗證通過 -> AUTO_APPROVED。"""
        decision = self.gate.evaluate(
            confidence_score=0.90,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.AUTO_APPROVED
        assert decision.review_state == 'AUTO_APPROVED'
        assert decision.confidence_score == 0.90
        assert decision.schema_pass is True
        assert decision.business_rule_pass is True

    def test_low_confidence_human_review(self):
        """低信心度 -> HUMAN_REVIEW_REQUIRED。"""
        decision = self.gate.evaluate(
            confidence_score=0.80,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED
        assert decision.review_state == 'HUMAN_REVIEW_REQUIRED'
        assert '信心度' in decision.reason

    def test_schema_fail_forces_review(self):
        """Schema 驗證失敗 -> 強制人工審核。"""
        decision = self.gate.evaluate(
            confidence_score=0.95,
            schema_pass=False,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED
        assert decision.review_state == 'HUMAN_REVIEW_REQUIRED'
        assert 'Schema 驗證失敗' in decision.reason

    def test_business_rule_fail_forces_review(self):
        """業務規則驗證失敗 -> 強制人工審核。"""
        decision = self.gate.evaluate(
            confidence_score=0.95,
            schema_pass=True,
            business_rule_pass=False,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED
        assert decision.review_state == 'HUMAN_REVIEW_REQUIRED'
        assert '業務規則驗證失敗' in decision.reason

    def test_all_fail_forces_review(self):
        """全部失敗 -> 強制人工審核。"""
        decision = self.gate.evaluate(
            confidence_score=0.70,
            schema_pass=False,
            business_rule_pass=False,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED
        assert decision.review_state == 'HUMAN_REVIEW_REQUIRED'
        assert '信心度' in decision.reason
        assert 'Schema 驗證失敗' in decision.reason
        assert '業務規則驗證失敗' in decision.reason

    def test_threshold_boundary(self):
        """測試門檻邊界值。"""
        decision = self.gate.evaluate(
            confidence_score=0.85,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.AUTO_APPROVED
        decision = self.gate.evaluate(
            confidence_score=0.849,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED

    def test_custom_threshold(self):
        """測試自訂門檻。"""
        gate = ConfidenceGate(auto_approve_threshold=0.90)
        decision = gate.evaluate(
            confidence_score=0.88,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED
        decision = gate.evaluate(
            confidence_score=0.90,
            schema_pass=True,
            business_rule_pass=True,
        )
        assert decision.result == ConfidenceGateResult.AUTO_APPROVED

    def test_invalid_confidence_score_raises(self):
        """無效信心度分數應拋出異常。"""
        with pytest.raises(InvalidConfidenceScoreError):
            self.gate.evaluate(
                confidence_score=1.5,
                schema_pass=True,
                business_rule_pass=True,
            )
        with pytest.raises(InvalidConfidenceScoreError):
            self.gate.evaluate(
                confidence_score=-0.1,
                schema_pass=True,
                business_rule_pass=True,
            )

    def test_evaluate_item(self):
        """測試直接評估 ReviewItem。"""
        item = ReviewItem(
            entity_type=EntityType.CHARACTER,
            entity_id='test-entity-id',
            confidence_score=0.90,
            metadata={
                'schema_pass': True,
                'business_rule_pass': True,
            },
        )
        decision = self.gate.evaluate_item(item)
        assert decision.result == ConfidenceGateResult.AUTO_APPROVED

    def test_evaluate_item_with_metadata_false(self):
        """測試 metadata 中包含 false 值。"""
        item = ReviewItem(
            entity_type=EntityType.GLOSSARY,
            entity_id='test-entity-id',
            confidence_score=0.90,
            metadata={
                'schema_pass': False,
                'business_rule_pass': True,
            },
        )
        decision = self.gate.evaluate_item(item)
        assert decision.result == ConfidenceGateResult.HUMAN_REVIEW_REQUIRED

    def test_evaluate_item_defaults_to_true(self):
        """測試 metadata 缺失時預設為 True。"""
        item = ReviewItem(
            entity_type=EntityType.SCENE,
            entity_id='test-entity-id',
            confidence_score=0.90,
            metadata={},
        )
        decision = self.gate.evaluate_item(item)
        assert decision.result == ConfidenceGateResult.AUTO_APPROVED

    def test_decision_to_dict(self):
        """測試決策結果序列化。"""
        decision = self.gate.evaluate(
            confidence_score=0.90,
            schema_pass=True,
            business_rule_pass=True,
        )
        data = decision.to_dict()
        assert data['result'] == 'AUTO_APPROVED'
        assert data['review_state'] == 'AUTO_APPROVED'
        assert data['confidence_score'] == 0.90
        assert data['schema_pass'] is True
        assert data['business_rule_pass'] is True
        assert 'reason' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
