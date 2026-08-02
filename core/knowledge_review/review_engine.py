"""
Knowledge Review Workflow - Review Engine

審核引擎：處理審核決策（APPROVE, REJECT, REVISE）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .models import ReviewItem
from .states import ReviewState, validate_transition
from .errors import InvalidReviewStateError
from .audit_log import AuditLog


class ReviewAction(str, Enum):
    """審核動作。"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVISE = "REVISE"


class ReviewDecision(str, Enum):
    """審核決策結果。"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISED = "REVISED"
    NO_CHANGE = "NO_CHANGE"


@dataclass(frozen=True, slots=True)
class ReviewResult:
    """審核執行結果。"""
    decision: ReviewDecision
    review_item: ReviewItem
    previous_state: str
    new_state: str
    message: str


class ReviewEngine:
    """
    審核引擎。

    提供：
    - submit_review(): 提交審核決策
    - 支援 APPROVE, REJECT, REVISE 動作
    - 自動記錄審計日誌
    """

    def __init__(self, audit_log: Optional[AuditLog] = None) -> None:
        self._audit_log = audit_log

    def submit_review(
        self,
        review_item: ReviewItem,
        action: ReviewAction,
        reason: str,
        actor: str = "system",
    ) -> ReviewResult:
        current_state = review_item.review_state

        if action == ReviewAction.APPROVE:
            if current_state in ("HUMAN_REVIEW_REQUIRED", "PENDING"):
                target_state = "APPROVED"
            else:
                raise InvalidReviewStateError(
                    current_state, "APPROVED",
                    f"無法從 {current_state} 通過 APPROVE 動作轉為 APPROVED"
                )

        elif action == ReviewAction.REJECT:
            if current_state in ("HUMAN_REVIEW_REQUIRED", "PENDING"):
                target_state = "REJECTED"
            else:
                raise InvalidReviewStateError(
                    current_state, "REJECTED",
                    f"無法從 {current_state} 通過 REJECT 動作轉為 REJECTED"
                )

        elif action == ReviewAction.REVISE:
            if current_state in ("HUMAN_REVIEW_REQUIRED", "APPROVED", "REJECTED"):
                target_state = "HUMAN_REVIEW_REQUIRED"
            else:
                raise InvalidReviewStateError(
                    current_state, "HUMAN_REVIEW_REQUIRED",
                    f"無法從 {current_state} 通過 REVISE 動作轉為 HUMAN_REVIEW_REQUIRED"
                )

        else:
            raise ValueError(f"未知的審核動作：{action}")

        try:
            validate_transition(ReviewState(current_state), ReviewState(target_state))
        except ValueError:
            pass

        new_item = review_item.with_state(target_state)

        if self._audit_log:
            self._audit_log.log(
                review_id=review_item.review_id,
                previous_state=current_state,
                new_state=target_state,
                action=action.value,
                reason=reason,
                actor=actor,
            )

        if action == ReviewAction.APPROVE:
            decision = ReviewDecision.APPROVED
            message = f"審核通過：{reason}"
        elif action == ReviewAction.REJECT:
            decision = ReviewDecision.REJECTED
            message = f"審核拒絕：{reason}"
        else:
            decision = ReviewDecision.REVISED
            message = f"要求修訂：{reason}"

        return ReviewResult(
            decision=decision,
            review_item=new_item,
            previous_state=current_state,
            new_state=target_state,
            message=message,
        )

    def auto_approve(
        self,
        review_item: ReviewItem,
        reason: str = "自動通過：信心度達標且驗證通過",
        actor: str = "confidence_gate",
    ) -> ReviewResult:
        current_state = review_item.review_state

        if current_state != "PENDING":
            raise InvalidReviewStateError(
                current_state, "AUTO_APPROVED",
                f"只有 PENDING 狀態可以自動通過，當前狀態：{current_state}"
            )

        new_item = review_item.with_state("AUTO_APPROVED")

        if self._audit_log:
            self._audit_log.log(
                review_id=review_item.review_id,
                previous_state=current_state,
                new_state="AUTO_APPROVED",
                action="AUTO_APPROVE",
                reason=reason,
                actor=actor,
            )

        return ReviewResult(
            decision=ReviewDecision.APPROVED,
            review_item=new_item,
            previous_state=current_state,
            new_state="AUTO_APPROVED",
            message=reason,
        )

    def supersede(
        self,
        review_item: ReviewItem,
        reason: str = "已被新版本取代",
        actor: str = "system",
    ) -> ReviewResult:
        current_state = review_item.review_state

        if current_state not in ("APPROVED", "AUTO_APPROVED"):
            raise InvalidReviewStateError(
                current_state, "SUPERSEDED",
                f"只有 APPROVED 或 AUTO_APPROVED 可以轉為 SUPERSEDED，當前狀態：{current_state}"
            )

        new_item = review_item.with_state("SUPERSEDED")

        if self._audit_log:
            self._audit_log.log(
                review_id=review_item.review_id,
                previous_state=current_state,
                new_state="SUPERSEDED",
                action="SUPERSEDE",
                reason=reason,
                actor=actor,
            )

        return ReviewResult(
            decision=ReviewDecision.NO_CHANGE,
            review_item=new_item,
            previous_state=current_state,
            new_state="SUPERSEDED",
            message=reason,
        )