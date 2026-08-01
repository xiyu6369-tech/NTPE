# RM-5.7.1 Style Knowledge Capability Audit

**Baseline**: RM-5.7.0 Knowledge Generation Architecture Baseline  
**Version**: RM-5.7.1  
**Status**: Capability Audit  
**Created**: 2026-08-02  
**Purpose**: Audit existing style knowledge extraction capabilities across all modules to identify gaps for Knowledge Generation Architecture.

---

## 1. Module Inventory

| Module | Path | Type | Status |
|--------|------|------|--------|
| Translation Naturalness | `core/translation_naturalness/` | Style Guards + Canonicalization | Active (Runtime) |
| Prompt Intelligence | `core/translation_engine/prompt_intelligence.py` | Text Profile + Directives | Active (Runtime) |
| Context Intelligence | `core/translation_engine/context_intelligence.py` | Context Profile + Tone | Active (Runtime) |
| Voice Register Guard | `core/translation_naturalness/voice_register_guard.py` | Voice/Register Consistency | Active (Runtime) |
| Hallucination Guard | `core/translation_naturalness/hallucination_guard.py` | Factuality Guard | Active (Runtime) |
| Collocation Guard | `core/translation_naturalness/collocation_guard.py` | Collocation Repair | Active (Runtime) |

---

## 2. Capability Analysis by Module

### 2.1 Translation Naturalness Suite

**Components**:
| Module | Capability | Implementation |
|--------|------------|----------------|
| `canonicalizer.py` | Term canonicalization | Rule-based term normalization |
| `collocation_guard.py` | Collocation repair/warnings | 7 safe replacements + 3 warning phrases |
| `freeze.py` | Translation freezing | Deterministic term locking |
| `hallucination_guard.py` | Factuality checking | Transport/island/duration specificity |
---

### 2.2 Voice Register Guard (`voice_register_guard.py`)

**Detection Capabilities**:
| Issue Code | Detection Method |
|------------|------------------|
| HONORIFIC_REGISTER_DRIFT | Same speaker: 您 + 你 in adjacent lines |
| CHARACTER_VOICE_DRIFT | Formal + slang in same speaker lines |
| NARRATIVE_VIEWPOINT_DRIFT | 3rd→1st person shift without source evidence |
| ERA_INAPPROPRIATE_EXPRESSION | Modern terms in historical profile |
| UNSUPPORTED_EMOTIONAL_AMPLIFICATION | Strong emotion terms without source support |
| NARRATIVE_REGISTER_DRIFT | Formal→colloquial shift in narration |
| DIALOGUE_NARRATION_REGISTER_MIX | (mapped to DIALOGUE_NARRATION_SEPARATION) |

**Gaps**:
- Keyword/pattern-based only
- No positive style extraction (what IS the style?)
- No speaker style profiling across volumes
- No learning from human-approved translations

---

### 2.3 Hallucination Guard (`hallucination_guard.py`)

**Detection Capabilities**:
| Detector | Checks |
|----------|--------|
| transport_specificity | 5 vehicle types with Korean aliases |
| named_island | Named island vs generic island forms |
| explicit_duration | 1-10 day/hour counts with Korean alias table |

**Gaps**:
- Fixed domain list only
- No style knowledge extraction
- Purely defensive (blocking), not constructive

---

### 2.4 Collocation Guard (`collocation_guard.py`)
---

### 2.5 Prompt Intelligence (`prompt_intelligence.py`)

**Style Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Text profile detection | ✅ `detect_text_profile()` → literary/dialogue_heavy/narration_heavy/formal/general |
| Profile directives | ✅ `build_quality_directives()` with 5 profiles × specific guidance |
| Prompt injection | ✅ `_inject_directives()` adds intelligence block |

**Gaps**:
- Classification only (no extraction)
- Profiles are coarse (5 categories)
- No author/style fingerprint persistence

---

### 2.6 Context Intelligence (`context_intelligence.py`)

**Style Capabilities**:
| Capability | Implementation |
|------------|----------------|
| Context profile | ✅ `detect_context_profile()` → dialogue_heavy/narration_heavy/descriptive/tension/neutral |
| Tone detection | ✅ `_detect_tone()` → tense/restrained/heated/atmospheric/neutral |
| Naturalness warnings | ✅ `detect_naturalness_warnings()` pattern-based |

**Gaps**:
- Runtime analysis only
- No style knowledge persistence

---

## 3. Schema Coverage vs RM-5.7.0 Requirements

| RM-5.7.0 Schema Field | Naturalness | Voice Guard | Prompt Intel | Context Intel | Gap |
|----------------------|-------------|-------------|--------------|---------------|-----|
| id (UUID) | ❌ | ❌ | ❌ | ❌ | **All** |
| schema_version | ❌ | ❌ | ❌ | ❌ | **All** |
| domain | ❌ | ❌ | ❌ | ❌ | **All** |
| created_at/updated_at | ❌ | ❌ | ❌ | ❌ | **All** |
| source_refs | ❌ | ❌ | ❌ | ❌ | **All** |
| confidence | ❌ | ✅ (per-issue) | ❌ | ❌ | Naturalness, Prompt, Context |
| style_fingerprint | ❌ | ❌ | ❌ | ❌ | **All** |
| author_profile | ❌ | ❌ | ❌ | ❌ | **All** |
| genre_profile | ❌ | ❌ | ❌ | ❌ | **All** |
| register_rules | ❌ (hardcoded) | ❌ (hardcoded) | ✅ (directives) | ❌ | Naturalness, Voice |
| collocation_patterns | ❌ (7 fixed) | ❌ | ❌ | ❌ | Voice, Prompt, Context |
| forbidden_patterns | ❌ (hardcoded) | ❌ (hardcoded) | ❌ | ❌ | Naturalness, Voice |
| positive_patterns | ❌ | ❌ | ❌ | ❌ | **All** |
| translation_preferences | ❌ | ❌ | ❌ | ❌ | **All** |

---

## 4. Extraction Pipeline Gaps

| Stage | Current State | Required |
|-------|---------------|----------|
| Source Ingestion | No style ingestion | ❌ Need full-volume style analysis |
| Extraction Agents | **None** — all runtime guards | ❌ Need StyleExtractor (LLM-based) |
| Validation Engine | Guards only (defensive) | ❌ Need constructive style validation |
| Review & Approve | None | ❌ Need style review workflow |
| Compilation | No style artifacts produced | ❌ Need offline compilation to style.schema.json |

---

## 5. Identified Gaps Summary

| Gap ID | Category | Description | Severity |
|--------|----------|-------------|----------|
| STYLE-001 | Schema | No style.schema.json exists; no style artifacts produced | Critical |
| STYLE-002 | Extraction | No LLM-based style/profile extraction from source | Critical |
| STYLE-003 | Extraction | No author style fingerprinting across volumes | High |
| STYLE-004 | Extraction | No genre-specific style modeling | High |
| STYLE-005 | Coverage | Only defensive guards (blocking), no positive patterns | High |
| STYLE-006 | Coverage | No collocation/phrase learning from approved translations | Medium |
| STYLE-007 | Pipeline | No validation engine with business rules (ST-001 to ST-005) | High |
| STYLE-008 | Integration | 6 disconnected runtime modules | Medium |

---

## 6. Recommendations

### Immediate (RM-5.7.1)
1. Document that NO style extraction exists — only runtime guards
2. Define StyleExtractor agent interface (author + genre profiling)
3. Plan style.schema.json creation

### Future (RM-5.7.2+)
1. **StyleExtractor Agent**: LLM-based author/genre style profiling from source + approved translations
2. **Positive Pattern Mining**: Learn collocations/register from human-approved data
3. **Validation Engine**: Implement ST-001 to ST-005 (style consistency, register, etc.)
4. **Artifact Compilation**: Produce style.json per schema
5. **Unified Naturalness Suite**: Merge 6 modules into single style engine

---

## 7. Validation

- Production Code Modified: **0** (audit only)
- Provider Requests: **0**
- Network Requests: **0**

**Capabilities**:
| Type | Count | Examples |
|------|-------|----------|
| Safe replacements | 7 | "若要是觸怒了他" → "要是惹怒了他" |
| Warning phrases | 3 | "嘔了一口氣" → AMBIGUOUS_BREATH_ACTION |

**Gaps**:
- Tiny fixed list
- No style pattern learning
- No genre-specific collocations
| `policy.py` | Naturalness policy | Configuration flags |
| `voice_register_guard.py` | Voice/register consistency | 7 issue codes with discipline mapping |

**Gaps**:
- **All runtime-only** — no offline extraction
- **Rule-based only** — no LLM-based style learning
- **Detection/repair only** — no style profile extraction from source
- No author style fingerprinting
- No genre-specific style modeling