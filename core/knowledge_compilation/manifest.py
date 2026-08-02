"""
Knowledge Compilation Engine - Manifest Generator

產生編譯套件的 Manifest，包含：
- package_id, package_version
- schema_versions
- entity_counts
- entity_refs (已排序)
- created_at
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .models import (
    CompilationManifest,
    EntityRef,
    DEFAULT_SCHEMA_VERSIONS,
    KNOWN_ENTITY_TYPES,
)


class ManifestGenerator:
    """
    Manifest 產生器。
    
    從已核准的實體集合生成標準化的 Manifest。
    """
    
    def __init__(
        self,
        package_id: str = "ntpe_knowledge",
        package_version: str = "1.0.0",
        compiler_version: str = "1.0.0",
        default_schema_versions: Dict[str, str] | None = None,
    ) -> None:
        self._package_id = package_id
        self._package_version = package_version
        self._compiler_version = compiler_version
        self._default_schema_versions = default_schema_versions or DEFAULT_SCHEMA_VERSIONS
    
    def generate(
        self,
        entities: Dict[str, List[Dict[str, Any]]],
        created_at: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> CompilationManifest:
        """
        從實體集合生成 Manifest。
        
        Args:
            entities: 實體類型 -> 實體列表的字典
            created_at: 建立時間（ISO 格式），預設為當前 UTC 時間
            metadata: 額外元資料
            
        Returns:
            CompilationManifest 實例
        """
        if created_at is None:
            created_at = datetime.now(timezone.utc).isoformat()
        
        entity_counts = {}
        entity_refs = []
        schema_versions = {}
        
        # 按已知實體類型順序處理（確保決定性）
        for entity_type in KNOWN_ENTITY_TYPES:
            if entity_type not in entities:
                continue
            
            entity_list = entities[entity_type]
            if not entity_list:
                continue
            
            entity_counts[entity_type] = len(entity_list)
            
            # 獲取 schema_version（從第一個實體）
            first_entity = entity_list[0]
            schema_version = first_entity.get("schema_version", self._default_schema_versions.get(entity_type, "1.0"))
            schema_versions[entity_type] = schema_version
            
            # 建立 EntityRef 列表
            for entity in entity_list:
                entity_refs.append(EntityRef(
                    entity_id=entity.get("entity_id", ""),
                    entity_type=entity_type,
                    name=entity.get("name", ""),
                    version=entity.get("version", 1),
                    schema_version=schema_version,
                ))
        
        # 決定性排序：entity_type -> entity_id -> version
        entity_refs.sort(key=lambda r: (r.entity_type, r.entity_id, r.version))
        
        return CompilationManifest(
            package_id=self._package_id,
            package_version=self._package_version,
            schema_versions=schema_versions,
            entity_counts=entity_counts,
            entity_refs=entity_refs,
            created_at=created_at,
            compiler_version=self._compiler_version,
            metadata=metadata or {},
        )
    
    def generate_from_package(self, package_id: str, package_version: str, **kwargs) -> CompilationManifest:
        """使用不同的 package_id/version 生成 Manifest。"""
        original_id = self._package_id
        original_version = self._package_version
        self._package_id = package_id
        self._package_version = package_version
        try:
            return self.generate(**kwargs)
        finally:
            self._package_id = original_id
            self._package_version = original_version


class ManifestValidator:
    """Manifest 驗證器。"""
    
    @staticmethod
    def validate(manifest: CompilationManifest) -> List[str]:
        """
        驗證 Manifest 完整性。
        
        Returns:
            錯誤訊息列表（空列表表示通過）
        """
        errors = []
        
        if not manifest.package_id:
            errors.append("package_id 不能為空")
        
        if not manifest.package_version:
            errors.append("package_version 不能為空")
        
        if not manifest.schema_versions:
            errors.append("schema_versions 不能為空")
        
        if not manifest.entity_counts:
            errors.append("entity_counts 不能為空")
        
        if not manifest.entity_refs:
            errors.append("entity_refs 不能為空")
        
        if not manifest.created_at:
            errors.append("created_at 不能為空")
        
        # 驗證 entity_counts 與 entity_refs 一致性
        ref_counts: Dict[str, int] = {}
        for ref in manifest.entity_refs:
            ref_counts[ref.entity_type] = ref_counts.get(ref.entity_type, 0) + 1
        
        for entity_type, count in manifest.entity_counts.items():
            ref_count = ref_counts.get(entity_type, 0)
            if count != ref_count:
                errors.append(f"實體類型 {entity_type} 的計數不一致：entity_counts={count}, entity_refs={ref_count}")
        
        # 驗證 entity_refs 排序
        for i in range(len(manifest.entity_refs) - 1):
            curr = manifest.entity_refs[i]
            next_ref = manifest.entity_refs[i + 1]
            if (curr.entity_type, curr.entity_id, curr.version) > (next_ref.entity_type, next_ref.entity_id, next_ref.version):
                errors.append("entity_refs 未按正確順序排序")
                break
        
        return errors
    
    @staticmethod
    def assert_valid(manifest: CompilationManifest) -> None:
        """驗證並拋出異常如果無效。"""
        from .errors import ManifestGenerationError
        errors = ManifestValidator.validate(manifest)
        if errors:
            raise ManifestGenerationError("Manifest 驗證失敗", {"errors": errors})