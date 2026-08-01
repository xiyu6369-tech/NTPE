# RM-5.7.1 Character Extraction Capability Audit

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit  
**Created**: 2026-08-02  
**Purpose**: Audit existing character extraction capabilities across all modules to identify gaps for Knowledge Generation Architecture.

---

## 1. Module Inventory

| Module | Path | Type | Status |
|--------|------|------|--------|
| Character Memory Engine v1.0 | `core/character_memory_engine.py` | Extraction + Merge | Active (Offline) |
| Character Memory v2 | `core/character_memory_v2/` | Structured Store + Lifecycle | Active (Offline) |
| Character Resolver | `core/character_resolver.py` | Alias Resolution | Active (Runtime) |
| Character Database | `core/character_database.py` | Database Builder | Active (Offline) |
| Context/Character State | `core/context/character_state.py` | Runtime State | Legacy (Unused) |

---

## 2. Capability Analysis by Module

### 2.1 Character Memory Engine v1.0 (`character_memory_engine.py`)

**Purpose**: Merge multi-volume character auto-candidates, apply overrides, export `character_memory.json` & CSV

**Input Sources**:
- `analysis/*_character_memory_auto.json` (from Document Analyzer)
- `character_override.json` (manual lock table)

**Extraction Capabilities**:
| Capability | Implementation | Quality |
|------------|----------------|---------|
| Multi-volume merge | ✅ `merge_memory()` aggregates by source_name | Good |
| Count/statistics | ✅ total_count, book_count per character | Good |
| Manual override | ✅ `apply_override()` with locked translations | Good |
| Alias tracking | ✅ `aliases` list per character | Basic |
| Status tracking | ✅ `locked`, `status`, `notes` fields | Basic |
| Confidence scoring | ✅ `confidence_score()` based on count/book_count | Heuristic |
| Filtering | ✅ MIN_TOTAL_COUNT=3 threshold | Configurable |

---

### 2.2 Character Memory v2 (`core/character_memory_v2/`)

**Purpose**: Structured character knowledge store with evidence-based lifecycle management

**Schema (models.py)**:
- **FactType**: 13 types (CANONICAL_NAME, NAME_VARIANT, PRONOUN_OR_GENDER_REFERENCE, ROLE_OR_IDENTITY, RELATIONSHIP, ADDRESSING_STYLE, SPEECH_STYLE, PERSONALITY_TRAIT, APPEARANCE, TEMPORAL_STATE, LOCATION_STATE, TERMINOLOGY_PREFERENCE, OTHER)
- **EvidenceType**: 7 types (SOURCE_OBSERVATION, TRANSLATION_OBSERVATION, AI_INFERENCE, HUMAN_APPROVED, HUMAN_REJECTED, HISTORICAL_IMPORT)
- **MemoryRecord**: Immutable with UUID, evidence chain, confidence, approval status, expiry policy
- **ApprovalStatus**: PENDING, APPROVED, REJECTED
- **ExpiryPolicy**: Multiple scopes (NEVER, SEGMENT_SCOPE, SCENE_SCOPE, CHAPTER_SCOPE, SESSION_SCOPE, TIMESTAMP, MANUAL_REVIEW_REQUIRED)

**Store Capabilities (store.py)**:
- Deduplication via fact_key + conflict_key
- Evidence ranking (HUMAN_APPROVED > SOURCE_OBSERVATION > TRANSLATION_OBSERVATION > RULE_DERIVED > AI_INFERENCE > HISTORICAL_IMPORT > HUMAN_REJECTED)
- Conflict detection and resolution (evidence precedence)
- Snapshot versioning for rollback
- Character-scoped context selection with token budgets

---

### 2.3 Character Resolver (`character_resolver.py`)

**Purpose**: Alias resolution with priority-based collision handling for runtime translation

**Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Full name mapping | ✅ MANUAL_LOCKED priority (200) |
| Given name / surname split | ✅ Automatic split with GIVEN_NAME (20) / SURNAME (10) priority |
| Alias management | ✅ add_alias() with kind tracking |
| Collision guard | ✅ RESERVED_ALIAS set + priority-based winner selection |
| Longest-match replacement | ✅ Regex-safe replacement with word boundaries |
| Glossary integration | ✅ `build_alias_index_from_glossary()` |

**Gaps**:
- Runtime-only (no offline extraction)
- No character attribute extraction (traits, relationships)
- Korean/Chinese/English name parsing only
- No evidence tracking

---

### 2.4 Character Database (`character_database.py`)

**Purpose**: Build structured character database with match dictionary for translation

**Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Override loading | ✅ `character_database_override.json` |
| Auto-candidate import | ✅ From `character_memory.json` (v1.0 output) |
| Match dictionary | ✅ Priority-based rules (full_name_ko: 100, single_name_ko: 90, etc.) |
| Regex patterns | ✅ Language-aware word boundaries |
| Multi-language | ✅ ko/en/zh_tw fields per name component |

**Gaps**:
- Downstream consumer of v1.0 output (not independent extraction)
- No fact-type granularity beyond name parts
- No relationship/traits extraction

---

### 2.5 Legacy Context State (`core/context/character_state.py`)

**Status**: **Dead Path** — exists but unused in production (per RM-5.1 GAP_ANALYSIS)
- Simple dict-based state with no extraction capabilities

---

## 3. Schema Coverage vs RM-5.7.0 Requirements

| RM-5.7.0 Schema Field | v1.0 Engine | v2 Store | Resolver | Database | Gap |
|----------------------|-------------|----------|----------|----------|-----|
| id (UUID) | ❌ | ✅ | ❌ | ✅ (CHAR######) | v1.0 missing |
---

## 4. Extraction Pipeline Gaps

### 4.1 Missing Extraction Stages (per RM-5.7.0 Generation Flow)

| Stage | Current State | Required for RM-5.7.1 |
|-------|---------------|----------------------|
| Source Ingestion | Document Analyzer → `analysis/*_character_memory_auto.json` | ✅ Exists |
| Extraction Agents | **None** — v1.0 only merges pre-extracted candidates | ❌ Need CharacterExtractor (LLM-based) |
| Validation Engine | v1.0: count threshold only; v2: schema validation only | ❌ Need business rules (CH-001 to CH-005) |
| Review & Approve | Manual override file only | ❌ Need review workflow |
| Compilation | v1.0 + v2 produce separate outputs | ❌ Need unified artifact per schema |

### 4.2 Missing LLM-Based Extraction

No module currently performs **LLM-based character extraction from source text**. The Document Analyzer (referenced but not audited here) produces the `*_character_memory_auto.json` files, but its implementation is not in the audited modules.

---

## 5. Identified Gaps Summary

| Gap ID | Category | Description | Severity |
|--------|----------|-------------|----------|
| CHAR-001 | Schema | v1.0 engine lacks UUID, schema_version, timestamps, source_refs | High |
| CHAR-002 | Schema | v1.0 engine lacks fact-type granularity (traits, relationships, etc.) | High |
| CHAR-003 | Extraction | No LLM-based extraction agent for character attributes | Critical |
| CHAR-004 | Extraction | No evidence chain at segment level (only book-level) | High |
| CHAR-005 | Pipeline | No validation engine with business rules (CH-001 to CH-005) | High |
| CHAR-006 | Pipeline | No review/approval workflow (only manual override file) | Medium |
| CHAR-007 | Integration | v1.0 and v2 stores are disconnected, different schemas | High |
| CHAR-008 | Runtime | v2 store designed for runtime context, not offline generation | Medium |
| CHAR-009 | Coverage | No cultivation_realm / power system tracking (xianxia genre) | Medium |
| CHAR-010 | Coverage | No character arc / temporal progression tracking | Medium |

---

## 6. Recommendations

### Immediate (RM-5.7.1 Scope - Documentation Only)
1. Document all gaps in this audit
2. Define extraction agent interface in Generation Flow doc
3. Map v1.0 → v2 schema migration path

### Future Implementation (RM-5.7.2+)
1. **CharacterExtractor Agent**: LLM-based extraction from source text with FactType granularity
2. **Unified Store**: Merge v1.0 merge logic into v2 store with schema migration
3. **Validation Engine**: Implement CH-001 to CH-005 business rules
4. **Review Workflow**: Build review queue with auto-approve thresholds
5. **Evidence Chain**: Segment-level evidence with source_text_hash

---

## 7. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**
- `git diff --check`: Will PASS (new docs only)
- `compileall`: Will PASS (docs only)
| schema_version | ❌ | ✅ (2.0) | ❌ | ✅ (2.0) | v1.0, Resolver |
| domain | ❌ | ✅ (character) | ❌ | ❌ | All |
| created_at/updated_at | ❌ | ✅ | ❌ | ❌ (history only) | v1.0, Resolver, DB |
| source_refs | ❌ (book-level only) | ✅ (evidence chain) | ❌ | ❌ | v1.0, Resolver, DB |
| confidence | ✅ (heuristic) | ✅ (evidence-based) | ❌ | ✅ (fixed 1.0/0.75) | Resolver |
| status | ✅ (locked/auto) | ✅ (PENDING/ACTIVE/REJECTED) | ❌ | ✅ | Resolver |
| name/canonical | ✅ | ✅ (CANONICAL_NAME fact) | ✅ | ✅ | — |
| source_name | ✅ | ✅ (evidence) | ✅ | ✅ | — |
| aliases | ✅ (list) | ✅ (NAME_VARIANT facts) | ✅ (AliasEntry) | ✅ | — |
| role | ❌ | ✅ (ROLE_OR_IDENTITY) | ❌ | ❌ | v1.0, Resolver, DB |
| traits | ❌ | ✅ (PERSONALITY_TRAIT, etc.) | ❌ | ❌ | v1.0, Resolver, DB |
| relationships | ❌ | ✅ (RELATIONSHIP fact) | ❌ | ❌ | v1.0, Resolver, DB |
| arc_summary | ❌ | ❌ | ❌ | ❌ | **All** |
| first_appearance | ❌ (book list) | ❌ | ❌ | ❌ | **All** |
| knowledge_tags | ❌ | ❌ | ❌ | ❌ | **All** |
**Gaps**:
- **No extraction pipeline** — store only, no LLM/document-based extraction agents
- **No integration** with v1.0 engine or Document Analyzer output
- **Runtime only** — designed for translation-time context injection, not offline generation
- **No schema migration** from v1.0 format
**Output Artifacts**:
- `memory/character_memory.json` - full character database
- `memory/character_memory.csv` - tabular export
- `memory/character_memory_report.txt` - human-readable report

**Gaps**:
- No structured fact types (only name/translation/aliases)
- No evidence citations (source references only at book level)
- No relationship modeling between characters
- No personality/physical trait extraction
- No cultivation realm / power system tracking
- No temporal state tracking (character arcs)