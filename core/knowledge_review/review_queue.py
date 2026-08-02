"""
Knowledge Review Workflow - Review Queue

審核隊列：管理待審核項目的佇列，支援優先級排序。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
from uuid import UUID

from .models import ReviewItem, ValidationResult


class Priority(IntEnum):
    """
    優先級枚舉（數值越小優先級越高）。

    排序規則：
    1. validation failure (最高優先級)
    2. low confidence
    3. duplicate conflict
    4. normal review (最低優先級)
    """
    VALIDATION_FAILURE = 1      # 驗證失敗
    LOW_CONFIDENCE = 2          # 低信心度
    DUPLICATE_CONFLICT = 3      # 重複衝突
    NORMAL_REVIEW = 4           # 一般審核


@dataclass(frozen=True, slots=True)
class QueueItem:
    """隊列項目（包含優先級資訊）。"""
    review_item: ReviewItem
    priority: Priority
    enqueued_at: float  # timestamp

    def __lt__(self, other: QueueItem) -> bool:
        """支援排序：優先級優先，然後按入隊時間。"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.enqueued_at < other.enqueued_at


class ReviewQueue:
    """
    審核隊列。

    功能：
    - enqueue(review_item): 加入隊列
    - get_pending(): 取得待審核項目（按優先級排序）
    - 支援按狀態過濾
    """

    def __init__(self) -> None:
        self._queue: list[QueueItem] = []
        self._item_index: dict[UUID, int] = {}  # review_id -> index in _queue
        self._timestamp = 0.0

    def _next_timestamp(self) -> float:
        self._timestamp += 1.0
        return self._timestamp

    def _calculate_priority(self, item: ReviewItem) -> Priority:
        """根據項目屬性計算優先級。"""
        # 1. 驗證失敗 - 最高優先級
        if item.validation_result == ValidationResult.FAIL:
            return Priority.VALIDATION_FAILURE

        # 2. 低信心度
        if item.confidence_score < 0.85:
            return Priority.LOW_CONFIDENCE

        # 3. 重複衝突（從 metadata 判斷）
        if item.metadata.get("duplicate_conflict", False):
            return Priority.DUPLICATE_CONFLICT

        # 4. 一般審核
        return Priority.NORMAL_REVIEW

    def enqueue(self, review_item: ReviewItem) -> None:
        """
        將審核項目加入隊列。

        Args:
            review_item: 要加入的審核項目

        Raises:
            DuplicateReviewItemError: 如果項目已存在
        """
        from .errors import DuplicateReviewItemError

        if review_item.review_id in self._item_index:
            raise DuplicateReviewItemError(str(review_item.review_id))

        priority = self._calculate_priority(review_item)
        queue_item = QueueItem(
            review_item=review_item,
            priority=priority,
            enqueued_at=self._next_timestamp(),
        )

        # 維持排序順序插入
        import bisect
        bisect.insort(self._queue, queue_item)
        self._item_index[review_item.review_id] = len(self._queue) - 1

    def dequeue(self) -> Optional[ReviewItem]:
        """
        取出並移除最高優先級的項目。

        Returns:
            ReviewItem 或 None（如果隊列為空）
        """
        if not self._queue:
            return None

        queue_item = self._queue.pop(0)
        del self._item_index[queue_item.review_item.review_id]

        # 重建索引
        self._rebuild_index()

        return queue_item.review_item

    def peek(self) -> Optional[ReviewItem]:
        """
        查看最高優先級的項目（不移除）。

        Returns:
            ReviewItem 或 None
        """
        if not self._queue:
            return None
        return self._queue[0].review_item

    def get_pending(
        self,
        state_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[ReviewItem]:
        """
        取得待審核項目列表（按優先級排序）。

        Args:
            state_filter: 可選，按狀態過濾
            entity_type_filter: 可選，按實體類型過濾
            limit: 可選，限制回傳數量

        Returns:
            符合條件的審核項目列表
        """
        results = []

        for queue_item in self._queue:
            item = queue_item.review_item

            if state_filter and item.review_state != state_filter:
                continue
            if entity_type_filter and item.entity_type.value != entity_type_filter:
                continue

            results.append(item)

            if limit and len(results) >= limit:
                break

        return results

    def remove(self, review_id: UUID) -> bool:
        """
        從隊列移除指定項目。

        Args:
            review_id: 要移除的項目 ID

        Returns:
            是否成功移除
        """
        if review_id not in self._item_index:
            return False

        index = self._item_index[review_id]
        self._queue.pop(index)
        self._rebuild_index()
        return True

    def _rebuild_index(self) -> None:
        """重建索引。"""
        self._item_index = {
            qi.review_item.review_id: i
            for i, qi in enumerate(self._queue)
        }

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)

    def __contains__(self, review_id: UUID) -> bool:
        return review_id in self._item_index

    def get_stats(self) -> dict:
        """取得隊列統計資訊。"""
        stats = {
            "total": len(self._queue),
            "by_priority": {},
            "by_state": {},
            "by_entity_type": {},
        }

        for qi in self._queue:
            item = qi.review_item

            # by priority
            p_name = qi.priority.name
            stats["by_priority"][p_name] = stats["by_priority"].get(p_name, 0) + 1

            # by state
            stats["by_state"][item.review_state] = stats["by_state"].get(item.review_state, 0) + 1

            # by entity type
            et_name = item.entity_type.value
            stats["by_entity_type"][et_name] = stats["by_entity_type"].get(et_name, 0) + 1

        return stats