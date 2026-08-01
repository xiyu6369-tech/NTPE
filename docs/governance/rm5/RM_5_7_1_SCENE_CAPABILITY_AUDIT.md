# RM-5.7.1 Scene Memory Capability Audit

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit  
**Created**: 2026-08-02  
**Purpose**: Audit existing scene memory capabilities across all modules to identify gaps for Knowledge Generation Architecture.

---

## 1. Module Inventory

| Module | Path | Type | Status |
|--------|------|------|--------|
| Context Scene Memory v2 | `core/context_scene_memory/` | Structured Store + Lifecycle | Active (Offline) |
| Context/Scene State | `core/context/scene_state.py` | Runtime State | Legacy (Unused) |
| Context Intelligence | `core/translation_engine/context_intelligence.py` | Runtime Analysis | Active (Runtime) |

---

## 2. Capability Analysis by Module

### 2.1 Context Scene Memory v2 (`core/context_scene_memory/`)

**Purpose**: Structured scene/context knowledge store with evidence-based lifecycle management

**Schema (models.py)**:
- **ContextType**: 15 types (PREVIOUS_TRANSLATION_EXCERPT, SOURCE_CONTEXT_EXCERPT, SCENE_SUMMARY, EVENT_STATE, TEMPORAL_STATE, LOCATION_STATE, SPEAKER_STATE, POINT_OF_VIEW, RELATIONSHIP_STATE, ADDRESSING_STATE, UNRESOLVED_REFERENCE, TERMINOLOGY_STATE, CONTINUITY_NOTE, OTHER)
- **EvidenceType**: 7 types (SOURCE_OBSERVATION, TRANSLATION_OBSERVATION, RULE_DERIVED, AI_INFERENCE, HUMAN_APPROVED, HUMAN_REJECTED, HISTORICAL_IMPORT)
- **ContextMemoryRecord**: Immutable with context_id, chapter_id, scene_id, context_type, value, evidence, confidence, expiry
- **SceneMemoryRecord**: Scene-level aggregation with participants, location, time_state, active_speaker, POV, event_state, unresolved_references
- **SceneParticipant**: character_id, status (PRESENT/MENTIONED/ABSENT/EXITED), role
- **UnresolvedReference**: surface_form, reference_type, candidate_targets, resolution_status
- **BoundaryType**: SAME_SCENE, SCENE_TRANSITION, CHAPTER_TRANSITION, etc.

**Store Capabilities (store.py)**:
- Deduplication via fact_key (chapter+scene+type+value) + conflict_key
---

### 2.2 Legacy Scene State (`core/context/scene_state.py`)

**Status**: **Dead Path** — exists but unused in production (per RM-5.1 GAP_ANALYSIS)

**Capabilities**:
- Simple keyword-based location detection (Korean → Chinese mapping)
- Weather/time/mood detection via keyword matching
- Object tracking with fixed Korean→Chinese mapping
- Max 12 objects tracked

**Gaps**:
- Hardcoded keyword mappings only
- No scene boundary detection
- No participant tracking
- No evidence chain
- No schema versioning

---

### 2.3 Context Intelligence (`core/translation_engine/context_intelligence.py`)

**Purpose**: Runtime context analysis for prompt enhancement

**Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Context profile detection | ✅ `detect_context_profile()` → dialogue_heavy/narration_heavy/descriptive/tension/neutral |
| Context snapshot | ✅ `build_context_snapshot()` with characters, locations, tone, narrative_state |
| Entity extraction | ✅ `_extract_entities()` regex-based Chinese name extraction |
| Location extraction | ✅ `_extract_locations()` keyword-based |
| Tone detection | ✅ `_detect_tone()` based on profile + keywords |
| Narrative state | ✅ `_detect_narrative_state()` continuing/current/empty |
---

## 3. Schema Coverage vs RM-5.7.0 Requirements

| RM-5.7.0 Schema Field | Scene Memory v2 | Legacy Scene State | Context Intel | Gap |
|----------------------|-----------------|-------------------|---------------|-----|
| id (UUID) | ✅ (context_id, scene_id) | ❌ | ❌ | Legacy, Intel |
| schema_version | ✅ (1.0) | ❌ | ❌ | Legacy, Intel |
| domain | ✅ (narrative) | ❌ | ❌ | Legacy, Intel |
| created_at/updated_at | ✅ | ❌ | ❌ | Legacy, Intel |
| source_refs | ✅ (evidence chain) | ❌ | ❌ | Legacy, Intel |
| confidence | ✅ | ❌ | ❌ | Legacy, Intel |
| status | ✅ (RecordStatus) | ❌ | ❌ | Legacy, Intel |
| scene_id | ✅ (SC-\\d+) | ❌ | ❌ | Legacy, Intel |
| title | ❌ | ❌ | ❌ | **All** |
| volume/chapter_range | ✅ (chapter_id) | ❌ | ❌ | Legacy, Intel |
| location | ✅ | ✅ (keyword-based) | ✅ (keyword-based) | — |
| time_of_day | ✅ (time_state) | ✅ (keyword-based) | ❌ | Intel |
| participants | ✅ (SceneParticipant) | ❌ | ✅ (entity extraction) | Legacy |
| plot_points | ❌ | ❌ | ❌ | **All** |
| summary | ❌ | ❌ | ❌ | **All** |
| tone | ❌ | ✅ (mood) | ✅ | Legacy |
| unresolved_refs | ✅ | ❌ | ❌ | Legacy, Intel |

---

## 4. Extraction Pipeline Gaps

| Stage | Current State | Required |
|-------|---------------|----------|
| Source Ingestion | No dedicated scene ingestion | ❌ Need scene boundary detection from source |
| Extraction Agents | **None** — store only | ❌ Need SceneExtractor (LLM-based) |
| Validation Engine | Schema validation only | ❌ Need business rules (NR-001 to NR-004) |
| Review & Approve | None | ❌ Need review workflow |
| Compilation | Store produces runtime artifacts only | ❌ Need offline compilation to narrative.schema.json |

---

## 5. Identified Gaps Summary

| Gap ID | Category | Description | Severity |
|--------|----------|-------------|----------|
| SCENE-001 | Schema | Missing title, summary, plot_points, tone fields | High |
| SCENE-002 | Extraction | No LLM-based scene boundary detection | Critical |
| SCENE-003 | Extraction | No participant/role extraction from source | High |
| SCENE-004 | Integration | Three disconnected modules (v2 store, legacy, context_intel) | High |
| SCENE-005 | Pipeline | No validation engine with business rules | High |
| SCENE-006 | Coverage | No narrative plot point extraction | Medium |
| SCENE-007 | Coverage | No world rule extraction | Medium |

---

## 6. Recommendations

### Immediate (RM-5.7.1)
1. Document gaps and disconnected modules
2. Define SceneExtractor agent interface

### Future (RM-5.7.2+)
1. **SceneExtractor Agent**: LLM-based scene boundary + attribute extraction
2. **Unified Store**: Merge context_scene_memory + context_intelligence capabilities
3. **Validation Engine**: Implement NR-001 to NR-004
4. **PlotExtractor**: Separate agent for plot_point/timeline/world_rule (narrative domain)

---

## 7. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**
| Naturalness warnings | ✅ `detect_naturalness_warnings()` pattern-based |
| Prompt injection | ✅ `_inject_context_directives()` adds context intelligence block |

**Gaps**:
- Runtime-only analysis (no offline extraction)
- Keyword/regex based (no LLM semantic understanding)
- No scene boundary detection
- No persistent scene memory across chunks
- No integration with context_scene_memory store
- Evidence ranking (HUMAN_APPROVED > SOURCE_OBSERVATION > TRANSLATION_OBSERVATION > RULE_DERIVED > AI_INFERENCE > HISTORICAL_IMPORT > HUMAN_REJECTED)
- Singular context types (location, time, speaker, POV, etc.) enforce single active value
- Conflict detection and resolution (evidence precedence)
- Scene memory creation with evidence
- Snapshot versioning

**Gaps**:
- **No extraction pipeline** — store only, no LLM/document-based scene extraction agents
- **No integration** with Document Analyzer or translation runtime
- **Runtime-oriented** — designed for translation-time context injection
- **No schema migration** path from legacy scene_state.py