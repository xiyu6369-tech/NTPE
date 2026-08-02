"""
Knowledge Review Workflow - Models

定義審核項目與相關資料模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class EntityType(str, Enum):
    """實體類型。"""
    CHARACTER = "character"
    GLOSSARY = "glossary"
    SCENE = "scene"
    NARRATIVE = "narrative"
    STYLE = "style"


class ValidationResult(str, Enum):
    """驗證結果。"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """
    審核項目 - 不可變資料模型。

    代表一個待審核的知識實體（角色、術語、場景、敘事、風格）。
    """

    # 唯一識別碼
    review_id: UUID = field(default_factory=uuid4)

    # 實體類型
    entity_type: EntityType = EntityType.CHARACTER

    # 實體 ID（關聯到原始知識庫中的實體）
    entity_id: UUID = field(default_factory=uuid4)

    # 來源版本號
    source_version: str = ""

    # 驗證結果
    validation_result: ValidationResult = ValidationResult.PASS

    # 信心度分數 (0.0 - 1.0)
    confidence_score: float = 0.0

    # 當前審核狀態
    review_state: str = "PENDING"  # 使用字串以便序列化

    # 建立時間
    created_at: datetime = field(default_factory=datetime.now)

    # 更新時間
    updated_at: datetime = field(default_factory=datetime.now)

    # 額外元資料（可選）
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """驗證欄位值。"""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"confidence_score 必須在 0.0 到 1.0 之間，收到：{self.confidence_score}")

        if self.review_state not in {
            "PENDING", "AUTO_APPROVED", "HUMAN_REVIEW_REQUIRED",
            "APPROVED", "REJECTED", "SUPERSEDED"
        }:
            raise ValueError(f"無效的 review_state：{self.review_state}")

    def with_state(self, new_state: str) -> ReviewItem:
        """
        回傳新的 ReviewItem 實例，狀態更新為 new_state。

        因為 ReviewItem 是 frozen dataclass，需建立新實例來更新狀態。
        """
        return ReviewItem(
            review_id=self.review_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            source_version=self.source_version,
            validation_result=self.validation_result,
            confidence_score=self.confidence_score,
            review_state=new_state,
            created_at=self.created_at,
            updated_at=datetime.now(),
            metadata=self.metadata.copy(),
        )

    def with_confidence(self, new_confidence: float) -> ReviewItem:
        """回傳更新信心度的新實例。"""
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError(f"confidence_score 必須在 0.0 到 1.0 之間，收到：{new_confidence}")
        return ReviewItem(
            review_id=self.review_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            source_version=self.source_version,
            validation_result=self.validation_result,
            confidence_score=new_confidence,
            review_state=self.review_state,
            created_at=self.created_at,
            updated_at=datetime.now(),
            metadata=self.metadata.copy(),
        )

    def with_validation_result(self, result: ValidationResult) -> ReviewItem:
        """回傳更新驗證結果的新實例。"""
        return ReviewItem(
            review_id=self.review_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            source_version=self.source_version,
            validation_result=result,
            confidence_score=self.confidence_score,
            review_state=self.review_state,
            created_at=self.created_at,
            updated_at=datetime.now(),
            metadata=self.metadata.copy(),
        )

    def to_dict(self) -> dict:
        """轉換為字典（用於序列化）。"""
        return {
            "review_id": str(self.review_id),
            "entity_type": self.entity_type.value,
            "entity_id": str(self.entity_id),
            "source_version": self.source_version,
            "validation_result": self.validation_result.value,
            "confidence_score": self.confidence_score,
            "review_state": self.review_state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReviewItem:
        """從字典建立實例。"""
        return cls(
            review_id=UUID(data["review_id"]),
            entity_type=EntityType(data["entity_type"]),
            entity_id=UUID(data["entity_id"]),
            source_version=data.get("source_version", ""),
            validation_result=ValidationResult(data.get("validation_result", "pass")),
            confidence_score=data.get("confidence_score", 0.0),
            review_state=data.get("review_state", "PENDING"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )