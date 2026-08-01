# RM-5.7.1 Narrative Knowledge Capability Audit

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit  
**Created**: 2026-08-02  
**Purpose**: Audit existing narrative knowledge extraction capabilities across all modules to identify gaps for Knowledge Generation Architecture.

---

## 1. Module Inventory

| Module | Path | Type | Status |
|--------|------|------|--------|
| Context Scene Memory v2 | `core/context_scene_memory/models.py` | Plot/Event types defined | Active (Offline) |
| Context Intelligence | `core/translation_engine/context_intelligence.py` | Runtime narrative_state | Active (Runtime) |
| Prompt Intelligence | `core/translation_engine/prompt_intelligence.py` | Text profile detection | Active (Runtime) |
| Translation Quality v7.2 | `core/translation_quality_integration_v72/` | Quality integration | Active (Runtime) |

---

## 2. Capability Analysis by Module

### 2.1 Context Scene Memory v2 — Narrative Types

**Schema Coverage (models.py)**:
---

### 2.2 Context Intelligence (`context_intelligence.py`)

**Narrative Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Narrative state detection | ✅ `_detect_narrative_state()` → continuing_scene/current_scene/empty |
| Previous text summarization | ✅ `_summarize_previous()` (last 180 chars) |
| Tone detection | ✅ `_detect_tone()` → tense/restrained/heated/atmospheric/neutral |

**Gaps**:
- No plot point extraction
- No timeline construction
- No world rule extraction
- No character milestone tracking
- Very limited (180-char summary only)

---

### 2.3 Prompt Intelligence (`prompt_intelligence.py`)

**Narrative Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Text profile detection | ✅ `detect_text_profile()` → literary/dialogue_heavy/narration_heavy/formal/general |
| Profile-aware directives | ✅ `build_quality_directives()` with profile-specific guidance |

**Gaps**:
- Classification only (no extraction)
- No narrative structure analysis
- No plot/timeline/world knowledge extraction

---
---

## 3. Schema Coverage vs RM-5.7.0 Requirements

| RM-5.7.0 Schema Field | Scene Memory v2 | Context Intel | Prompt Intel | Quality v7.2 | Gap |
|----------------------|-----------------|---------------|--------------|--------------|-----|
| **PlotPoint** |
| plot_id (PP-\\d+) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| title | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| type (enum) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| description | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| affected_characters | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| prerequisite/consequence | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| timeline_position | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| **Timeline** |
| timeline_id (TL-\\d+) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| events (position+type+desc) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| **WorldRule** |
| rule_id (WR-\\d+) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| category (enum) | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| constraints/exceptions | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |
| source_volume | ✅ | ❌ | ❌ | ❌ | Intel, Prompt, Quality |

---

## 4. Extraction Pipeline Gaps

| Stage | Current State | Required |
|-------|---------------|----------|
| Source Ingestion | No dedicated narrative ingestion | ❌ Need full-volume analysis pipeline |
| Extraction Agents | **None** — types defined only | ❌ Need NarrativeExtractor (LLM-based) |
| Validation Engine | Schema validation only | ❌ Need business rules (NR-001 to NR-004) |
| Review & Approve | None | ❌ Need review workflow |
| Compilation | Types exist but no artifacts produced | ❌ Need offline compilation |

---

## 5. Identified Gaps Summary

| Gap ID | Category | Description | Severity |
|--------|----------|-------------|----------|
| NARR-001 | Schema | Types defined in Scene Memory but no narrative.schema.json | High |
| NARR-002 | Extraction | No LLM-based plot point extraction | Critical |
| NARR-003 | Extraction | No timeline construction from source | Critical |
| NARR-004 | Extraction | No world rule extraction (cultivation systems, etc.) | Critical |
| NARR-005 | Extraction | No character milestone tracking | High |
| NARR-006 | Pipeline | No validation engine with business rules | High |
| NARR-007 | Integration | Narrative types scattered across modules | Medium |

---

## 6. Recommendations

### Immediate (RM-5.7.1)
1. Document that narrative types exist in Scene Memory v2 but are unused
2. Define NarrativeExtractor agent interface (separate from SceneExtractor)
3. Plan narrative.schema.json creation from existing type definitions

### Future (RM-5.7.2+)
1. **NarrativeExtractor Agent**: Full-volume LLM analysis for plot/timeline/world
2. **Validation Engine**: Implement NR-001 to NR-004
3. **Review Workflow**: Narrative knowledge review queue
4. **Artifact Compilation**: Produce narrative.json per schema

---

## 7. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**

### 2.4 Translation Quality Integration v7.2

**Narrative Capabilities**:
- Quality integration flags for character/context/scene/naturalness
- Prompt budget allocation for scene_tokens (192) and naturalness_tokens (192)
- Selection fingerprint for deterministic context selection

**Gaps**:
- Runtime integration only
- No offline narrative knowledge generation
- **PlotPoint**: plot_id (PP-\\d+), title, type (inciting/rising/climax/falling/resolution/revelation/twist/setup), description, affected_characters, prerequisite_plots, consequence_plots, timeline_position
- **Timeline**: timeline_id (TL-\\d+), name, events (position, event_id, event_type, description)
- **WorldRule**: rule_id (WR-\\d+), category (cultivation_system/magic_system/political_structure/geography/history/technology/social_custom), name, description, constraints, exceptions, source_volume

**Gaps**:
- **Types defined but NO extraction pipeline** — store only
- **No scene-level extraction** (Scene type exists but separate)
- **No integration** with source text analysis
- **Runtime-oriented** — designed for context injection during translation