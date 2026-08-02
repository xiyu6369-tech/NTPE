"""
Knowledge Review Workflow - States

定義審核狀態的不可變模型與狀態轉換規則。
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet, Mapping

from .errors import InvalidStateTransition


class ReviewState(str, Enum):
    """
    審核狀態枚舉。

    狀態流向：
    PENDING
       |
       +-- confidence high + schema_pass + business_rule_pass
       |          |
       |          v
       |    AUTO_APPROVED
       |
       +-- confidence low OR validation fail
                  |
                  v
           HUMAN_REVIEW_REQUIRED
                  |
          +-------+-------+
          |               |
          v               v
      APPROVED        REJECTED
          |               |
          +-------+-------+
                  |
                  v
            HUMAN_REVIEW_REQUIRED (REVISE)
                  |
                  v
             SUPERSEDED (from APPROVED/AUTO_APPROVED)
    """

    # 初始狀態：待審核
    PENDING = "PENDING"

    # 自動通過：高信心度且通過所有驗證
    AUTO_APPROVED = "AUTO_APPROVED"

    # 需人工審核：低信心度或驗證失敗
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"

    # 人工通過
    APPROVED = "APPROVED"

    # 人工拒絕
    REJECTED = "REJECTED"

    # 已被取代（新版本覆蓋）
    SUPERSEDED = "SUPERSEDED"

    @property
    def is_terminal(self) -> bool:
        """是否為終態（不可再轉換）。"""
        return self in (ReviewState.SUPERSEDED,)

    @property
    def is_active(self) -> bool:
        """是否為作用中狀態（可繼續處理）。"""
        return self in (
            ReviewState.PENDING,
            ReviewState.AUTO_APPROVED,
            ReviewState.HUMAN_REVIEW_REQUIRED,
            ReviewState.APPROVED,
            ReviewState.REJECTED,
        )

    @property
    def requires_human_review(self) -> bool:
        """是否需要人工審核。"""
        return self == ReviewState.HUMAN_REVIEW_REQUIRED


# 合法的狀態轉換映射：current_state -> frozenset(valid_next_states)
STATE_TRANSITIONS: Mapping[ReviewState, FrozenSet[ReviewState]] = {
    ReviewState.PENDING: frozenset({
        ReviewState.AUTO_APPROVED,
        ReviewState.HUMAN_REVIEW_REQUIRED,
        ReviewState.APPROVED,      # 直接通過
        ReviewState.REJECTED,      # 直接拒絕
    }),
    ReviewState.AUTO_APPROVED: frozenset({
        ReviewState.SUPERSEDED,
    }),
    ReviewState.HUMAN_REVIEW_REQUIRED: frozenset({
        ReviewState.APPROVED,
        ReviewState.REJECTED,
        ReviewState.HUMAN_REVIEW_REQUIRED,  # REVISE 保持在 HUMAN_REVIEW_REQUIRED
    }),
    ReviewState.APPROVED: frozenset({
        ReviewState.SUPERSEDED,
        ReviewState.HUMAN_REVIEW_REQUIRED,  # REVISE 回到人工審核
    }),
    ReviewState.REJECTED: frozenset({
        ReviewState.HUMAN_REVIEW_REQUIRED,  # REVISE 重新審核
    }),
    ReviewState.SUPERSEDED: frozenset(),  # 禁止從 SUPERSEDED 轉出
}


def validate_transition(current: ReviewState, target: ReviewState) -> None:
    """
    驗證狀態轉換是否合法。

    Args:
        current: 當前狀態
        target: 目標狀態

    Raises:
        InvalidStateTransition: 如果轉換不合法
    """
    if target not in STATE_TRANSITIONS.get(current, frozenset()):
        raise InvalidStateTransition(current.value, target.value)

    # 額外檢查：禁止的特定轉換
    forbidden = {
        (ReviewState.REJECTED, ReviewState.APPROVED),  # 禁止 REJECTED -> APPROVED
        (ReviewState.SUPERSEDED, ReviewState.APPROVED),
        (ReviewState.SUPERSEDED, ReviewState.HUMAN_REVIEW_REQUIRED),
        (ReviewState.SUPERSEDED, ReviewState.AUTO_APPROVED),
    }
    if (current, target) in forbidden:
        raise InvalidStateTransition(
            current.value, target.value,
            f"禁止的狀態轉換：{current.value} -> {target.value}"
        )


def get_valid_transitions(current: ReviewState) -> FrozenSet[ReviewState]:
    """取得從當前狀態可轉換的目標狀態集合。"""
    return STATE_TRANSITIONS.get(current, frozenset())