"""
Knowledge Compilation Engine - Checksum Calculator

提供決定性的 SHA256 checksum 計算。

規則：
1. 實體按 entity_type -> entity_id -> version 排序
2. 序列化為 canonical JSON（排序鍵、無空白）
3. 計算 SHA256
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .models import CompilationPackage, CompilationManifest


class ChecksumCalculator:
    """
    決定性 Checksum 計算器。
    
    同樣的輸入永遠產生相同的輸出。
    """
    
    ALGORITHM = "sha256"
    
    def __init__(self, algorithm: str = "sha256") -> None:
        if algorithm != "sha256":
            raise ValueError(f"不支援的演算法：{algorithm}，僅支援 sha256")
        self._algorithm = algorithm
    
    @property
    def algorithm(self) -> str:
        return self._algorithm
    
    def calculate(self, package: CompilationPackage) -> str:
        """
        計算套件的 checksum。
        
        使用實體的 canonical JSON 表示進行雜湊（與編譯時一致）。
        """
        return self.calculate_from_entities(package.entities)
    
    def calculate_from_entities(self, entities: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        從實體字典直接計算 checksum（用於建構過程中）。
        
        Args:
            entities: 實體類型 -> 實體列表的字典
            
        Returns:
            SHA256 雜湊值（十六進制字串）
        """
        # 建立臨時 manifest 結構用於計算
        entity_refs = []
        entity_counts = {}
        schema_versions = {}
        
        for entity_type in sorted(entities.keys()):
            entity_list = entities[entity_type]
            entity_counts[entity_type] = len(entity_list)
            
            # 獲取 schema_version（從第一個實體）
            if entity_list:
                schema_versions[entity_type] = entity_list[0].get("schema_version", "1.0")
            
            # 建立 EntityRef 列表（已排序）
            for entity in entity_list:
                entity_refs.append({
                    "entity_id": entity.get("entity_id", ""),
                    "entity_type": entity_type,
                    "name": entity.get("name", ""),
                    "version": entity.get("version", 1),
                    "schema_version": entity.get("schema_version", "1.0"),
                })
        
        # 排序 entity_refs
        entity_refs.sort(key=lambda r: (r["entity_type"], r["entity_id"], r["version"]))
        
        manifest_data = {
            "package_id": "temp",
            "package_version": "0.0.0",
            "schema_versions": schema_versions,
            "entity_counts": entity_counts,
            "entity_refs": entity_refs,
            "created_at": "1970-01-01T00:00:00+00:00",
            "compiler_version": "1.0.0",
            "metadata": {},
        }
        
        canonical_json = self._to_canonical_json(manifest_data)
        return self._hash(canonical_json)
    
    def _to_canonical_json(self, data: Dict[str, Any]) -> str:
        """
        轉換為 canonical JSON。
        
        規則：
        - 所有鍵按字母順序排序
        - 無空白字元
        - 使用 UTF-8 編碼
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    
    def _hash(self, data: str) -> str:
        """計算字串的 SHA256 雜湊。"""
        hasher = hashlib.new(self._algorithm)
        hasher.update(data.encode("utf-8"))
        return hasher.hexdigest()
    
    @classmethod
    def hash_string(cls, data: str, algorithm: str = "sha256") -> str:
        """便利方法：直接雜湊字串。"""
        hasher = hashlib.new(algorithm)
        hasher.update(data.encode("utf-8"))
        return hasher.hexdigest()
    
    @classmethod
    def hash_bytes(cls, data: bytes, algorithm: str = "sha256") -> str:
        """便利方法：直接雜湊位元組。"""
        hasher = hashlib.new(algorithm)
        hasher.update(data)
        return hasher.hexdigest()


# 全域實例
DEFAULT_CALCULATOR = ChecksumCalculator()