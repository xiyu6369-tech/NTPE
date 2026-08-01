# RM-5.7.0 Boundary Report

**Baseline**: RM-5.7.0 Architecture Baseline  
**Version**: RM-5.7.0  
**Status**: Boundary Governance  
**Created**: 2026-08-02  
**Purpose**: Defines and enforces the boundary between Knowledge Generation Layer and Frozen Translation Pipeline.

---

## 1. Boundary Definition

### 1.1 The Hard Boundary

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GENERATION LAYER (RM-5.7+)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │  Schemas    │ │  Generation │ │  Validation │ │  Runtime Contracts  │  │
│  │  (JSON)     │ │  Pipeline   │ │  Engine     │ │  (Interfaces Only)  │  │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘  │
└─────────┼───────────────┼───────────────┼───────────────────┼──────────────┘
          │               │               │                   │
          ▼               ▼               ▼                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         █████ HARD BOUNDARY █████                          │
│                    NO CODE CROSSING PERMITTED                              │
│                    NO SHARED MODULES                                       │
│                    NO RUNTIME DEPENDENCIES                                 │
└────────────────────────────────────────────────────────────────────────────┘
          │               │               │                   │
          ▼               ▼               ▼                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      FROZEN TRANSLATION PIPELINE (RM-4)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │  core/      │ │  engine/    │ │  lts/       │ │  tools/ (frozen)    │  │
│  │  translator │ │  nvidia.py  │ │  batch_*    │ │  provider_*         │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Boundary Rules

---

## 2. Frozen Pipeline Inventory (RM-4)

### 2.1 Core Modules (FROZEN - No Modifications)

| Module | Path | Responsibility | Knowledge Layer Access |
|--------|------|----------------|------------------------|
| Translator | `core/translator.py` | File→chunks→translate→validate→output | **NONE** - reads `data/glossary.txt` only |
| Chunker | `core/chunker.py` | Scene/paragraph segmentation | **NONE** |
| Prompt Engine | `core/prompt_engine.py` | Template + glossary + context + profile | **NONE** - builds prompt from static data |
| Glossary | `core/glossary.py` | Runtime glossary loader + term enforcement | **NONE** - loads `data/glossary.txt` |
| Character Memory | `core/character_memory_engine.py` | Offline character DB export | **NONE** - exports to `memory/` |
| Validator | `core/validator.py` | Post-translation validation | **NONE** |
| Rules | `core/rules.py` | Post-processing rules | **NONE** |
| Formatter | `core/formatter.py` | Paragraph/quote normalization | **NONE** |
| Scheduler | `core/scheduler.py` | RPM rate limiting | **NONE** |
| Config | `core/config.py` | Configuration management | **NONE** |
| Exceptions | `core/exceptions.py` | Exception types | **NONE** |

### 2.2 Engine Modules (FROZEN)

| Module | Path | Responsibility |
|--------|------|----------------|
| NVIDIA Engine | `engine/nvidia.py` | NIM API client (llama-3.3-70b-instruct) |

### 2.3 LTS Modules (FROZEN)

| Module | Path | Responsibility |
|--------|------|----------------|
| Batch Runtime | `lts/batch_translation_runtime.py` | Batch translation execution |
| Batch Monitor | `lts/batch_runtime_monitor.py` | Batch monitoring |
| RC Freeze | `lts/rc_freeze.py` | Release candidate freeze |
| Release Candidate | `lts/release_candidate.py` | RC management |
| Stable Finalization | `lts/stable_finalization.py` | Stable release finalization |
| Runtime Freeze | `lts/runtime_freeze.py` | Runtime freeze |
| Regression Validation | `lts/regression_validation.py` | Regression test validation |
| Quality Validation | `lts/quality_validation.py` | Quality validation |
| Performance Validation | `lts/performance_validation.py` | Performance validation |
| Compatibility Validation | `lts/compatibility_validation.py` | Compatibility validation |
| Final Validation | `lts/final_validation.py` | Final validation |

---

## 3. Knowledge Layer Permitted Structure (RM-5.7.0+)

### 3.1 New Directories (Authorized)

```
schemas/knowledge/           # JSON Schema definitions (NEW)
├── base.schema.json
├── glossary.schema.json
├── character.schema.json
├── narrative.schema.json
├── style.schema.json
└── manifest.schema.json

tools/knowledge_generation/  # Offline generation scripts (FUTURE RM-5.7.1+)
├── extractors/
├── validators/
├── compilers/
└── main.py

tools/knowledge_validation/  # Validation utilities (FUTURE RM-5.7.1+)
├── schema_validator.py
├── business_rules.py
├── cross_ref_validator.py
└── manifest_validator.py

tests/fixtures/knowledge/    # Test fixtures (FUTURE RM-5.7.1+)
├── glossary_samples.json
├── character_samples.json
└── manifest_samples.json

docs/governance/rm5/         # Governance documentation (THIS BASELINE)
├── RM_5_7_0_KNOWLEDGE_GENERATION_ARCHITECTURE.md
├── RM_5_7_0_KNOWLEDGE_SCHEMA_DESIGN.md
├── RM_5_7_0_GENERATION_FLOW.md
└── RM_5_7_0_BOUNDARY_REPORT.md
```

### 3.2 Artifact Output Locations (Read-Only for Translation)

```
memory/knowledge/            # Generated artifacts (build output, not source)
├── manifest.json            # KnowledgeManifest
├── glossary.json            # list[GlossaryTerm]
---

## 4. Interface Contracts (Read-Only)

### 4.1 KnowledgeProvider (Protocol)

```python
# Location: knowledge_layer/contracts/provider.py (NEW - not in core/)
class KnowledgeProvider(Protocol):
    """Read-only knowledge access for translation runtime.
    
    IMPLEMENTATION NOTE: This interface is DEFINED in knowledge layer.
    The FROZEN pipeline does NOT import this. Instead, an adapter
    in a future RM stage (RM-5.8+) will bridge the gap.
    """
    
    def get_glossary_terms(self, domain_tags: list[str] = None) -> list[GlossaryTerm]: ...
    def get_character(self, char_id: str) -> Character | None: ...
    def get_characters_by_scene(self, scene_id: str) -> list[Character]: ...
    def get_narrative_context(self, timeline_position: float) -> NarrativeContext: ...
    def get_style_profile(self, profile_id: str) -> StyleProfile: ...
    def resolve_references(self, entity_ids: list[str]) -> dict[str, BaseEntity]: ...
```

### 4.2 SchemaResolver (Protocol)

```python
# Location: knowledge_layer/contracts/resolver.py (NEW)
class SchemaResolver(Protocol):
    """Schema version resolution and migration."""
    
    def get_schema(self, domain: str, version: str) -> Schema: ...
    def migrate_entity(self, entity: dict, from_version: str, to_version: str) -> dict: ...
    def validate_artifact(self, artifact_path: Path) -> ValidationResult: ...
```

### 4.3 CacheProtocol (Protocol)

```python
# Location: knowledge_layer/contracts/cache.py (NEW)
---

## 5. Boundary Violation Detection

### 5.1 Static Analysis Rules

```python
# .github/workflows/boundary_check.yml (FUTURE)
BOUNDARY_RULES = [
    # Knowledge layer must not import frozen modules
    {
        "pattern": r"from (core|engine|lts|tools\.provider_) import",
        "paths": ["tools/knowledge_generation/**", "schemas/knowledge/**"],
        "message": "Knowledge layer imports frozen module"
    },
    # Frozen modules must not import knowledge layer
    {
        "pattern": r"from (schemas|tools\.knowledge_) import",
        "paths": ["core/**", "engine/**", "lts/**", "tools/provider_*/**"],
        "message": "Frozen module imports knowledge layer"
    },
    # No shared non-stdlib modules
    {
        "check": "shared_modules",
        "allowlist": ["json", "pathlib", "dataclasses", "typing", "uuid", "datetime"],
        "message": "Shared module detected across boundary"
    }
]
```

### 5.2 Runtime Boundary Guards

```python
# knowledge_layer/runtime_guard.py (FUTURE)
class RuntimeBoundaryGuard:
    """Enforce boundary at runtime."""
    
    FORBIDDEN_IMPORTS = {
        'core', 'engine', 'lts', 'tools.provider_controls', 'tools.provider_utils'
    }
    
    @classmethod
    def check_imports(cls):
        """Verify no forbidden modules loaded."""
        import sys
        for module in sys.modules:
            if any(module.startswith(f) for f in cls.FORBIDDEN_IMPORTS):
                if not module.startswith('knowledge_layer'):
                    raise BoundaryViolationError(
                        f"Forbidden import detected: {module}"
                    )
    
    @classmethod
---

## 6. Current Integration Points (Read-Only)

### 6.1 Existing Frozen Integration Points

| Frozen Module | Current Behavior | Knowledge Layer Relationship |
|---------------|------------------|------------------------------|
| `core/glossary.py` | Loads `data/glossary.txt` (text format) | **None** — knowledge layer provides alternative `memory/knowledge/glossary.json` |
| `core/character_memory_engine.py` | Exports `memory/character_memory.json` | **Input Source** — knowledge layer consumes this for incremental generation |
| `core/prompt_engine.py` | Builds prompt from static templates | **None** — knowledge layer provides enriched context via external preprocessing tool |
| `core/translator.py` | Main translation loop | **None** — no knowledge injection |
| `core/validator.py` | Rule-based validation | **None** — no knowledge-aware rules |

### 6.2 Data Flow Direction

```
EXISTING (RM-4):
core/character_memory_engine.py ──exports──► memory/character_memory.json
                                                             │
                                                             ▼ (CONSUMED by knowledge layer)
knowledge_layer/generation ──reads──► CharacterExtractor (incremental)

PROPOSED FUTURE (RM-5.8+):
---

## 7. Forbidden Operations Matrix

| Operation | Layer | Status | Reason |
|-----------|-------|--------|--------|
| Modify `core/translator.py` | Frozen | **FORBIDDEN** | RM-4 Freeze |
| Modify `core/prompt_engine.py` | Frozen | **FORBIDDEN** | RM-4 Freeze |
| Modify `core/glossary.py` | Frozen | **FORBIDDEN** | RM-4 Freeze |
| Modify `engine/nvidia.py` | Frozen | **FORBIDDEN** | RM-4 Freeze |
| Import `core.*` in knowledge layer | Knowledge | **FORBIDDEN** | Boundary violation |
| Import `knowledge_layer.*` in `core/` | Frozen | **FORBIDDEN** | Boundary violation |
| Call provider API during translation | Either | **FORBIDDEN** | Policy + boundary |
| Write to `memory/knowledge/` during translation | Runtime | **FORBIDDEN** | Read-only contract |
| Commit generated artifacts to git | Either | **FORBIDDEN** | Build outputs |
| Shared utility module across boundary | Either | **FORBIDDEN** | Coupling |

---

## 8. Permitted Operations (RM-5.7.0 Scope)

| Operation | Layer | Authorization |
|-----------|-------|---------------|
| Create governance docs | `docs/governance/rm5/` | This baseline |
| Define JSON schemas | `schemas/knowledge/` | Schema design doc |
| Create generation scripts | `tools/knowledge_generation/` | Future RM-5.7.1 |
| Create validation utils | `tools/knowledge_validation/` | Future RM-5.7.1 |
| Add test fixtures | `tests/fixtures/knowledge/` | Future RM-5.7.1 |
| Read `memory/character_memory.json` | Knowledge (offline) | Input source |
| Write `memory/knowledge/*.json` | Knowledge (offline) | Build output |
| Define interface contracts | `knowledge_layer/contracts/` | Architecture baseline |

---

## 9. Validation Checklist

### 9.1 Boundary Compliance (This Baseline)

- [ ] No `core/`, `engine/`, `lts/`, `tools/provider_*` imports in knowledge layer docs
- [ ] No knowledge layer imports in frozen module docs
- [ ] All four governance documents created in `docs/governance/rm5/`
- [ ] Schema files defined in `schemas/knowledge/` (documented, not created)
- [ ] Artifact output paths documented as `memory/knowledge/` (build outputs)
- [ ] Interface contracts defined as Protocols (not implemented in frozen code)

### 9.2 Automated Verification (Future CI)

- [ ] `git diff --check` PASS
- [ ] `python -m compileall docs/governance/rm5/` PASS
- [ ] `ntpe_validate.py` PASS
- [ ] Static import analysis: 0 boundary violations
- [ ] Production Code Modified = 0
- [ ] Provider Requests = 0
- [ ] Network Requests = 0

---

## 10. Evolution Path (Post-RM-5.7.0)

### 10.1 Authorized Future Stages

| Stage | Scope | Boundary Impact |
|-------|-------|-----------------|
| RM-5.7.1 | Schema implementation + validation tools | No boundary crossing (offline only) |
| RM-5.7.2 | Generation pipeline implementation | No boundary crossing (offline only) |
| RM-5.7.3 | Runtime contract implementations | **Boundary crossing via adapter** — requires RM-5.8 authorization |
| RM-5.8 | Translation pipeline integration | **Requires explicit authorization** — modifies frozen pipeline via adapter pattern |

### 10.2 Integration Pattern (RM-5.8+)

```
knowledge_layer/runtime/
├── provider_impl.py          # Implements KnowledgeProvider
├── cache_impl.py             # Implements CacheProtocol
└── adapter.py                # BRIDGE: translates provider calls to frozen pipeline hooks

# Frozen pipeline (RM-5.8 modification - EXPLICITLY AUTHORIZED):
core/translator.py ──calls──► adapter.get_context(chunk) ──► KnowledgeProvider
```

**Critical**: No RM-5.7.x stage may modify frozen pipeline. Integration requires RM-5.8+ with full regression evidence.

---

## 11. References

- RM-5.7.0 Architecture Baseline: `RM_5_7_0_KNOWLEDGE_GENERATION_ARCHITECTURE.md`
- RM-5.7.0 Schema Design: `RM_5_7_0_KNOWLEDGE_SCHEMA_DESIGN.md`
- RM-5.7.0 Generation Flow: `RM_5_7_0_GENERATION_FLOW.md`
- Project Boundaries Policy: `.ai/policies/project_boundaries.md`
- Provider Policy: `.ai/policies/provider_policy.md`
- RM-5.6 Root Hygiene: `RM_5_6_1_ROOT_HYGIENE.md`
knowledge_layer/runtime ──provides──► KnowledgeProvider
                                                    │
                                                    ▼ (via ADAPTER)
core/translator.py ──consumes──► enriched context
```

**Key**: Current RM-5.7.0 has **zero** integration. Future integration requires explicit RM stage authorization.
    def check_network(cls):
        """Verify no network calls in translation path."""
        # Socket monkey-patch or network monitor
        pass
```
class CacheProtocol(Protocol):
    """Artifact caching for translation sessions."""
    
    def load_manifest(self, manifest_path: Path) -> KnowledgeManifest: ...
    def get_artifact(self, domain: str, version: str) -> KnowledgeArtifact: ...
    def is_stale(self, artifact_path: Path, max_age_hours: int) -> bool: ...
```
├── character.json           # list[Character]
├── narrative.json           # list[NarrativeEntity]
└── style.json               # list[StyleEntity]
```

**Critical**: These are **build outputs**, not source files. They are:
- Generated by offline pipeline
- Immutable at translation runtime
- Not committed to git (gitignored)
- Versioned via manifest checksums
### 2.4 Tools Modules (FROZEN)

| Directory | Role |
|-----------|------|
| `tools/legacy_pipeline_launchers/` | Historical pipeline launch scripts |
| `tools/maintenance/` | Maintenance utilities |
| `tools/one_shots/` | One-shot stage application scripts |
| `tools/provider_controls/` | Provider authorization, invocation, benchmarking |
| `tools/provider_utils/` | Provider setup/verification utilities |
| Rule | Enforcement | Violation Consequence |
|------|-------------|----------------------|
| **No imports from `core/`, `engine/`, `lts/` in knowledge layer** | Static analysis (import graph) | Build failure |
| **No imports from knowledge layer in `core/`, `engine/`, `lts/`** | Static analysis (import graph) | Build failure |
| **No shared modules between layers** | Directory structure audit | Build failure |
| **Knowledge artifacts consumed via read-only interfaces only** | Interface segregation audit | Runtime error |
| **No provider API calls from knowledge layer during translation** | Network monitor / policy check | Immediate halt |