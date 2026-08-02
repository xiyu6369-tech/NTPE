"""
Knowledge Compilation Engine - Compiler

核心編譯流程：
1. load approved entities
2. validate state
3. normalize ordering
4. merge entities
5. generate manifest
6. calculate checksum
7. output package
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import (
    CompilationPackage,
    CompilationManifest,
    EntityRef,
    APPROVED_STATES,
    KNOWN_ENTITY_TYPES,
    DEFAULT_SCHEMA_VERSIONS,
    utc_now_iso,
)
from .manifest import ManifestGenerator, ManifestValidator
from .checksum import ChecksumCalculator, DEFAULT_CALCULATOR
from .package_builder import PackageBuilder
from .errors import (
    CompilationError,
    InvalidEntityStateError,
    EmptyPackageError,
    ManifestGenerationError,
    ChecksumCalculationError,
    PackageBuildError,
    RuntimeInvocationError,
)


# 實體載入器介面
EntityLoader = Callable[[], Dict[str, List[Dict[str, Any]]]]


@dataclass(frozen=True, slots=True)
class CompilationConfig:
    """編譯器配置。"""
    package_id: str = "ntpe_knowledge"
    package_version: str = "1.0.0"
    compiler_version: str = "1.0.0"
    allowed_states: frozenset = APPROVED_STATES
    output_root: str = "artifacts/knowledge_packages"
    version_dir: str = "v1"
    strict_mode: bool = True  # 嚴格模式：遇到無效狀態拋出異常
    include_rejected: bool = False  # 是否包含被拒絕的實體（用於審計）


@dataclass(slots=True)
class CompilationStats:
    """編譯統計資訊。"""
    total_input_entities: int = 0
    approved_entities: int = 0
    rejected_entities: int = 0
    skipped_entities: int = 0
    entity_types_processed: int = 0
    compilation_time_ms: float = 0.0
    output_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_entities": self.total_input_entities,
            "approved_entities": self.approved_entities,
            "rejected_entities": self.rejected_entities,
            "skipped_entities": self.skipped_entities,
            "entity_types_processed": self.entity_types_processed,
            "compilation_time_ms": self.compilation_time_ms,
            "output_path": self.output_path,
        }

class KnowledgeCompiler:
    """
    知識編譯器 - 建構時核心組件。
    
    負責：
    1. 載入已核准實體（APPROVED, AUTO_APPROVED）
    2. 驗證實體狀態
    3. 標準化排序
    4. 合併實體
    5. 生成 Manifest
    6. 計算 Checksum
    7. 輸出凍結套件
    
    重要：此類別屬於建構時組件，禁止在翻譯運行時調用。
    運行時請使用 PackageReader 讀取凍結套件。
    """
    
    def __init__(
        self,
        config: CompilationConfig | None = None,
        entity_loader: EntityLoader | None = None,
        manifest_generator: ManifestGenerator | None = None,
        checksum_calculator: ChecksumCalculator | None = None,
        package_builder: PackageBuilder | None = None,
    ) -> None:
        self._config = config or CompilationConfig()
        self._entity_loader = entity_loader
        self._manifest_generator = manifest_generator or ManifestGenerator(
            package_id=self._config.package_id,
            package_version=self._config.package_version,
            compiler_version=self._config.compiler_version,
        )
        self._checksum_calculator = checksum_calculator or DEFAULT_CALCULATOR
        self._package_builder = package_builder or PackageBuilder(
            output_root=self._config.output_root,
            calculator=self._checksum_calculator,
        )
        
        # 執行時檢查：防止在運行時環境調用
        self._runtime_guard_enabled = True
    
    @property
    def config(self) -> CompilationConfig:
        return self._config
    
    def set_entity_loader(self, loader: EntityLoader) -> None:
        """設定實體載入器。"""
        self._entity_loader = loader
    
    def disable_runtime_guard(self) -> None:
        """禁用運行時防護（僅供測試使用）。"""
        self._runtime_guard_enabled = False
    
    def compile(self) -> CompilationPackage:
        """
        執行完整編譯流程。
        
        Returns:
            CompilationPackage: 編譯完成的凍結套件
            
        Raises:
            CompilationError: 編譯過程中發生錯誤
            RuntimeInvocationError: 在運行時環境調用
        """
        import time
        start_time = time.perf_counter()
        
        # 運行時防護
        self._check_runtime_guard()
        
        # 1. 載入實體
        if self._entity_loader is None:
            raise CompilationError("未設定實體載入器")
        
        raw_entities = self._entity_loader()
        
        # 2. 驗證狀態並過濾
        approved_entities, stats = self._filter_approved_entities(raw_entities)
        
        if not approved_entities:
            raise EmptyPackageError("沒有符合條件的已核准實體可供編譯")
        
        # 3. 標準化排序
        normalized_entities = self._normalize_ordering(approved_entities)
        
        # 4. 生成 Manifest
        created_at = utc_now_iso()
        manifest = self._manifest_generator.generate(
            entities=normalized_entities,
            created_at=created_at,
            metadata={
                "compiler_version": self._config.compiler_version,
                "compilation_stats": stats.to_dict(),
            },
        )
        
        # 驗證 Manifest
        ManifestValidator.assert_valid(manifest)
        
        # 5. 計算 Checksum
        checksum = self._checksum_calculator.calculate_from_entities(normalized_entities)
        
        # 6. 建構套件
        package = CompilationPackage(
            package_id=self._config.package_id,
            package_version=self._config.package_version,
            schema_versions=manifest.schema_versions,
            entities=normalized_entities,
            manifest=manifest,
            checksum=checksum,
            created_at=created_at,
            compiler_version=self._config.compiler_version,
            metadata={
                "compilation_stats": stats.to_dict(),
            },
        )
        
        # 7. 輸出套件
        output_path = self._package_builder.build(package, self._config.version_dir)
        
        # 更新統計
        final_stats = CompilationStats(
            total_input_entities=stats.total_input_entities,
            approved_entities=stats.approved_entities,
            rejected_entities=stats.rejected_entities,
            skipped_entities=stats.skipped_entities,
            entity_types_processed=stats.entity_types_processed,
            compilation_time_ms=(time.perf_counter() - start_time) * 1000,
            output_path=str(output_path),
        )
        
        # 返回帶有更新統計的套件（因為 frozen，需重建）
        return CompilationPackage(
            package_id=package.package_id,
            package_version=package.package_version,
            schema_versions=package.schema_versions,
            entities=package.entities,
            manifest=package.manifest,
            checksum=package.checksum,
            created_at=package.created_at,
            compiler_version=package.compiler_version,
            metadata={**package.metadata, "compilation_stats": final_stats.to_dict()},
        )
    def _check_runtime_guard(self) -> None:
        """檢查是否在運行時環境調用。"""
        if not self._runtime_guard_enabled:
            return
        
        # 檢查常見的運行時標誌
        import sys
        import os
        
        # 如果是作為模組被翻譯運行時導入，拋出錯誤
        # 這是一個啟發式檢查，實際部署時應由部署腳本設置環境變量
        if os.environ.get("NTPE_RUNTIME_MODE") == "translation":
            raise RuntimeInvocationError(
                "檢測到翻譯運行時環境，禁止調用知識編譯器。請使用 PackageReader 讀取凍結套件。"
            )
    
    def _filter_approved_entities(
        self,
        raw_entities: Dict[str, List[Dict[str, Any]]],
    ) -> tuple[Dict[str, List[Dict[str, Any]]], CompilationStats]:
        """過濾並驗證已核准實體。"""
        approved_entities: Dict[str, List[Dict[str, Any]]] = {}
        stats = CompilationStats()
        
        for entity_type in KNOWN_ENTITY_TYPES:
            if entity_type not in raw_entities:
                continue
            
            entity_list = raw_entities[entity_type]
            if not entity_list:
                continue
            
            stats.total_input_entities += len(entity_list)
            stats.entity_types_processed += 1
            
            approved_list = []
            
            for entity in entity_list:
                # 從 metadata 或頂層獲取審核狀態
                review_state = entity.get("metadata", {}).get("review_status", entity.get("review_state", ""))
                
                # 標準化狀態值
                review_state = review_state.upper() if review_state else ""
                
                if review_state in self._config.allowed_states:
                    approved_list.append(entity)
                    stats.approved_entities += 1
                elif review_state in {"REJECTED", "SUPERSEDED"}:
                    stats.rejected_entities += 1
                    if self._config.include_rejected:
                        approved_list.append(entity)  # 審計模式下包含
                else:
                    # PENDING, HUMAN_REVIEW_REQUIRED 等
                    stats.skipped_entities += 1
                    if self._config.strict_mode:
                        entity_id = entity.get("entity_id", "unknown")
                        raise InvalidEntityStateError(
                            entity_id=entity_id,
                            entity_type=entity_type,
                            current_state=review_state or "UNKNOWN",
                            allowed_states=list(self._config.allowed_states),
                        )
            
            if approved_list:
                approved_entities[entity_type] = approved_list
        
        return approved_entities, stats
    def _normalize_ordering(
        self,
        entities: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        標準化實體排序。
        
        排序規則：
        1. entity_type（按 KNOWN_ENTITY_TYPES 順序）
        2. entity_id
        3. version
        """
        normalized = {}
        
        for entity_type in KNOWN_ENTITY_TYPES:
            if entity_type not in entities:
                continue
            
            entity_list = entities[entity_type]
            if not entity_list:
                continue
            
            # 決定性排序
            sorted_entities = sorted(
                entity_list,
                key=lambda e: (
                    e.get("entity_id", ""),
                    e.get("version", 1),
                ),
            )
            
            normalized[entity_type] = sorted_entities
        
        return normalized
    
    def compile_entities(
        self,
        entities: Dict[str, List[Dict[str, Any]]],
    ) -> CompilationPackage:
        """
        直接編譯給定的實體（不使用 entity_loader）。
        
        用於測試或已經有實體資料的情況。
        """
        import time
        start_time = time.perf_counter()
        
        self._check_runtime_guard()
        
        # 驗證並過濾
        approved_entities, stats = self._filter_approved_entities(entities)
        
        if not approved_entities:
            raise EmptyPackageError("沒有符合條件的已核准實體可供編譯")
        
        # 標準化排序
        normalized_entities = self._normalize_ordering(approved_entities)
        
        # 生成 Manifest
        created_at = utc_now_iso()
        manifest = self._manifest_generator.generate(
            entities=normalized_entities,
            created_at=created_at,
            metadata={
                "compiler_version": self._config.compiler_version,
                "compilation_stats": stats.to_dict(),
            },
        )
        
        ManifestValidator.assert_valid(manifest)
        
        # 計算 Checksum
        checksum = self._checksum_calculator.calculate_from_entities(normalized_entities)
        
        # 建構套件
        package = CompilationPackage(
            package_id=self._config.package_id,
            package_version=self._config.package_version,
            schema_versions=manifest.schema_versions,
            entities=normalized_entities,
            manifest=manifest,
            checksum=checksum,
            created_at=created_at,
            compiler_version=self._config.compiler_version,
            metadata={
                "compilation_stats": stats.to_dict(),
            },
        )
        
        # 輸出
        output_path = self._package_builder.build(package, self._config.version_dir)
        
        final_stats = CompilationStats(
            total_input_entities=stats.total_input_entities,
            approved_entities=stats.approved_entities,
            rejected_entities=stats.rejected_entities,
            skipped_entities=stats.skipped_entities,
            entity_types_processed=stats.entity_types_processed,
            compilation_time_ms=(time.perf_counter() - start_time) * 1000,
            output_path=str(output_path),
        )
        
        return CompilationPackage(
            package_id=package.package_id,
            package_version=package.package_version,
            schema_versions=package.schema_versions,
            entities=package.entities,
            manifest=package.manifest,
            checksum=package.checksum,
            created_at=package.created_at,
            compiler_version=package.compiler_version,
            metadata={**package.metadata, "compilation_stats": final_stats.to_dict()},
        )


def create_compiler(
    package_id: str = "ntpe_knowledge",
    package_version: str = "1.0.0",
    output_root: str = "artifacts/knowledge_packages",
    entity_loader: EntityLoader | None = None,
) -> KnowledgeCompiler:
    """建立編譯器的便利函數。"""
    config = CompilationConfig(
        package_id=package_id,
        package_version=package_version,
        output_root=output_root,
    )
    return KnowledgeCompiler(config=config, entity_loader=entity_loader)