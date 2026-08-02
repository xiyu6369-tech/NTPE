"""
Audit Log Tests

測試審計日誌功能。
"""

import pytest
from uuid import uuid4
from datetime import datetime

from core.knowledge_review.audit_log import AuditLog, ReviewAuditEntry


class TestAuditLog:
    """測試審計日誌。"""

    def setup_method(self):
        """每個測試前的設置。"""
        self.audit_log = AuditLog()

    def test_log_entry(self):
        """測試記錄審計條目。"""
        review_id = uuid4()
        entry = self.audit_log.log(
            review_id=review_id,
            previous_state="PENDING",
            new_state="APPROVED",
            action="APPROVE",
            reason="Test passed",
            actor="test_user",
        )

        assert entry.review_id == review_id
        assert entry.previous_state == "PENDING"
        assert entry.new_state == "APPROVED"
        assert entry.action == "APPROVE"
        assert entry.reason == "Test passed"
        assert entry.actor == "test_user"
        assert isinstance(entry.timestamp, datetime)
        assert len(self.audit_log) == 1

    def test_get_history(self):
        """測試取得審核項目歷史記錄。"""
        review_id = uuid4()

        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="HUMAN_REVIEW_REQUIRED", action="SUBMIT", reason="Submit review")
        self.audit_log.log(review_id=review_id, previous_state="HUMAN_REVIEW_REQUIRED", new_state="APPROVED", action="APPROVE", reason="Approved")

        history = self.audit_log.get_history(review_id)
        assert len(history) == 2
        assert history[0].action == "SUBMIT"
        assert history[1].action == "APPROVE"

    def test_get_history_empty(self):
        """測試不存在的審核項目歷史為空。"""
        history = self.audit_log.get_history(uuid4())
        assert history == []

    def test_get_all_entries(self):
        """測試取得所有條目。"""
        review_id1 = uuid4()
        review_id2 = uuid4()

        self.audit_log.log(review_id=review_id1, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")
        self.audit_log.log(review_id=review_id2, previous_state="PENDING", new_state="REJECTED", action="REJECT", reason="Rejected")

        all_entries = self.audit_log.get_all_entries()
        assert len(all_entries) == 2

    def test_get_entries_by_actor(self):
        """測試按執行者過濾。"""
        review_id = uuid4()

        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved", actor="user1")
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="REJECTED", action="REJECT", reason="Rejected", actor="user2")

        user1_entries = self.audit_log.get_entries_by_actor("user1")
        user2_entries = self.audit_log.get_entries_by_actor("user2")

        assert len(user1_entries) == 1
        assert user1_entries[0].actor == "user1"
        assert len(user2_entries) == 1
        assert user2_entries[0].actor == "user2"

    def test_get_entries_by_action(self):
        """測試按動作過濾。"""
        review_id = uuid4()

        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="REJECTED", action="REJECT", reason="Rejected")

        approve_entries = self.audit_log.get_entries_by_action("APPROVE")
        reject_entries = self.audit_log.get_entries_by_action("REJECT")

        assert len(approve_entries) == 1
        assert approve_entries[0].action == "APPROVE"
        assert len(reject_entries) == 1
        assert reject_entries[0].action == "REJECT"

    def test_export_json(self):
        """測試匯出 JSON。"""
        review_id = uuid4()
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")

        json_data = self.audit_log.export_json()
        assert len(json_data) == 1
        assert json_data[0]["review_id"] == str(review_id)
        assert json_data[0]["action"] == "APPROVE"
        assert "timestamp" in json_data[0]

    def test_clear(self):
        """測試清空日誌。"""
        review_id = uuid4()
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")

        assert len(self.audit_log) == 1

        self.audit_log.clear()

        assert len(self.audit_log) == 0
        assert self.audit_log.get_history(review_id) == []

    def test_iteration(self):
        """測試迭代器。"""
        review_id = uuid4()
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")
        self.audit_log.log(review_id=review_id, previous_state="PENDING", new_state="REJECTED", action="REJECT", reason="Rejected")

        entries = list(self.audit_log)
        assert len(entries) == 2

    def test_bool_always_true(self):
        """測試 AuditLog 實例總是為 True（即使為空）。"""
        empty_log = AuditLog()
        assert bool(empty_log) is True

        log_with_entries = AuditLog()
        log_with_entries.log(review_id=uuid4(), previous_state="PENDING", new_state="APPROVED", action="APPROVE", reason="Approved")
        assert bool(log_with_entries) is True

    def test_entry_to_dict(self):
        """測試條目序列化。"""
        review_id = uuid4()
        entry = ReviewAuditEntry(
            review_id=review_id,
            previous_state="PENDING",
            new_state="APPROVED",
            action="APPROVE",
            reason="Test",
            actor="test",
        )

        data = entry.to_dict()
        assert data["review_id"] == str(review_id)
        assert data["previous_state"] == "PENDING"
        assert data["new_state"] == "APPROVED"
        assert data["action"] == "APPROVE"
        assert data["reason"] == "Test"
        assert data["actor"] == "test"
        assert "timestamp" in data
        assert "entry_id" in data

    def test_entry_from_dict(self):
        """測試從字典建立條目。"""
        review_id = uuid4()
        entry_id = uuid4()
        timestamp = datetime.now()

        data = {
            "entry_id": str(entry_id),
            "review_id": str(review_id),
            "previous_state": "PENDING",
            "new_state": "APPROVED",
            "action": "APPROVE",
            "reason": "Test",
            "timestamp": timestamp.isoformat(),
            "actor": "test",
        }

        entry = ReviewAuditEntry.from_dict(data)
        assert entry.entry_id == entry_id
        assert entry.review_id == review_id
        assert entry.previous_state == "PENDING"
        assert entry.new_state == "APPROVED"
        assert entry.action == "APPROVE"
        assert entry.reason == "Test"
        assert entry.actor == "test"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])