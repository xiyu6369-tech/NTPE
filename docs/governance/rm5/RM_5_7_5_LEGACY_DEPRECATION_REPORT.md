# RM-5.7.5 Legacy Deprecation Report

**Date**: 2026-08-03  
**Status**: Complete  

---

## Overview

This report documents the migration from legacy knowledge storage (v1) to
Frozen Knowledge Packages (v2) as part of RM-5.7.5 Integration & Legacy Migration.

The legacy system used scattered JSON files in `memory/` and flat text files in `data/`.
The v2 system consolidates all knowledge into a single, versioned, verified package
at `artifacts/knowledge_packages/v1/` with deterministic builds and read-only runtime access.

---

## Legacy Sources (v1)

| Legacy Path | Type | Description | Status |
|-------------|------|-------------|--------|
| `memory/character_memory.json` | Character | Extracted character database | **Deprecated** |
| `memory/glossary.json` | Glossary | Structured glossary database | **Deprecated** |
| `memory/knowledge_base.json` | Composite | Merged character + glossary | **Deprecated** |
| `memory/character_match_dictionary.json` | Character | Alias resolution index | **Deprecated** |
| `memory/character_alias_index.json` | Character | Resolver-compatible aliases | **Deprecated** |
| `data/glossary.txt` | Glossary | Flat key=value glossary | **Deprecated** |

---

## v2 Package Structure

```
artifacts/knowledge_packages/v1/
|-- characters.json      # Character entities
|-- glossaries.json      # Glossary entities (irregular plural)
|-- scenes.json          # Scene entities
|-- narrative.json       # Narrative entities
|-- style.json           # Style entities
|-- manifest.json        # Package manifest with counts, versions, checksum
|-- package.json         # Full package (all entities + manifest)
```

---

## Migration Mapping

| Legacy Source | v2 Target | Entity Type | Notes |
|---------------|-----------|-------------|-------|
| `memory/character_memory.json` | `characters.json` | character | Direct migration |
| `memory/glossary.json` | `glossaries.json` | glossary | Direct migration |
| `memory/knowledge_base.json` | `characters.json` + `glossaries.json` | character, glossary | Split composite |
| `memory/character_match_dictionary.json` | `characters.json` | character | Aliases merged into entities |
| `memory/character_alias_index.json` | `characters.json` | character | Aliases merged into entities |
| `data/glossary.txt` | `glossaries.json` | glossary | Parsed from flat format |

---

## Runtime Boundary

### PROHIBITED for Runtime

- `core.knowledge_generation` (Extractor)
- `core.knowledge_compilation` (Compiler)
- `core.knowledge_review` (Review Engine)
- `core.knowledge_validation` (Validator)
- Any generation pipeline component

### ALLOWED for Runtime

- `core.knowledge.compatibility.KnowledgePackageProvider` (READ-ONLY)

The provider exposes only typed read methods:

```python
provider.get_character(entity_id=None, name=None)
provider.get_glossary(entity_id=None, name=None)
provider.get_scene(entity_id=None, name=None)
provider.get_narrative(entity_id=None, name=None)
provider.get_style(entity_id=None, name=None)
provider.get_entities(entity_type, entity_id=None, name=None)
provider.build_context(entity_types=None)  # For prompt pipeline
provider.verify()  # Integrity check
```

---

## Verification Requirements

All v2 packages must pass:

1. **Checksum Verification** - Package checksum matches manifest
2. **Manifest Verification** - Entity counts match actual files
3. **Structure Verification** - All required files exist
4. **Deterministic Rebuild** - Package can be rebuilt from source with identical checksum
5. **Compatibility** - Package schema matches current provider expectations
6. **Read-Only Boundary** - No write methods exposed to runtime

---

## Deprecation Timeline

| Phase | Date | Action |
|-------|------|--------|
| RM-5.7.5 | 2026-08-03 | Legacy paths documented, v2 package established, compatibility layer active |
| RM-5.8 | TBD | Legacy paths marked with deprecation warnings in code |
| RM-5.9 | TBD | Legacy paths removed from active profiles |
| RM-5.10 | TBD | Legacy files archived to `archive/legacy/` |

---

## Verification

Run freeze verification:

```python
from core.knowledge.compatibility import verify_package

report = verify_package("artifacts/knowledge_packages/v1")
print(f"Overall: {\"PASS\" if report.overall_passed else \"FAIL\"}")
for r in report.results:
    print(f"  {r.check_name}: {\"OK\" if r.passed else \"FAIL\"} - {r.detail}")
```

---

## Sign-off

- Architecture: | **Baseline established (RM-5.7.0)**
- Capability Audit: | **Complete (RM-5.7.1)**
- Schema & Extraction: | **Complete (RM-5.7.2)**
- Validation: | **Complete (RM-5.7.3)**
- Compilation: | **Complete (RM-5.7.4)**
- **Integration & Legacy Migration: | **Complete (RM-5.7.5)**

**RM-5.7 Series Complete**
