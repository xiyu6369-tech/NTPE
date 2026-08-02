"""
Knowledge Review Workflow - Confidence Gate

信心度閘控：根據信心度、Schema 驗證、業務規則驗證結果，
決定審核項目是自動通過還是需要人工審核。

規則來源：RM-5.7.2A Confidence Rules
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ReviewItem, ValidationResult
from .errors import InvalidConfidenceScoreError


class ConfidenceGateResult(str, Enum):
    """信心度閘控結果。"""
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class ConfidenceGateDecision:
    """信心度閘控決策結果。"""

    result: ConfidenceGateResult
    review_state: str
    reason: str
    confidence_score: float
    schema_pass: bool
    business_rule_pass: bool

    def to_dict(self) -> dict:
        return {
            "result": self.result.value,
            "review_state": self.review_state,
            "reason": self.reason,
            "confidence_score": self.confidence_score,
            "schema_pass": self.schema_pass,
            "business_rule_pass": self.business_rule_pass,
        }


class ConfidenceGate:
    """
    信心度閘控器。

    判斷規則：
    - confidence >= 0.85
    - AND schema_pass == True
    - AND business_rule_pass == True
    => AUTO_APPROVED

    否則 => HUMAN_REVIEW_REQUIRED
    """

    # 自動通過的最低信心度門檻
    AUTO_APPROVE_THRESHOLD: float = 0.85

    def __init__(
        self,
        auto_approve_threshold: float = 0.85,
    ) -> None:
        """
        初始化信心度閘控器。

        Args:
            auto_approve_threshold: 自動通過的信心度門檻 (0.0 - 1.0)
        """
        if not 0.0 <= auto_approve_threshold <= 1.0:
            raise InvalidConfidenceScoreError(auto_approve_threshold)
        self._threshold = auto_approve_threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def evaluate(
        self,
        confidence_score: float,
        schema_pass: bool,
        business_rule_pass: bool,
    ) -> ConfidenceGateDecision:
        """
        評估信心度閘控。

        Args:
            confidence_score: 信心度分數 (0.0 - 1.0)
            schema_pass: Schema 驗證是否通過
            business_rule_pass: 業務規則驗證是否通過

        Returns:
            ConfidenceGateDecision: 閘控決策結果
        """
        if not 0.0 <= confidence_score <= 1.0:
            raise InvalidConfidenceScoreError(confidence_score)

        # 核心判斷邏輯
        all_checks_pass = (
            confidence_score >= self._threshold
            and schema_pass
            and business_rule_pass
        )

        if all_checks_pass:
            return ConfidenceGateDecision(
                result=ConfidenceGateResult.AUTO_APPROVED,
                review_state="AUTO_APPROVED",
                reason=(
                    f"信心度 {confidence_score:.2f} >= {self._threshold:.2f} "
                    f"且 Schema 驗證通過且業務規則驗證通過"
                ),
                confidence_score=confidence_score,
                schema_pass=schema_pass,
                business_rule_pass=business_rule_pass,
            )
        else:
            reasons = []
            if confidence_score < self._threshold:
                reasons.append(
                    f"信心度 {confidence_score:.2f} < {self._threshold:.2f}"
                )
            if not schema_pass:
                reasons.append("Schema 驗證失敗")
            if not business_rule_pass:
                reasons.append("業務規則驗證失敗")

            return ConfidenceGateDecision(
                result=ConfidenceGateResult.HUMAN_REVIEW_REQUIRED,
                review_state="HUMAN_REVIEW_REQUIRED",
                reason="; ".join(reasons),
                confidence_score=confidence_score,
                schema_pass=schema_pass,
                business_rule_pass=business_rule_pass,
            )

    def evaluate_item(self, item: ReviewItem) -> ConfidenceGateDecision:
        """
        直接評估 ReviewItem。

        從 ReviewItem 提取必要資訊進行評估。
        """
        # 從 metadata 讀取 schema_pass 和 business_rule_pass
        # 如果不存在，預設為 True（向後相容）
        schema_pass = item.metadata.get("schema_pass", True)
        business_rule_pass = item.metadata.get("business_rule_pass", True)

        return self.evaluate(
            confidence_score=item.confidence_score,
            schema_pass=schema_pass,
            business_rule_pass=business_rule_pass,
        )