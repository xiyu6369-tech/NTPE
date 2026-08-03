# RM-5.7 Architecture Baseline

**Version**: RM-5.7 (Frozen Baseline)  
**Date**: 2026-08-03  
**Status**: 🔒 **FROZEN — Reference Architecture for RM-5.8+**

---

## Purpose

This document captures the complete RM-5.7 Knowledge Layer architecture as formally accepted in **RM-5.7.6 Series Final Acceptance**. It serves as the immutable reference baseline for all RM-5.8+ development.

**RM-5.8+ Rule**: Only **Extend** — Never **Rewrite** this architecture.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER (RM-5.7 FROZEN)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐   │
│  │   GENERATION     │───►│   VALIDATION     │───►│    REVIEW      │   │
│  │ (Offline/Build)  │    │ (Schema+Biz+Ref) │    │ (Human/Approve)│   │
│  └────────┬─────────┘    └────────┬─────────┘    └───────┬────────┘   │
│           │                       │                       │            │
│           ▼                       ▼                       ▼            │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    COMPILATION (Build-Time)                     │   │
│  │  KnowledgeCompiler → Manifest → Checksum → Frozen Package      │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              FROZEN PACKAGE (artifacts/knowledge_packages/v1/)  │   │
│  │  characters.json  glossaries.json  scenes.json                  │   │
│  │  narrative.json   style.json       manifest.json  package.json  │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │         COMPATIBILITY PROVIDER (Runtime Read-Only Interface)    │   │
│  │  KnowledgePackageProvider  •  FreezeVerifier  •  LegacyMapper   │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              TRANSLATION RUNTIME (RM-4 Frozen Pipeline)         │   │
│  │  Consumes knowledge via KnowledgePackageProvider ONLY           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
## 2. Layer Definitions (Frozen)

### 2.1 Generation Layer — `core/knowledge_generation/`

**Purpose**: Offline knowledge extraction from source text

| Component | Responsibility | Key Classes |
|-----------|---------------|-------------|
| Schema System | Domain schema definitions + validation | `KnowledgeSchema`, `SchemaValidator`, `CHARACTER_SCHEMA`... |
| Extractor Base | Common extraction infrastructure | `BaseKnowledgeExtractor`, `ExtractorConfig` |
| Domain Extractors | Character, Glossary, Scene, Narrative, Style | `tools/knowledge_generation/*_extractor.py` |
| Validation Pipeline | Multi-phase validation (Schema→Biz→Ref→Confidence) | `ValidationPipeline`, `SchemaValidation`, `BusinessValidation` |
| Compiler Interface | Abstract compilation contract | `KnowledgeCompiler`, `CompilerConfig` |
| Manifest | Generation-time manifest | `KnowledgeManifest`, `ManifestBuilder` |

**Constraint**: **NEVER runs in Translation Runtime**. Pure offline/build-time.

---

### 2.2 Validation Layer — `core/knowledge_generation/validator.py`

**Purpose**: Ensure extracted entities meet quality standards

| Phase | Validator | Checks |
|-------|-----------|--------|
| SCHEMA | `SchemaValidation` | JSON Schema compliance, required fields, types, enums |
| BUSINESS | `BusinessValidation` | Domain rules (unique names, confidence bounds, relationships) |
| REFERENCE | `ReferenceValidation` | Cross-entity UUID resolution, no dangling refs |
| CONFIDENCE | `ConfidenceValidation` | Score bounds [0,1], thresholds (warning/critical) |

**Output**: `ValidationResult` with `is_valid`, `issues`, `validated_entities`

---

### 2.3 Review Layer — Offline Human Process

**Purpose**: Human approval of extracted entities before compilation

| State | Meaning |
|-------|---------|
| `PENDING` | Awaiting review |
| `APPROVED` | Cleared for compilation |
| `REJECTED` | Failed review, needs re-extraction |
| `NEEDS_REVIEW` | Conditional, requires human decision |

**Only `APPROVED` entities enter compilation.**
### 2.4 Compilation Layer — `core/knowledge_compilation/`

**Purpose**: Deterministic build of Frozen Knowledge Packages

| Component | Responsibility |
|-----------|---------------|
| `KnowledgeCompiler` | Build-time only; collects APPROVED entities, sorts, builds package |
| `ManifestGenerator` | Creates `CompilationManifest` with entity refs, counts, schema versions |
| `ChecksumCalculator` | SHA-256 over canonical package JSON (deterministic ordering) |
| `PackageBuilder` | Writes entity files + manifest + package.json |
| `PackageReader` | **Runtime read-only interface** — only class runtime may use |

**Runtime Guard**: `KnowledgeCompiler` raises `RuntimeInvocationError` if `NTPE_RUNTIME_MODE=translation`.

---

### 2.5 Frozen Package — `artifacts/knowledge_packages/v1/`

**Structure** (Immutable after build):

```
v1/
├── characters.json      # Array of character entities
├── glossaries.json      # Array of glossary entities (irregular plural)
├── scenes.json          # Array of scene entities
├── narrative.json       # Array of narrative entities
├── style.json           # Array of style entities
├── manifest.json        # CompilationManifest (counts, versions, checksum)
└── package.json         # Full package: {entities: {...}, manifest: {...}, checksum: "..."}
```

**Properties**:
- Deterministic: Same input → identical checksum
- Self-verifying: Manifest includes SHA-256 checksum
- Versioned: `package_version`, per-entity `schema_version`
- Read-only: Runtime never writes here

---

### 2.6 Compatibility Provider — `core/knowledge/compatibility/`

**Purpose**: Single read-only interface for Translation Runtime

| Module | Exports | Purpose |
|--------|---------|---------|
| `provider.py` | `KnowledgePackageProvider`, `create_provider()`, `EntityQuery` | Runtime entity access |
| `freeze_verifier.py` | `FreezeVerifier`, `verify_package()`, `VerificationResult`, `FreezeVerificationReport` | Package integrity verification |
| `legacy_mapper.py` | `LegacyMapper` | **Offline only** — v1→v2 migration |

**Provider API (FROZEN)**:
```python
# Typed entity access
get_character(entity_id, name) -> List[Dict]
get_glossary(entity_id, name) -> List[Dict]
get_scene(entity_id, name) -> List[Dict]
get_narrative(entity_id, name) -> List[Dict]
get_style(entity_id, name) -> List[Dict]
get_entities(entity_type, entity_id, name) -> List[Dict]

# Metadata
get_package_info() -> Dict
get_entity_types() -> List[str]
get_entity_count(entity_type) -> int
total_entity_count() -> int

# Verification
verify() -> bool
is_verified() -> bool

# Prompt pipeline integration
build_context(entity_types) -> Dict
attach_to_prompt_package(prompt_package) -> Dict
```

**No write methods. No compile/extract/validate/review methods.**

---

### 2.7 Translation Runtime — Consumer Only

**Purpose**: Use knowledge during translation — **zero knowledge-layer imports except provider**

| Runtime Component | Knowledge Access Pattern |
## 3. Data Flow (Frozen)

### 3.1 Build-Time Flow (Offline)

```
Source Novel Text
       │
       ▼
Chunking + Extraction Prompts (RM-5.7.2A)
       │
       ▼
Domain Extractors (Character/Glossary/Scene/Narrative/Style)
       │
       ▼
Validation Pipeline (Schema → Business → Reference → Confidence)
       │
       ▼
Human Review (Approve/Reject)
       │
       ▼
Compilation (KnowledgeCompiler)
       │
       ▼
Manifest + Checksum + Package Files
       │
       ▼
Frozen Package (artifacts/knowledge_packages/v1/)
```

### 3.2 Runtime Flow (Translation)

```
Translation Chunk
       │
       ▼
KnowledgePackageProvider (created once per session)
       │
       ▼
provider.build_context(entity_types)  or  provider.get_character(...)
       │
       ▼
Prompt Package + Knowledge Context
       │
       ▼
Translation Engine → Provider → Translation Output
```

## 4. Schema Contracts (Frozen v1.0)

| Domain | Schema File | Version | Key Fields |
## 5. Boundary Enforcement (Frozen)

| Boundary | Enforcement Mechanism |
|----------|----------------------|
| Runtime ⇏ Generation | Import analysis; `knowledge_generation` not in runtime deps |
| Runtime ⇏ Compiler | `KnowledgeCompiler` runtime guard (`RuntimeInvocationError`) |
| Runtime ⇏ Validation | Not exported in compatibility layer |
| Runtime ⇏ Review | Offline-only; no runtime entry point |
| Runtime ⇏ Package Files | Only via `PackageReader` (internal to provider) |
| Compiler ⇏ Runtime | Compiler checks `NTPE_RUNTIME_MODE` env var |
| Generation ⇏ Runtime | No shared state; pure offline |

## 6. Version Pinning

| Artifact | Version Scheme | Location |
|----------|----------------|----------|
| Package | `package_version` (semver) | `manifest.json`, `package.json` |
| Schema | `schema_version` per domain | `manifest.schema_versions`, each entity |
| Compiler | `compiler_version` | `manifest.compiler_version` |
| Provider API | Implicit via package version | `provider.build_context()` returns `version: "rm-5.7.5"` |

## 7. RM-5.8+ Extension Guidelines

| Extension Type | Guideline | Example |
|----------------|-----------|---------|
| New extractor | Add to `tools/knowledge_generation/` only | `tools/knowledge_generation/magic_system_extractor.py` |
| New schema field | Optional only; backward compatible | Add `sub_genre` to narrative schema |
| New validation check | Add to `FreezeVerifier` (additive) | Check for duplicate aliases |
| New entity type | Requires RFC; bumps package version | Add `magic_system` entity type |
| Better prompts | Update `tools/knowledge_generation/*_extractor.py` | Improved few-shot examples |
| Incremental package | New package version (v2); provider handles both | `artifacts/knowledge_packages/v2/` |

**Never**:
- Modify `KnowledgePackageProvider` method signatures
- Remove frozen APIs
- Allow runtime to import generation/compilation/validation/review
- Write to package directory from runtime

## 8. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_7_6_FINAL_ACCEPTANCE.md` | Formal acceptance record |
| `RM_5_7_6_RUNTIME_BOUNDARY_REPORT.md` | Runtime boundary audit detail |
| `RM_5_7_6_ACCEPTANCE_CHECKLIST.md` | Checklist used for verification |
| `RM_5_7_6_EXECUTION_REPORT.md` | Validation execution evidence |
| `RM_5_7_0_KNOWLEDGE_GENERATION_ARCHITECTURE.md` | Original architecture baseline |
| `RM_5_7_0_KNOWLEDGE_SCHEMA_DESIGN.md` | Schema design decisions |
| `RM_5_7_5_LEGACY_DEPRECATION_REPORT.md` | Legacy migration completion |

---

*This architecture is FROZEN as of RM-5.7.6 (2026-08-03). All RM-5.8+ development must Extend Only.*
|--------|-------------|---------|------------|
| Character | `character_schema.json` | 1.0 | name, attributes(canonical_name, role, traits...), confidence |
| Glossary | `glossary_schema.json` | 1.0 | name, attributes(canonical_translation, domain_tags...), confidence |
| Scene | `scene_schema.json` | 1.0 | name, attributes(location, characters, summary...), confidence |
| Narrative | `narrative_schema.json` | 1.0 | name, attributes(plot_points, themes...), confidence |
| Style | `style_schema.json` | 1.0 | name, attributes(category, rules, examples...), confidence |

**Common Required Fields** (all domains):
- `entity_id` (UUID)
- `entity_type` (discriminator)
- `schema_version` (e.g., "1.0")
- `name` (string, 1-200 chars)
- `confidence` (float 0.0-1.0)
- `created_at`, `updated_at` (ISO 8601)
- `version` (integer ≥ 1)
|-------------------|-------------------------|
| Prompt Builder | `provider.build_context()` → inject into prompt package |
| Chunk Translator | Receives prompt package with knowledge context |
| Session Manager | Creates provider once per session |

**Forbidden in Runtime**:
- `import core.knowledge_generation`
- `import core.knowledge_compilation` (except `PackageReader` via provider)
- `import core.knowledge_review`
- `import core.knowledge_validation`
- Direct file I/O on knowledge packages
- Direct schema loading