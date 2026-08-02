"""
Knowledge Review Workflow - Audit Log

審計日誌：記錄審核狀態變更歷史，提供不可變的審計追蹤。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ReviewAuditEntry:
    """
    審計日誌條目 - 不可變記錄。

    內容：
    {
     "review_id": "",
     "previous_state": "",
     "new_state": "",
     "action": "",
     "reason": "",
     "timestamp": "",
     "actor": ""
    }
    """

    # 唯一條目 ID
    entry_id: UUID = field(default_factory=uuid4)

    # 關聯的審核項目 ID
    review_id: UUID = field(default_factory=uuid4)

    # 變更前狀態
    previous_state: str = ""

    # 變更後狀態
    new_state: str = ""

    # 執行的動作
    action: str = ""

    # 變更理由
    reason: str = ""

    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)

    # 執行者
    actor: str = "system"

    def to_dict(self) -> dict:
        """轉換為字典（用於序列化）。"""
        return {
            "entry_id": str(self.entry_id),
            "review_id": str(self.review_id),
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "action": self.action,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReviewAuditEntry:
        """從字典建立實例。"""
        return cls(
            entry_id=UUID(data["entry_id"]),
            review_id=UUID(data["review_id"]),
            previous_state=data["previous_state"],
            new_state=data["new_state"],
            action=data["action"],
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor=data.get("actor", "system"),
        )

    def __str__(self) -> str:
        return (
            f"[{self.timestamp.isoformat()}] {self.actor}: "
            f"{self.previous_state} -> {self.new_state} "
            f"({self.action}) - {self.reason}"
        )


class AuditLog:
    """
    審計日誌管理器。

    用途：
    - 可追蹤知識變更
    - 支援版本演進
    - 避免不可逆修改
    """

    def __init__(self) -> None:
        self._entries: list[ReviewAuditEntry] = []
        self._by_review_id: dict[UUID, list[ReviewAuditEntry]] = {}

    def log(
        self,
        review_id: UUID,
        previous_state: str,
        new_state: str,
        action: str,
        reason: str,
        actor: str = "system",
    ) -> ReviewAuditEntry:
        """
        記錄審計條目。

        Args:
            review_id: 審核項目 ID
            previous_state: 變更前狀態
            new_state: 變更後狀態
            action: 執行動作
            reason: 理由
            actor: 執行者

        Returns:
            建立的審計條目
        """
        entry = ReviewAuditEntry(
            review_id=review_id,
            previous_state=previous_state,
            new_state=new_state,
            action=action,
            reason=reason,
            actor=actor,
        )

        self._entries.append(entry)

        if review_id not in self._by_review_id:
            self._by_review_id[review_id] = []
        self._by_review_id[review_id].append(entry)

        return entry

    def get_history(self, review_id: UUID) -> list[ReviewAuditEntry]:
        """
        取得指定審核項目的完整歷史記錄。

        Args:
            review_id: 審核項目 ID

        Returns:
            該項目的所有審計條目（按時間排序）
        """
        return self._by_review_id.get(review_id, []).copy()

    def get_all_entries(self) -> list[ReviewAuditEntry]:
        """取得所有審計條目（按時間排序）。"""
        return self._entries.copy()

    def get_entries_by_actor(self, actor: str) -> list[ReviewAuditEntry]:
        """取得指定執行者的所有操作記錄。"""
        return [e for e in self._entries if e.actor == actor]

    def get_entries_by_action(self, action: str) -> list[ReviewAuditEntry]:
        """取得指定動作的所有記錄。"""
        return [e for e in self._entries if e.action == action]

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        """Always return True for AuditLog instances to allow truthiness checks."""
        return True

    def __iter__(self):
        return iter(self._entries)

    def export_json(self) -> list[dict]:
        """匯出為 JSON 可序列化格式。"""
        return [e.to_dict() for e in self._entries]

    def clear(self) -> None:
        """清空日誌（僅供測試使用）。"""
        self._entries.clear()
        self._by_review_id.clear()