# RM-5.7.0 Knowledge Generation Architecture Baseline

**Baseline**: RM-5.6 Freeze  
**Version**: RM-5.7.0  
**Status**: Architecture Governance  
**Created**: 2026-08-02  
**Purpose**: Reference architecture for Knowledge Generation subsystem — defines knowledge layer boundaries, data flows, schema contracts, and frozen constraints.

---

## 1. Knowledge Generation Architecture Overview

The Knowledge Generation Architecture introduces a structured knowledge layer that operates **orthogonal to the frozen translation pipeline**. It provides:

- **Knowledge Schema**: Formal definitions for glossary, character, narrative, and domain knowledge entities
- **Generation Pipeline**: Offline knowledge extraction, validation, and compilation workflows
- **Runtime Contracts**: Read-only interfaces for translation-time knowledge consumption
- **Boundary Enforcement**: Clear separation between knowledge management and translation execution

### 1.1 Architectural Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE GENERATION LAYER (NEW)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  Schema Layer   │  │ Generation      │  │ Runtime Contracts           │  │
│  │  (Definitions)  │  │ Pipeline        │  │ (Read-Only Interfaces)      │  │
│  │                 │  │                 │  │                             │  │
│  │ • Entity Types  │  │ • Extraction    │  │ • KnowledgeProvider         │  │
│  │ • Relationships │  │ • Validation    │  │ • SchemaResolver            │  │
│  │ • Constraints   │  │ • Compilation   │  │ • QueryInterface            │  │
│  │ • Versioning    │  │ • Serialization │  │ • CacheProtocol             │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                 │
└───────────┼────────────────────┼──────────────────────────┼─────────────────┘
            │                    │                          │
            ▼                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FROZEN TRANSLATION PIPELINE (RM-4)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  core/translator.py  │  core/prompt_engine.py  │  core/validator.py       │
│  core/chunker.py     │  core/glossary.py       │  core/rules.py           │
│  core/scheduler.py   │  engine/nvidia.py       │  lts/*.py                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Description | Enforcement |
|-----------|-------------|-------------|
| **Orthogonality** | Knowledge layer never modifies frozen translation code | Git diff --check; static analysis |
| **Schema-First** | All knowledge entities defined by versioned schemas | JSON Schema validation at generation time |
| **Read-Only Runtime** | Translation pipeline consumes knowledge via immutable contracts | Interface segregation; no write paths |
| **Offline Generation** | All knowledge extraction/validation happens offline | No provider calls during translation |
| **Version Pinning** | Knowledge artifacts pinned to schema versions | Manifest with schema_version field |
---

## 2. Knowledge Domain Boundaries

### 2.1 Core Knowledge Domains

| Domain | Entity Types | Source | Update Cadence |
|--------|--------------|--------|----------------|
| **Glossary** | Term, Alias, DomainTag, ContextRule | `glossary_builder.py` output + manual curation | Per-volume / per-series |
| **Character** | Character, Alias, Trait, Relationship, Arc | `character_memory_engine.py` output + manual curation | Per-volume / per-series |
| **Narrative** | Scene, PlotPoint, Timeline, WorldRule | Novel analysis pipeline (future) | Per-volume |
| **Style** | ToneProfile, RegisterRule, FormattingConvention | Translation policy + style guides | Per-project |

### 2.2 Domain Independence

Each domain:
- Has its own schema file (`schemas/knowledge/{domain}.schema.json`)
- Generates independent artifact (`memory/knowledge/{domain}.json`)
- Can be versioned and deployed independently
- Exposes domain-specific query interface

### 2.3 Cross-Domain Relationships

```
Glossary ◄──► Character    (character-specific terminology)
    │            │
    ▼            ▼
Narrative ◄──► Style       (narrative-aware style adaptation)
```

Cross-domain links are **explicit references** (UUIDs), not embedded objects.

---

## 3. Data Flow Architecture

### 3.1 Generation Flow (Offline)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Source     │───►│  Extraction  │───►│  Validation  │───►│ Compilation  │
---

## 4. Schema Architecture

### 4.1 Schema Hierarchy

```
schemas/knowledge/
├── base.schema.json           # Root definitions: Entity, Reference, Metadata
├── glossary.schema.json       # Term, Alias, DomainTag, ContextRule
├── character.schema.json      # Character, Alias, Trait, Relationship, Arc
├── narrative.schema.json      # Scene, PlotPoint, Timeline, WorldRule
├── style.schema.json          # ToneProfile, RegisterRule, FormattingConvention
└── manifest.schema.json       # KnowledgeManifest: version, domains, checksums
```

### 4.2 Base Entity Contract

All knowledge entities inherit from `BaseEntity`:

```json
{
  "id": "uuid-v4",
  "schema_version": "1.0.0",
  "domain": "glossary|character|narrative|style",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "source_refs": ["source_document.md:123-145"],
  "confidence": 0.0-1.0,
  "status": "draft|validated|approved|deprecated"
}
```

### 4.3 Schema Evolution Policy

| Change Type | Version Impact | Migration |
|-------------|----------------|-----------|
| Add optional field | PATCH | Auto-forward compatible |
| Add required field | MINOR | Migration script required |
| Remove field | MINOR | Deprecation cycle (2 versions) |
| Change type/constraint | MAJOR | Full regeneration required |

---

## 5. Generation Pipeline Components

### 5.1 Extraction Agents

| Agent | Input | Output | Provider |
|-------|-------|--------|----------|
| GlossaryExtractor | Novel text + existing glossary | Term candidates | LLM (offline) |
| CharacterExtractor | Novel text + existing chars | Character candidates | LLM (offline) |
---

## 6. Runtime Contracts (Read-Only)

### 6.1 KnowledgeProvider Interface

```python
class KnowledgeProvider(Protocol):
    """Read-only knowledge access for translation runtime."""
    
    def get_glossary_terms(self, domain_tags: list[str] = None) -> list[GlossaryTerm]: ...
    def get_character(self, char_id: str) -> Character | None: ...
    def get_characters_by_scene(self, scene_id: str) -> list[Character]: ...
    def get_narrative_context(self, timeline_position: float) -> NarrativeContext: ...
    def get_style_profile(self, profile_id: str) -> StyleProfile: ...
    def resolve_references(self, entity_ids: list[str]) -> dict[str, BaseEntity]: ...
```

### 6.2 SchemaResolver Interface

```python
class SchemaResolver(Protocol):
    """Schema version resolution and migration."""
    
    def get_schema(self, domain: str, version: str) -> Schema: ...
    def migrate_entity(self, entity: dict, from_version: str, to_version: str) -> dict: ...
    def validate_artifact(self, artifact_path: Path) -> ValidationResult: ...
```

### 6.3 CacheProtocol Interface

```python
class CacheProtocol(Protocol):
    """Artifact caching for translation sessions."""
    
    def load_manifest(self, manifest_path: Path) -> KnowledgeManifest: ...
    def get_artifact(self, domain: str, version: str) -> KnowledgeArtifact: ...
    def is_stale(self, artifact_path: Path, max_age_hours: int) -> bool: ...
```

---

## 7. Frozen Constraints

### 7.1 Absolute Constraints (Non-Negotiable)

| Constraint | Rationale | Verification |
|------------|-----------|--------------|
| **Zero modifications to `core/`, `lts/`, `tools/`, `tests/`** | RM-4 Freeze integrity | `git diff --check` |
| **Zero provider calls during translation** | Cost, latency, reliability | Static analysis; no `engine/` imports in knowledge layer |
| **Zero network requests during translation** | Offline capability | Network monitor; no `http`/`requests` imports |
| **Knowledge artifacts immutable at runtime** | Reproducibility | Write-once filesystem; no `open(..., 'w')` in runtime path |
| **Schema version pinned per translation session** | Deterministic behavior | Manifest validation at session start |

### 7.2 Permitted Operations (RM-5.7.0 Scope)

| Operation | Location | Authorization |
|-----------|----------|---------------|
| Create governance documentation | `docs/governance/rm5/` | This baseline |
| Define JSON Schemas | `schemas/knowledge/` | Schema design doc |
| Create generation scripts (offline) | `tools/knowledge_generation/` | Future RM-5.7.x |
| Create validation utilities | `tools/knowledge_validation/` | Future RM-5.7.x |
| Add test fixtures | `tests/fixtures/knowledge/` | Future RM-5.7.x |

### 7.3 Forbidden Operations

| Operation | Reason |
|-----------|--------|
| Modify `core/translator.py` to inject knowledge | Breaks frozen pipeline |
| Add knowledge imports to `core/prompt_engine.py` | Breaks frozen pipeline |
| Create runtime knowledge writer | Violates read-only contract |
| Execute provider API in knowledge generation (without explicit auth) | Policy violation |
| Commit generated artifacts to git | Artifacts are build outputs |

---

## 8. Integration Points

### 8.1 Current Frozen Integration Points

| Point | Current State | Knowledge Layer Hook |
|-------|---------------|----------------------|
| `core/glossary.py` | Loads `data/glossary.txt` | **None** — knowledge layer provides alternative source |
| `core/character_memory_engine.py` | Exports `memory/character_memory.json` | **None** — knowledge layer consumes this as input |
| `core/prompt_engine.py` | Builds prompt from static templates | **None** — knowledge layer provides enriched context via external tool |

### 8.2 Future Integration (Post-RM-5.7.0)

| Integration | Mechanism | Stage |
|-------------|-----------|-------|
| Glossary runtime source switch | Config flag → `KnowledgeProvider` | RM-5.8+ |
| Character context injection | Prompt preprocessor hook | RM-5.8+ |
| Narrative-aware chunking | `Chunker` strategy plugin | RM-5.9+ |
| Style-adaptive validation | `Validator` rule plugin | RM-5.9+ |

**All future integrations require explicit RM stage authorization.**

---

## 9. Validation Criteria

### 9.1 Architecture Validation (This Baseline)

- [ ] All four governance documents created
- [ ] `git diff --check` PASS
- [ ] `python -m compileall docs/governance/rm5/` PASS
- [ ] `ntpe_validate.py` PASS
- [ ] Production Code Modified = 0
- [ ] Provider Requests = 0
- [ ] Network Requests = 0

### 9.2 Schema Validation (Future RM-5.7.1)

- [ ] All schema files validate against JSON Schema meta-schema
- [ ] Cross-reference resolution 100% for test fixtures
- [ ] Migration scripts tested for v1.0.0 → v1.1.0

### 9.3 Generation Pipeline Validation (Future RM-5.7.2)

- [ ] Extraction agents produce schema-valid output
- [ ] Validation engine catches all rule violations in test corpus
- [ ] Compilation produces loadable artifacts < 500ms

### 9.4 Runtime Contract Validation (Future RM-5.7.3)

- [ ] `KnowledgeProvider` implementations pass contract tests
- [ ] Cache protocol handles stale/refresh correctly
- [ ] Zero import-time side effects in knowledge layer

---

## 10. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| RM-5.7.0 | 2026-08-02 | Architecture Governance | Initial baseline |

---

## 11. References

- RM-5.0 Architecture Baseline: `RM_5_ARCHITECTURE_BASELINE.md`
- RM-5.0 Design Principles: `RM_5_DESIGN_PRINCIPLES.md`
- RM-5.6 Root Hygiene: `RM_5_6_1_ROOT_HYGIENE.md`
- Project Boundaries Policy: `.ai/policies/project_boundaries.md`
- Provider Policy: `.ai/policies/provider_policy.md`
| NarrativeExtractor | Novel text (structured) | Scene/Plot candidates | LLM (offline) |
| StyleExtractor | Translation samples + guides | Tone/Register rules | Rule-based + LLM |

### 5.2 Validation Engine

- **Schema Validation**: JSON Schema Draft 2020-12
- **Rule Validation**: Domain-specific business rules (e.g., "no duplicate canonical terms")
- **Cross-Reference Validation**: All UUID references resolve
- **Confidence Thresholding**: Minimum confidence per domain (configurable)

### 5.3 Compilation & Serialization

- **Output Format**: JSON (UTF-8, no BOM) + Manifest
- **Compression**: Optional gzip for large artifacts
- **Indexing**: Inverted indices for common query patterns
- **Checksums**: SHA-256 per artifact in manifest
│   Corpus     │    │  Agents      │    │  (Schema +   │    │  (Artifact   │
│  (Novel txt) │    │  (LLM +      │    │   Rules)    │    │   + Manifest)│
└──────────────┘    │   Rules)     │    └──────────────┘    └──────┬───────┘
                    └──────────────┘                                 │
                          │                                          │
                          ▼                                          ▼
                   ┌──────────────┐                         ┌──────────────┐
                   │  Review &    │                         │  Versioned   │
                   │  Approval    │                         │  Artifacts   │
                   │  (Human)     │                         │  (memory/)   │
                   └──────────────┘                         └──────────────┘
```

### 3.2 Runtime Consumption Flow (Frozen)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Translation │───►│  Knowledge   │───►│  Schema      │───►│  Context     │
│  Chunk       │    │  Provider    │    │  Resolver    │    │  Injection   │
└──────────────┘    │  (Read-Only) │    │  (Cached)    │    │  (Prompt)    │
                    └──────────────┘    └──────────────┘    └──────────────┘
```

**Critical**: The runtime flow uses **only existing frozen interfaces** — no new code paths in `core/`.