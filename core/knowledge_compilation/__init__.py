"""
Knowledge Compilation Engine (RM-5.7.4)

離線知識建構管線：
- 收集已 APPROVED 的 knowledge entity
- 排序與合併
- 產生 deterministic package
- 建立 manifest
- 產生 checksum
- 提供 runtime read-only artifact

架構邊界：
- Compiler (KnowledgeCompiler) = Build-time only
- PackageReader = Runtime read-only
- 禁止：Translation Runtime -> Knowledge Compiler
"""

from __future__ import annotations

from .models import (
    EntityRef,
    CompilationManifest,
    CompilationPackage,
    APPROVED_STATES,
    REJECTED_STATES,
    PENDING_STATES,
    KNOWN_ENTITY_TYPES,
    DEFAULT_SCHEMA_VERSIONS,
    utc_now_iso,
)

from .compiler import (
    KnowledgeCompiler,
    CompilationConfig,
    CompilationStats,
    EntityLoader,
    create_compiler,
)

from .manifest import (
    ManifestGenerator,
    ManifestValidator,
)

from .checksum import (
    ChecksumCalculator,
    DEFAULT_CALCULATOR,
)

from .package_builder import (
    PackageBuilder,
    PackageReader,
    create_package_reader,
)

from .errors import (
    CompilationError,
    InvalidEntityStateError,
    EmptyPackageError,
    ManifestGenerationError,
    ChecksumCalculationError,
    PackageBuildError,
    RuntimeInvocationError,
)

__all__ = [
    # Models
    "EntityRef",
    "CompilationManifest",
    "CompilationPackage",
    "APPROVED_STATES",
    "REJECTED_STATES",
    "PENDING_STATES",
    "KNOWN_ENTITY_TYPES",
    "DEFAULT_SCHEMA_VERSIONS",
    "utc_now_iso",
    # Compiler
    "KnowledgeCompiler",
    "CompilationConfig",
    "CompilationStats",
    "EntityLoader",
    "create_compiler",
    # Manifest
    "ManifestGenerator",
    "ManifestValidator",
    # Checksum
    "ChecksumCalculator",
    "DEFAULT_CALCULATOR",
    # Package Builder
    "PackageBuilder",
    "PackageReader",
    "create_package_reader",
    # Errors
    "CompilationError",
    "InvalidEntityStateError",
    "EmptyPackageError",
    "ManifestGenerationError",
    "ChecksumCalculationError",
    "PackageBuildError",
    "RuntimeInvocationError",
]

__version__ = "1.0.0"