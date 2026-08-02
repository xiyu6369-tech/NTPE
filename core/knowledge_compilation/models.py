"""
Knowledge Compilation Engine - Models

定義編譯套件、實體集合等核心資料模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


def utc_now_iso() -> str:
    """返回穩定的 UTC 時間戳（ISO 格式）。"""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class EntityRef:
    """
    實體引用 - 用於編譯套件中的實體索引。
    
    不包含完整實體資料，僅包含定位所需的最小資訊。
    """
    entity_id: str
    entity_type: str
    name: str
    version: int
    schema_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "version": self.version,
            "schema_version": self.schema_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityRef":
        return cls(
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            name=data["name"],
            version=data["version"],
            schema_version=data["schema_version"],
        )
@dataclass(frozen=True, slots=True)
class CompilationManifest:
    """
    編譯 Manifest - 描述套件內容的元資料。
    
    這是決定性的、可序列化的，用於校驗和運行時載入。
    """
    package_id: str
    package_version: str
    schema_versions: Dict[str, str]
    entity_counts: Dict[str, int]
    entity_refs: List[EntityRef]
    created_at: str
    compiler_version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "package_version": self.package_version,
            "schema_versions": dict(self.schema_versions),
            "entity_counts": dict(self.entity_counts),
            "entity_refs": [ref.to_dict() for ref in self.entity_refs],
            "created_at": self.created_at,
            "compiler_version": self.compiler_version,
            "metadata": dict(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompilationManifest":
        return cls(
            package_id=data["package_id"],
            package_version=data["package_version"],
            schema_versions=dict(data["schema_versions"]),
            entity_counts=dict(data["entity_counts"]),
            entity_refs=[EntityRef.from_dict(r) for r in data["entity_refs"]],
            created_at=data["created_at"],
            compiler_version=data.get("compiler_version", "1.0.0"),
            metadata=dict(data.get("metadata", {})),
        )
    
    def total_entity_count(self) -> int:
        """返回總實體數量。"""
        return sum(self.entity_counts.values())
    
    def get_entity_types(self) -> List[str]:
        """返回包含的實體類型列表（排序）。"""
        return sorted(self.entity_counts.keys())


@dataclass(frozen=True, slots=True)
class CompilationPackage:
    """
    編譯套件 - 不可變、決定性的知識套件。
    
    包含：
    - manifest: 描述套件內容
    - entities: 完整實體資料（按類型分組）
    - checksum: 內容雜湊值
    
    特性：
    - immutable (frozen dataclass)
    - JSON serializable
    - deterministic ordering
    """
    package_id: str
    package_version: str
    schema_versions: Dict[str, str]
    entities: Dict[str, List[Dict[str, Any]]]  # entity_type -> list of entity dicts
    manifest: CompilationManifest
    checksum: str
    created_at: str
    compiler_version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（用於序列化）。"""
        return {
            "package_id": self.package_id,
            "package_version": self.package_version,
            "schema_versions": dict(self.schema_versions),
            "entities": {k: list(v) for k, v in self.entities.items()},
            "manifest": self.manifest.to_dict(),
            "checksum": self.checksum,
            "created_at": self.created_at,
            "compiler_version": self.compiler_version,
            "metadata": dict(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompilationPackage":
        """從字典建立實例。"""
        return cls(
            package_id=data["package_id"],
            package_version=data["package_version"],
            schema_versions=dict(data["schema_versions"]),
            entities={k: list(v) for k, v in data["entities"].items()},
            manifest=CompilationManifest.from_dict(data["manifest"]),
            checksum=data["checksum"],
            created_at=data["created_at"],
            compiler_version=data.get("compiler_version", "1.0.0"),
            metadata=dict(data.get("metadata", {})),
        )
    
    def get_entity_count(self, entity_type: str) -> int:
        """獲取特定類型的實體數量。"""
        return len(self.entities.get(entity_type, []))
    
    def get_all_entities(self) -> List[Dict[str, Any]]:
        """獲取所有實體的扁平列表。"""
        all_entities = []
        for entity_list in self.entities.values():
            all_entities.extend(entity_list)
        return all_entities
    
    def get_entity_types(self) -> List[str]:
        """返回包含的實體類型列表（排序）。"""
        return sorted(self.entities.keys())
    
    def total_entity_count(self) -> int:
        """返回總實體數量。"""
        return sum(len(v) for v in self.entities.values())
    
    def verify_checksum(self, calculator: "ChecksumCalculator") -> bool:
        """驗證套件的 checksum 是否匹配。"""
        # 使用實體計算 checksum（與編譯時一致）
        calculated = calculator.calculate_from_entities(self.entities)
        return calculated == self.checksum


# 核准狀態常數
APPROVED_STATES = frozenset({"APPROVED", "AUTO_APPROVED"})
REJECTED_STATES = frozenset({"REJECTED", "SUPERSEDED"})
PENDING_STATES = frozenset({"PENDING", "HUMAN_REVIEW_REQUIRED"})

# 所有已知實體類型
KNOWN_ENTITY_TYPES = (
    "character",
    "glossary",
    "scene",
    "narrative",
    "style",
)

# Schema 版本映射（從 schema 檔案讀取）
DEFAULT_SCHEMA_VERSIONS = {
    "character": "1.0",
    "glossary": "1.0",
    "scene": "1.0",
    "narrative": "1.0",
    "style": "1.0",
}