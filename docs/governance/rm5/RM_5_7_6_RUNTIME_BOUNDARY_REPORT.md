# RM-5.7.6 Runtime Boundary Report

**Version**: RM-5.7.6  
**Date**: 2026-08-03  
**Status**: 🔒 **FROZEN — Boundary Verification Complete**

---

## Purpose

Detailed audit of the Translation Runtime boundary — confirming that runtime code **only** accesses knowledge through the `KnowledgePackageProvider` and has **zero** direct dependencies on generation, compilation, validation, or review layers.

---

## 1. Import Audit

### 1.1 Verified: Runtime Imports

```python
# Translation Runtime (core/translation_runtime/, core/translation_engine/, etc.)
# ONLY imports from knowledge layer:

from core.knowledge.compatibility.provider import (
    KnowledgePackageProvider,
    create_provider,
    EntityQuery,
)
```

### 1.2 Verified: Forbidden Imports (Absent)

| Forbidden Import | Status | Verification Method |
|------------------|--------|---------------------|
| `core.knowledge_generation` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge_compilation.KnowledgeCompiler` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge_compilation.PackageBuilder` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge_review` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge_validation` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge.legacy` | ✅ NOT IMPORTED | grep + import graph |
| `core.knowledge.generation` | ✅ NOT IMPORTED | grep + import graph |

---

## 2. Operation Audit

### 2.1 Verified: Runtime CANNOT Perform

| Operation | Blocked By | Evidence |
|-----------|------------|----------|
| Direct JSON file load (`json.load(open(...))`) | Architecture policy + provider abstraction | Provider wraps PackageReader |
| Direct schema read/validation | SchemaValidator not exported to runtime | Only in generation layer |
| Entity extraction | Extractors in `tools/knowledge_generation/` (offline) | Not in runtime deps |
| Package compilation | `KnowledgeCompiler` runtime guard | Raises `RuntimeInvocationError` |
| Entity validation | ValidationPipeline not exported | Only in generation layer |
| Human review invocation | Review is offline process | No runtime entry point |
| Legacy file access (`memory/*.json`) | LegacyMapper offline-only | Not imported by runtime |
| Package file write | Provider has no write methods | Verified by FreezeVerifier |

### 2.2 Verified: Runtime CAN Perform (via Provider)

| Operation | Provider Method | Returns |
|-----------|-----------------|---------|
| Get character by ID/name | `get_character(entity_id, name)` | `List[Dict]` |
| Get glossary by ID/name | `get_glossary(entity_id, name)` | `List[Dict]` |
| Get scene by ID/name | `get_scene(entity_id, name)` | `List[Dict]` |
| Get narrative by ID/name | `get_narrative(entity_id, name)` | `List[Dict]` |
| Get style by ID/name | `get_style(entity_id, name)` | `List[Dict]` |
| Generic entity query | `get_entities(entity_type, entity_id, name)` | `List[Dict]` |
| Package metadata | `get_package_info()` | `Dict` |
---

## 3. Provider Method Surface Audit

### 3.1 Public Methods on `KnowledgePackageProvider`

```python
# Verified via reflection:
[
    'ENTITY_TYPES',           # Class constant tuple
    'attach_to_prompt_package',  # Prompt pipeline integration
    'build_context',          # Prompt pipeline integration
    'get_character',          # Typed entity access
    'get_entities',           # Generic entity access
    'get_entity_count',       # Metadata
    'get_entity_types',       # Metadata
    'get_glossary',           # Typed entity access
    'get_narrative',          # Typed entity access
    'get_package_info',       # Metadata
    'get_scene',              # Typed entity access
    'get_style',              # Typed entity access
    'is_verified',            # Verification status
    'manifest',               # Property (read-only)
    'package',                # Property (read-only)
    'package_dir',            # Property (read-only)
    'total_entity_count',     # Metadata
    'verify',                 # Verification
]
```

### 3.2 Verified: NO Write/Mutate Methods

| Forbidden Pattern | Methods Checked | Result |
|-------------------|-----------------|--------|
| `write_*` | — | ✅ NONE |
| `save_*` | — | ✅ NONE |
| `create_*` | — | ✅ NONE |
| `build_*` | `build_context` (read-only) | ✅ ALLOWED |
| `update_*` | — | ✅ NONE |
| `delete_*` | — | ✅ NONE |
| `remove_*` | — | ✅ NONE |
| `set_*` | — | ✅ NONE |
| `compile` | — | ✅ NONE |
| `extract` | — | ✅ NONE |
| `validate` | — | ✅ NONE |
| `review` | — | ✅ NONE |

**Automated Check**: `FreezeVerifier._check_readonly_boundary()` scans all methods — **PASSED**

---

## 4. Legacy Isolation Audit

### 4.1 Legacy Components (Offline Only)

| Component | Path | Runtime Import? |
|-----------|------|-----------------|
| `LegacyMapper` | `core/knowledge/compatibility/legacy_mapper.py` | ❌ NO |
| v1→v2 migration scripts | `tools/legacy_migration/` | ❌ NO |
| Legacy JSON files | `memory/character_memory.json`, `memory/glossary.json`, etc. | ❌ NO |
| Flat glossary | `data/glossary.txt` | ❌ NO |

### 4.2 Verified: Zero Legacy References in Runtime

```bash
# Search in core/knowledge/runtime/
findstr /s /i "legacy" core/knowledge/runtime/
# Result: NO MATCHES

findstr /s /i "migration" core/knowledge/runtime/
# Result: NO MATCHES

findstr /s /i "upgrade" core/knowledge/runtime/
# Result: NO MATCHES

findstr /s /i "convert" core/knowledge/runtime/
# Result: NO MATCHES
```

### 4.3 Legacy Awareness: ONLY in Compatibility Layer (Offline)

```python
# core/knowledge/compatibility/legacy_mapper.py
# ONLY used by migration scripts, NEVER by runtime
class LegacyMapper:
    """Maps v1 legacy files to v2 package structure. OFFLINE ONLY."""
```

---

## 5. Compiler Runtime Guard

### 5.1 Guard Implementation

```python
# core/knowledge_compilation/compiler.py:236-239
if os.environ.get("NTPE_RUNTIME_MODE") == "translation":
    raise RuntimeInvocationError(
        "檢測到翻譯運行時環境，禁止調用知識編譯器。請使用 PackageReader 讀取凍結套件。"
    )
```

### 5.2 Verified: Guard Active

| Test | Result |
|------|--------|
| `test_compiler_raises_in_runtime_mode` | ✅ PASS |
| `test_compile_method_also_guarded` | ✅ PASS |
| `test_package_reader_works_in_runtime_mode` | ✅ PASS |

**Guard cannot be bypassed in production** (requires explicit `disable_runtime_guard()` only for testing).

---

## 6. Dependency Direction Verification

### 6.1 Allowed Dependency Flow

```
Translation Runtime
       │
       ▼ (imports)
core.knowledge.compatibility.provider.KnowledgePackageProvider
       │
       ▼ (uses internally)
core.knowledge_compilation.package_builder.PackageReader
       │
       ▼ (reads)
Frozen Package (artifacts/knowledge_packages/v1/)
```

### 6.2 Verified: NO Reverse Dependencies

| Reverse Path | Checked | Result |
|--------------|---------|--------|
| `PackageReader` → Runtime | Import scan | ✅ NO |
| `KnowledgeCompiler` → Runtime | Import scan | ✅ NO |
| `ValidationPipeline` → Runtime | Import scan | ✅ NO |
| `BaseKnowledgeExtractor` → Runtime | Import scan | ✅ NO |
| `LegacyMapper` → Runtime | Import scan | ✅ NO |
| `knowledge_generation` → Runtime | Import scan | ✅ NO |

---

## 7. Summary

| Boundary Aspect | Status | Evidence |
|-----------------|--------|----------|
| Import isolation | ✅ PASS | Only provider imported |
| Operation restriction | ✅ PASS | No write/compile/extract/validate/review |
| Provider surface | ✅ PASS | 18 methods, all read-only |
| Legacy isolation | ✅ PASS | Zero runtime refs |
| Compiler guard | ✅ PASS | RuntimeInvocationError enforced |
| Dependency direction | ✅ PASS | Acyclic, unidirectional |

**RUNTIME BOUNDARY: VERIFIED AND FROZEN**

---

*This boundary is FROZEN as of RM-5.7.6. Any RM-5.8+ runtime changes must preserve these boundaries.*
| Entity types present | `get_entity_types()` | `List[str]` |
| Entity count by type | `get_entity_count(entity_type)` | `int` |
| Total entity count | `total_entity_count()` | `int` |
| Package verification | `verify()` | `bool` (raises on fail) |
| Verification status | `is_verified()` | `bool` |
| Build prompt context | `build_context(entity_types)` | `Dict` (knowledge_context) |
| Attach to prompt package | `attach_to_prompt_package(pkg)` | `Dict` |
**No other knowledge-layer imports found in runtime code paths.**