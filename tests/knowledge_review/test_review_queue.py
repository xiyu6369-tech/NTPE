"""
Review Queue Tests

測試審核隊列功能。
"""

import pytest
from uuid import uuid4

from core.knowledge_review.review_queue import (
    ReviewQueue,
    Priority,
    QueueItem,
)
from core.knowledge_review.models import ReviewItem, EntityType, ValidationResult
from core.knowledge_review.errors import DuplicateReviewItemError


class TestReviewQueue:
    """測試審核隊列。"""

    def setup_method(self):
        """每個測試前的設置。"""
        self.queue = ReviewQueue()

    def create_item(
        self,
        entity_type=EntityType.CHARACTER,
        confidence=0.90,
        validation=ValidationResult.PASS,
        metadata=None,
    ):
        """建立測試用的 ReviewItem。"""
        return ReviewItem(
            entity_type=entity_type,
            entity_id=uuid4(),
            confidence_score=confidence,
            validation_result=validation,
            metadata=metadata or {},
        )

    def test_enqueue(self):
        """測試加入隊列。"""
        item = self.create_item()
        self.queue.enqueue(item)
        assert len(self.queue) == 1
        assert item.review_id in self.queue

    def test_enqueue_duplicate_raises(self):
        """測試重複加入拋出異常。"""
        item = self.create_item()
        self.queue.enqueue(item)
        with pytest.raises(DuplicateReviewItemError):
            self.queue.enqueue(item)

    def test_dequeue(self):
        """測試取出隊列項目。"""
        item = self.create_item(confidence=0.80)
        self.queue.enqueue(item)

        dequeued = self.queue.dequeue()
        assert dequeued is not None
        assert dequeued.review_id == item.review_id
        assert len(self.queue) == 0

    def test_dequeue_empty_returns_none(self):
        """測試空隊列取出回傳 None。"""
        result = self.queue.dequeue()
        assert result is None

    def test_peek(self):
        """測試查看隊列首項（不移除）。"""
        item = self.create_item(confidence=0.80)
        self.queue.enqueue(item)

        peeked = self.queue.peek()
        assert peeked is not None
        assert peeked.review_id == item.review_id
        assert len(self.queue) == 1

    def test_priority_ordering(self):
        """測試優先級排序：VALIDATION_FAILURE > LOW_CONFIDENCE > DUPLICATE_CONFLICT > NORMAL_REVIEW。"""
        normal = self.create_item(confidence=0.90, validation=ValidationResult.PASS)
        low_conf = self.create_item(confidence=0.70, validation=ValidationResult.PASS)
        validation_fail = self.create_item(confidence=0.90, validation=ValidationResult.FAIL)
        duplicate = self.create_item(confidence=0.90, validation=ValidationResult.PASS, metadata={"duplicate_conflict": True})

        self.queue.enqueue(normal)
        self.queue.enqueue(low_conf)
        self.queue.enqueue(validation_fail)
        self.queue.enqueue(duplicate)

        first = self.queue.dequeue()
        assert first.review_id == validation_fail.review_id

        second = self.queue.dequeue()
        assert second.review_id == low_conf.review_id

        third = self.queue.dequeue()
        assert third.review_id == duplicate.review_id

        fourth = self.queue.dequeue()
        assert fourth.review_id == normal.review_id

    def test_get_pending_no_filter(self):
        """測試取得所有待審項目。"""
        item1 = self.create_item(confidence=0.80)
        item2 = self.create_item(confidence=0.70)
        self.queue.enqueue(item1)
        self.queue.enqueue(item2)

        pending = self.queue.get_pending()
        assert len(pending) == 2

    def test_get_pending_state_filter(self):
        """測試按狀態過濾。"""
        item1 = self.create_item(confidence=0.80)
        item2 = self.create_item(confidence=0.70)
        item2 = item2.with_state("HUMAN_REVIEW_REQUIRED")
        self.queue.enqueue(item1)
        self.queue.enqueue(item2)

        pending = self.queue.get_pending(state_filter="PENDING")
        assert len(pending) == 1
        assert pending[0].review_id == item1.review_id

    def test_get_pending_entity_type_filter(self):
        """測試按實體類型過濾。"""
        item1 = self.create_item(entity_type=EntityType.CHARACTER)
        item2 = self.create_item(entity_type=EntityType.GLOSSARY)
        self.queue.enqueue(item1)
        self.queue.enqueue(item2)

        pending = self.queue.get_pending(entity_type_filter="character")
        assert len(pending) == 1
        assert pending[0].entity_type == EntityType.CHARACTER

    def test_get_pending_limit(self):
        """測試限制回傳數量。"""
        for i in range(5):
            item = self.create_item(confidence=0.70 + i * 0.05)
            self.queue.enqueue(item)

        pending = self.queue.get_pending(limit=3)
        assert len(pending) == 3

    def test_remove(self):
        """測試移除項目。"""
        item = self.create_item()
        self.queue.enqueue(item)

        removed = self.queue.remove(item.review_id)
        assert removed is True
        assert len(self.queue) == 0

    def test_remove_nonexistent(self):
        """測試移除不存在的項目。"""
        removed = self.queue.remove(uuid4())
        assert removed is False

    def test_contains(self):
        """測試包含檢查。"""
        item = self.create_item()
        self.queue.enqueue(item)

        assert item.review_id in self.queue
        assert uuid4() not in self.queue

    def test_get_stats(self):
        """測試統計資訊。"""
        item1 = self.create_item(entity_type=EntityType.CHARACTER, confidence=0.90)
        item2 = self.create_item(entity_type=EntityType.GLOSSARY, confidence=0.70)
        item3 = self.create_item(entity_type=EntityType.CHARACTER, confidence=0.80, validation=ValidationResult.FAIL)
        self.queue.enqueue(item1)
        self.queue.enqueue(item2)
        self.queue.enqueue(item3)

        stats = self.queue.get_stats()
        assert stats["total"] == 3
        assert stats["by_priority"]["VALIDATION_FAILURE"] == 1
        assert stats["by_priority"]["LOW_CONFIDENCE"] == 1
        assert stats["by_priority"]["NORMAL_REVIEW"] == 1
        assert stats["by_entity_type"]["character"] == 2
        assert stats["by_entity_type"]["glossary"] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
