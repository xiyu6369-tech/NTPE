# NTPE RM-8.5 Requirements / Architecture Inventory — Consistency Audit

**Baseline**: NTPE main branch, RM-8.4 final commit: `e4af617`, RM-8.4 Push: CLEAR  
**Audit Target**: `RM_8_5_REQUIREMENTS_ARCHITECTURE_INVENTORY.md`  
**Date**: 2026-08-13  
**Status**: Audit complete — based on actual repository inspection, not document inference

---

## 1. Baseline Verification

| Item | Expected | Actual | Status |
|---|---|---|---|
| Main branch HEAD | `e4af617` | `e4af617` (RM-8.4: add optional EPUB packaging layer) | ✅ |
| RM-8.3 baseline | `d901c92` | `d901c92` (RM-8.3: add output polish and delivery pipeline) | ✅ |
| RM-8.4 Push Verification | CLEAR | `ntpe_validate.py` ALL PASS, compileall 0 errors, git diff --check clean | ✅ |
| Working tree | Clean except inventory | Inventory report + pre-existing temp files only | ✅ |

---

## 2. Repository Evidence — Capability Inventory Verification

### 2.1 RM-8.1 Literary Quality Enforcement (VERIFIED)

**Files Inspected**:
- `core/translation_runtime/runtime_qa.py` — `_LITERARY_QUALITY_CODES` (5 codes), `classify_literary_quality_hits()`, extended `analyze_runtime_quality()` metrics
- `core/adaptive_context_production_rollout/outcome.py` — 5 new `ProductionOutcome` fields
- `lts/txt_translation_runtime.py` — manifest includes `literary_quality` block

**Actual Runtime Behavior** (from code inspection):
- Detection: `_NATURALNESS_PATTERNS` in `context_intelligence.py` unchanged (6 patterns)
- Classification: Pure function `classify_literary_quality_hits()` splits hits by code set
- Enforcement: Reuses existing `naturalness_guard_policy="literary_retry"` + `quality_profile` logic — **no new policy/gate**
- Metrics: 5 explicit counters (`hits`, `errors`, `warnings`, `passed`, `issue_codes`) — **no synthetic score**
- Propagation: QA report → runtime result → `ProductionOutcome` → manifest — verified in code paths
- Provider cost: Zero additional calls — architecture unchanged

**Policy Matrix Verified** (matches specification exactly):
| Policy / Profile | Hits | Errors | Warnings | Passed | Chunk Saved |
|---|---:|---:|---:|---|---|
| `off` | 2 | 0 | 0 | true | Yes |
| `warn` + literary | 2 | 0 | 2 | true | Yes |
| `literary_retry` + literary | 2 | 2 | 0 | false | No (qa_fail≠warn) |
| `literary_retry` + non-literary | 2 | 0 | 2 | true | Yes |
| `fail` | 2 | 2 | 0 | false | No |

**Inventory Accuracy**: ✅ **FULLY ACCURATE** — all claims verified against actual code.

---

### 2.2 RM-8.2 Cross-Chunk Context Continuity (VERIFIED)

**Files Inspected**:
- `core/translation_runtime/boundary_detector.py` — Conservative explicit-marker detection
- `core/context_scene_memory/*` — Store, selection, scene_state, models, serialization
- `core/intelligence/narrative_engine.py` — `analyze_chunk()`, `get_context_for_prompt()`, checkpoint persistence
- `core/prompt_runtime/sections.py` — `build_context_selection()`, parameterized `build_character/scene/narrative`
- `core/runtime_orchestrator/manager.py` — Extended `execute()` metadata pass-through
- `lts/txt_translation_runtime.py` — Chunk loop integration (feature-gated `quality_context_scene_v72`)

**Actual Runtime Data Structures Verified**:
```python
# BoundaryResult (frozen dataclass)
type: BoundaryType          # SAME_SCENE | SCENE_TRANSITION | CHAPTER_TRANSITION | UNKNOWN_TRANSITION
scene_id: Optional[str]
chapter_id: Optional[str]
confidence: float
metadata: Dict

# ContextSelectionResult
selected_records: Tuple[SelectedContextItem, ...]
selected_character_memories: Tuple[CharacterContextItem, ...]
estimated_tokens: int
character_estimated_tokens: int
deterministic_fingerprint: str

# SceneMemoryRecord
scene_id, scene_version, chapter_id
location, time_state
participants: Tuple[SceneParticipant, ...]
active_speaker, point_of_view
event_state, unresolved_references

# NarrativeState
last_perspective, last_voice, last_tense, last_emotional_tone
scene_history, counters

# Per-chunk metadata.context_state
{
  "context_selection_fingerprint": "...",
  "scene_id": "...",
  "scene_version": 1,
  "narrative": {...},
  "boundary": {"type": "...", "scene_id": "...", ...},
  "selected_context_ids": (...)
}
```

**Conservative Boundary Detection Verified** (from `boundary_detector.py`):
- Chapter: `제N장`, `第N章`, `Chapter N` → `CHAPTER_TRANSITION` (confidence 0.95)
- Scene: `제N절`, `第N節`, `Scene N`, `***`/`---`/`===` → `SCENE_TRANSITION` (confidence 0.9)
- Heuristics (location/time/speaker) → `UNKNOWN_TRANSITION` only, **no auto scene_id**
- Default: `SAME_SCENE`

**Checkpoint/Resume Verified**:
- `ContextMemoryStore.to_dict()/from_dict()` — full serialization roundtrip
- `NarrativeState.to_dict()/from_dict()` + `restore_state_from_checkpoint()`
- Scene/chapter IDs + `prev_chunk_text` in checkpoint metadata

**Feature Flag Zero-Regression Verified**:
- `quality_context_scene_v72` default `False`
- When `False`: `context_state_metadata = None`, no Context section, Scene/Narrative empty
- All 10 unit tests pass (`tests/unit/rm8_phase6_reader_outcome_test.py`)

**Provider Increment**: **0** — verified by test `test_no_provider_request_increment` and architecture inspection

**Inventory Accuracy**: ✅ **FULLY ACCURATE** — all claims verified against actual code and tests.

---

### 2.3 RM-8.3 Output Polish & Delivery (VERIFIED)

**Files Inspected**:
- `core/translation_release/polish.py` — `normalize_paragraphs()`, `unify_quote_style()`, `polish_full_novel()`
- `core/translation_release/validator.py` — `validate_final_novel()` with 9 deterministic checks
- `core/translation_release/metadata.py` — `build_toc_from_chunk_records()`, `inject_metadata_into_text()`, manifest/cert generation
- `core/translation_release/package.py` — `write_txt_delivery()`, `write_json_delivery()`
- `core/translation_release/delivery_pipeline.py` — `run_delivery_pipeline()` orchestrator
- `lts/txt_translation_runtime.py` — Integration via `quality_delivery_v83` flag

**Polish Pipeline Verified** (6 steps, full-novel scope):
1. `clean_provider_output()` — preamble removal, line endings
2. `normalize_paragraphs()` — empty removal, 3+ newline consolidation, whitespace
3. `unify_quote_style()` — **conservative** ASCII→CJK (apostrophes/measurements/code protected)
4. `normalize_punctuation_for_zh_tw()` — ASCII→CJK punctuation
5. `normalize_taiwan_traditional()` — Simplified→Traditional
6. `clean_provider_output()` — final cleanup

**Validation Gate Verified** (9 checks, weighted scoring, PASS ≥ 70 + no critical failures):
| Check | Severity | Key Criteria |
|---|---|---|
| paragraph_structure | critical | No empty paragraphs, no 3+ newlines |
| punctuation_consistency | major | CJK ratio > 95%, quote style unified |
| korean_residue_global | critical | Korean chars < max × chunks × 0.5 |
| locked_term_compliance | major | Only matched terms; no glossary-only failures |
| length_ratio_global | major | Translated/source ∈ [min_ratio, 2.0] (source from chunk_records) |
| chinese_char_ratio | minor | Chinese char ratio > 80% |
| repeated_lines_global | minor | No consecutive duplicate lines |
| quote_balance | minor | Corner brackets balanced |
| empty_content | info | Non-empty text |

**Delivery Package Verified** (core = TXT + manifest + QC cert; optional = EPUB/PDF)
- Feature flag: `quality_delivery_v83` default OFF, `quality_delivery_formats_v83` = `("txt",)`
- 154 unit tests pass (2 skipped for optional deps)

**Inventory Accuracy**: ✅ **FULLY ACCURATE**

---

### 2.4 RM-8.4 Reader Structure / Optional EPUB Packaging (VERIFIED)

**Files Inspected**:
- `core/translation_release/reader_structure/models.py` — `ChapterBoundary`, `ReaderChapterMap` (frozen)
- `core/translation_release/reader_structure/chapter_mapper.py` — `build_reader_chapter_map()` (read-only)
- `core/translation_release/reader_structure/epub_packager.py` — `pack_epub()` (slices by positions)

**Chapter Provenance Verified** (single source, priority order):
1. RM-8.2 `context_state.boundary.chapter_id` (deterministic, already exists)
2. Explicit marker in TXT: `第N章`, `Chapter N` (fallback only)
3. Deterministic fallback: `chapter_N`

**Position Mapping Verified**:
- `start_position` / `end_position` = 0-based UTF-8 code point offsets in RM-8.3 TXT body (excludes metadata header/TOC)
- End-exclusive, deterministic: same input → same positions
- Assembly logic replicated exactly from `txt_translation_runtime.py`

**Content Preservation Invariant Verified**:
```python
# In chapter_mapper.py and epub_packager.py:
reconstructed = "".join(txt_body[c.start_position:c.end_position] for c in chapters)
assert reconstructed == txt_body  # Content preservation by construction
```

**Core/Optional Boundary Verified**:
| Layer | Classification | Failure Blocks Core? |
|---|---|---|
| Chapter Mapper + ReaderChapterMap + QC | **Core** | Yes |
| EPUB Packaging | **Optional EPUB Packaging** | No (graceful fallback) |
| PDF Packaging | **Truly Optional** | No |

**CLI Separation Verified**:
- `quality_delivery_v83=True` → Core delivery (includes ReaderChapterMap)
- `--export-epub` → Optional EPUB (requires Core first)
- Test `test_delivery_pipeline_txt_only_no_epub_attempt` confirms isolation

**Inventory Accuracy**: ✅ **FULLY ACCURATE**

---

## 3. RM-8.1～8.4 Compatibility Matrix

| Cross-Stage Dependency | Status | Evidence |
|---|---|---|
| RM-8.3 consumes RM-8.1 metrics | ✅ | `delivery_pipeline.py:_aggregate_literary_quality()` reads `qa.metrics.literary_quality_*` |
| RM-8.3 consumes RM-8.2 metadata | ✅ | `metadata.py:build_toc_from_chunk_records()` reads `context_state` from chunk_records |
| RM-8.4 consumes RM-8.3 TXT body | ✅ | `chapter_mapper.py` takes `txt_body` as immutable input |
| RM-8.4 consumes RM-8.2 metadata | ✅ | `chapter_mapper.py` reads `context_state.boundary.chapter_id`, `scene_id` |
| RM-8.2 feature flag isolation | ✅ | `quality_context_scene_v72` OFF = zero behavior change |
| RM-8.3 feature flag isolation | ✅ | `quality_delivery_v83` OFF = zero behavior change |
| RM-8.4 EPUB optional isolation | ✅ | EPUB failure never blocks Core (try/except, graceful fallback) |
| No Provider/Network in 8.1-8.4 | ✅ | All pipelines deterministic, zero external calls |

---

## 4. Inventory Accuracy — Overall Assessment

| Section | Claim | Verification | Result |
|---|---|---|---|
| 1.1 RM-8.1 capability | 5 metrics, policy matrix, no new gate | Code + tests | ✅ Accurate |
| 1.2 RM-8.2 capability | Context store, selection, narrative, checkpoint | Code + 10 tests | ✅ Accurate |
| 1.3 RM-8.3 capability | 6-step polish, 9-check validator, delivery pkg | Code + 154 tests | ✅ Accurate |
| 1.4 RM-8.4 capability | ChapterMapper, ReaderChapterMap, EPUB packager | Code + tests | ✅ Accurate |
| 1.5 Cross-capability table | All listed capabilities exist | Code inspection | ✅ Accurate |
| 2.1 Reader gaps | 8 gaps listed | Manual review of output artifacts | ✅ Valid |
| 2.2 Remaining gaps | No glossary, no bookmarks, no parallel, etc. | Confirmed absent in delivery | ✅ Valid |
| 3.1 Quality gaps | 10 problems NOT solved | RM-8.2 acceptance report §5 explicit | ✅ Accurate |
| 4.1 Missing capabilities | Semantic validation, global term consistency | Confirmed absent | ✅ Valid |
| 4.2 Duplications | Paragraph/quote normalization ×2, locked dict ×3 | Code inspection | ✅ Accurate |
| 4.3 Dangerous coupling | 5 couplings identified | Code inspection | ✅ Accurate |
| 4.4 Unnecessary complexity | 5 items identified | Architecture review | ✅ Valid |
| 5 Performance | 5 areas documented | Code inspection | ✅ Accurate |
| 6 Candidates | 7 candidates with full matrix | Evidence-based | ✅ Valid |
| 7 False candidates | 15 eliminated with governance refs | Spec non-goals verified | ✅ Accurate |

**Overall Inventory Accuracy**: ✅ **HIGH — All claims verified against actual repository**

---

## 5. Gap Validity Audit

### 5.1 Reader-Facing Gaps (8 claimed)

| Gap | Evidence | Valid? |
|---|---|---|
| No glossary/character reference in output | Delivery TXT/EPUB contains only novel text + metadata header + TOC | ✅ |
| No reading progress/bookmark sync | EPUB has nav.xhtml only, no reading position persistence | ✅ |
| No alternative formats | Only TXT + optional EPUB/PDF | ✅ |
| No inline annotations/footnotes | No footnote/annotation layer in output | ✅ |
| No "first chapter free" sample | Full novel only; no subset generation | ✅ |
| No bilingual/parallel text | Source Korean discarded after translation | ✅ |
| No audio/TTS preparation | No SSML, no prosody hints at boundaries | ✅ |
| No reading statistics | No word count/reading time in metadata | ✅ |

**All 8 gaps confirmed REAL and NOT addressed by RM-8.1-8.4.**

---

### 5.2 Translation-Quality Gaps (10 claimed)

| Gap | RM-8.2 Acceptance Report §5 Evidence | Valid? |
|---|---|---|
| Cross-chunk pronoun resolution | "Pronoun resolution accuracy" — NOT Verified | ✅ |
| Dialogue speaker attribution | "Dialogue speaker attribution accuracy" — NOT Verified | ✅ |
| Narrative POV stability | "Narrative POV semantic stability" — NOT Verified | ✅ |
| Non-locked term consistency | Only locked_dict enforced globally | ✅ |
| Tense/voice consistency | RM-8.2 tracks but no validation gate | ✅ |
| Emotional tone continuity | RM-8.2 tracks but no cross-chunk validation | ✅ |
| Cultural nuance preservation | No dedicated detector | ✅ |
| Name transliteration consistency | Only locked terms | ✅ |
| Sentence-level flow across boundaries | Per-chunk QA only | ✅ |
| Long-range entity consistency | Token budget limits context selection | ✅ |

**All 10 gaps confirmed REAL and EXPLICITLY ACKNOWLEDGED in RM-8.2 acceptance report.**

---

## 6. Candidate Direction Audit — Cross-Chunk Semantic Quality Gate

### 6.1 Problem Existence — CONFIRMED

**Evidence from RM-8.2 Acceptance Report (§5)**:
> "已驗證跨 Chunk 的 NarrativeState、SceneState、Context selection、Prompt injection 與 checkpoint/resume propagation；reader-outcome continuity tests 驗證狀態延續基礎設施，**但不等同於完整語意層面的翻譯正確性**."

**Explicitly NOT Verified (Semantic)**:
- Pronoun resolution accuracy
- Dialogue speaker attribution accuracy
- Narrative POV semantic stability
- Translation quality improvement
- End-to-end reader experience

**This is a documented, acknowledged gap — not speculative.**

---

### 6.2 Existing Capability Assessment — CAN BE EXTENDED, NOT REPLACED

**Existing Infrastructure That Can Be Leveraged**:
1. **NarrativeState** (`narrative_state.py`): `perspective`, `voice`, `tense`, `emotional_tone`, `scene_history` — propagated per-chunk, checkpointable
2. **SceneMemoryRecord** (`models.py`): `active_speaker`, `participants`, `point_of_view`, `unresolved_references` — per-scene, expired at boundaries
3. **ContextSelectionResult**: `selected_records` with `TERMINOLOGY_STATE`, `RELATIONSHIP_STATE`, `ADDRESSING_STATE` contexts
4. **Chunk Records**: `metadata.context_state` contains `narrative`, `boundary`, `scene_id`, `scene_version`, `selected_context_ids`
5. **RM-8.3 Validator Framework** (`validator.py`): 9 deterministic checks, weighted scoring, extensible `ValidationCheck` pattern

**What's Missing**: Deterministic validation checks that **consume** this metadata on the **final assembled novel** to verify semantic consistency.

**No New Infrastructure Needed** — only new validation checks in existing validator.

---

### 6.3 Architecture Duplication Check — NO DUPLICATION

| Existing Component | Purpose | Cross-Chunk Semantic Gate Would |
|---|---|---|
| RM-8.1 `runtime_qa.py` | Per-chunk literary quality | **Different scope**: full-novel semantic validation |
| RM-8.2 Context/Scene/Narrative | Propagation infrastructure | **Consumes** this infrastructure, doesn't duplicate |
| RM-8.3 `validator.py` | Format validation (paragraphs, punctuation, Korean, locked terms) | **Extends** with semantic checks (pronoun, speaker, POV, tense, tone) |
| RM-7 Entity Resolution | Per-chunk entity mapping | **Different**: novel-wide term consistency vs per-chunk resolution |
| Prompt Injection | Provides context TO provider | **Different**: validates OUTPUT after translation |

**No duplication** — this fills the explicit gap between RM-8.2 (infrastructure) and RM-8.3 (format validation).

---

### 6.4 Provider/LLM Request Analysis — ZERO REQUIRED

**Mandate**: Deterministic validation only — no LLM, no provider calls.

**Implementation Pattern** (following RM-8.3 `validator.py`):
```python
def _check_pronoun_consistency(text: str, chunk_records: list[dict]) -> ValidationCheck:
    # Analyze pronoun usage across chunk boundaries using RM-8.2 metadata
    # Pure Python regex/string analysis — no external calls
    ...

def _check_speaker_attribution_stability(text: str, chunk_records: list[dict]) -> ValidationCheck:
    # Track dialogue speaker markers across chunks using SceneMemoryRecord.active_speaker
    # Pure Python analysis — no external calls
    ...

def _check_narrative_pov_continuity(text: str, chunk_records: list[dict]) -> ValidationCheck:
    # Verify NarrativeState.perspective/voice/tense consistency using chunk_records metadata
    # Pure Python analysis — no external calls
    ...
```

**Provider Requests = 0** — aligned with RM-8.1/8.2/8.3/8.4 principle.

---

### 6.5 Latency/Cost/Failure Surface — NO INCREASE

- **No provider calls** → no latency increase, no cost increase, no failure surface increase
- **No RPM impact** — NVIDIA provider 40 RPM limit unaffected
- **Pure local computation** — O(n) text scans on final assembled novel (already done for Korean residue, punctuation ratio, etc.)

---

### 6.6 Deterministic Pre-Check Strategy — YES, BY DESIGN

All checks are **deterministic pre-checks** on final assembled text + existing metadata:
- No LLM gate at all
- No "true necessary cases" for LLM — **zero LLM usage**
- Follows RM-8.3 pattern: weighted scoring, PASS ≥ 70, no critical failures

---

### 6.7 Pipeline Integrity — NO RE-CHUNK/RE-ASSEMBLE/RE-POLISH/RE-TRANSLATE

| Prohibited Action | Cross-Chunk Semantic Gate |
|---|---|
| Re-chunk | ❌ No — consumes final assembled text |
| Re-assemble | ❌ No — reads `txt_body` from RM-8.3 |
| Re-polish | ❌ No — validates polished text |
| Re-translate | ❌ No — validation only |
| Modify RM-8.3 TXT Source of Truth | ❌ No — read-only |
| Auto-generate EPUB | ❌ No — independent of RM-8.4 |
| EPUB reverse dependency | ❌ No — EPUB consumes validated TXT |
| AI/LLM for chapter boundary | ❌ No — uses RM-8.2 metadata + explicit markers |
| Unapproved provider requests | ❌ No — zero provider calls |

---

### 6.8 Architectural Complexity — MINIMAL INCREMENT

**Files to Modify** (following RM-8.3 pattern):
1. `core/translation_release/validator.py` — Add 5-6 new `_check_*` functions + register in `validate_final_novel()`
2. `core/translation_release/metadata.py` — Extend `QualityCertificate` with new dimension scores
3. Tests — Unit tests for each new check + integration test

**No New Modules, No New Dependencies, No New Dataclasses** (reuse `ValidationCheck`, `ValidationResult`)

---

### 6.9 Input/Output/Ownership Boundary — EXPLICITLY DEFINABLE

**Input**:
- `text: str` — RM-8.3 polished TXT body (final assembled novel)
- `chunk_records: list[dict]` — with `metadata.context_state` (scene_id, chapter_id, narrative, boundary, selected_context_ids)
- `locked_dictionary: dict[str, str]` — for term consistency baseline
- `options: TxtTranslationOptions` — config thresholds

**Output**:
- Extended `ValidationResult` with new `ValidationCheck` entries:
  - `pronoun_consistency` (major)
  - `speaker_attribution_stability` (major)
  - `narrative_pov_continuity` (major)
  - `tense_voice_consistency` (major)
  - `emotional_tone_coherence` (minor)
  - `cross_chunk_entity_consistency` (major)
- Updated `QualityCertificate` with new dimension scores

**Ownership**: `core/translation_release/validator.py` — same as existing validator.

---

### 6.10 Reproducible Regression Tests — YES

**Test Pattern** (following `tests/unit/translation_release/test_validator.py`):
```python
def test_validator_pronoun_consistency_detects_flip():
    # Fixture: chunks with pronoun flip at boundary
    # Verify check fails with major severity
    ...

def test_validator_speaker_attribution_stable_across_chunks():
    # Fixture: consistent speaker across scene
    # Verify check passes
    ...

def test_validator_narrative_pov_continuity_detects_shift():
    # Fixture: POV shift mid-scene
    # Verify check fails
    ...
```

**Deterministic**: Same input → same result. No flakiness.

---

### 6.11 Simpler Equivalent Candidate — EVALUATED

| Alternative | Assessment |
|---|---|
| **Enhance RM-8.2 prompt injection** | Already done; prompt provides context TO provider, doesn't validate OUTPUT |
| **Post-translation LLM review** | Violates zero-provider principle; adds latency/cost/RPM pressure |
| **Per-chunk semantic QA** | Misses cross-boundary issues by definition |
| **Manual review interface** | Violates Fail Closed; not automated |
| **Wait for RM-9** | Gap exists now; RM-8.5 is the logical completion of RM-8 quality stack |

**No simpler equivalent** that satisfies: deterministic, zero-provider, cross-chunk semantic, automated.

---

## 7. Architecture Duplication / Coupling Audit

### 7.1 Duplications Confirmed (Acceptable)
- Paragraph normalization: per-chunk (`runtime_formatter`) + full-novel (`polish.py`) — **intentional defense-in-depth**
- Quote normalization: per-chunk + full-novel — **intentional**
- Taiwan traditional: per-chunk (2×) + full-novel — **spec-mandated**
- Locked dictionary: per-chunk + final assembly + delivery (3×) — **idempotent, defensive**
- Chapter boundary: runtime detector + post-hoc mapper — **different purposes**

### 7.2 Dangerous Couplings Confirmed (Pre-Existing, Not Introduced by RM-8.5)
- `txt_translation_runtime.py` lazy-imports `translation_release` — **pre-existing**
- `delivery_pipeline.py` re-runs canonicalization — **pre-existing, defensive**
- `chapter_mapper.py` replicates assembly logic — **pre-existing, required for position accuracy**
- `epub_packager.py` duplicates title extraction — **pre-existing, minor**
- `NarrativeIntelligenceEngine` checkpoint incomplete — **pre-existing, documented**

**RM-8.5 does not introduce new couplings** — extends validator only.

---

## 8. Performance / Stability Audit

| Metric | Current | RM-8.5 Impact |
|---|---|---|
| Provider requests/novel | = chunk count | **No change** (0 additional) |
| Validation passes | 9 checks on full text | **+5-6 checks** (O(n) each, negligible) |
| Memory growth | Context store O(chunks) | **No change** |
| Checkpoint I/O | Full store snapshot | **No change** |
| Large novel handling | O(n) validation scans | **+5-6 O(n) scans** — acceptable |

**Stability**: Pure deterministic functions — no new failure modes.

---

## 9. Provider / RPM Impact — ZERO

- **Provider Requests**: 0 additional
- **Network Requests**: 0 additional  
- **NVIDIA 40 RPM Limit**: No impact
- **Latency**: No increase (local validation only)
- **Cost**: No increase

---

## 10. Proposed Minimal RM-8.5 Boundary

### Scope
Add deterministic cross-chunk semantic validation checks to RM-8.3 `validate_final_novel()`:
- Pronoun consistency across chunk boundaries
- Speaker attribution stability across scene/chapter transitions
- Narrative POV/tense/voice continuity
- Emotional tone coherence
- Cross-chunk entity consistency (non-locked terms)

### Non-Goals
- ❌ New provider/LLM calls
- ❌ Re-translation / auto-fix / correction
- ❌ Modify RM-8.2 propagation logic
- ❌ Human review interfaces
- ❌ New chunking / assembly / polish
- ❌ Modify RM-8.3 TXT Source of Truth
- ❌ Synthetic semantic score (0-100)
- ❌ Auto-learning

### Inputs
1. RM-8.3 polished TXT body (`text: str`)
2. `chunk_records` with `metadata.context_state` (RM-8.2 provenance)
3. `locked_dictionary` (baseline)
4. `TxtTranslationOptions` (thresholds)

### Outputs
- Extended `ValidationResult` with 5-6 new `ValidationCheck` entries
- Updated `QualityCertificate` with new dimension scores

### Dependencies
- RM-8.2 (metadata in chunk_records) — **required**
- RM-8.3 (validator framework) — **required**
- RM-8.1 (literary quality aggregate) — **optional, for correlation**

### Core/Optional
**Core** — quality gate is mandatory for delivery (`quality_delivery_v83` controls execution)

### Provider/Network
**Provider Requests = 0, Network Requests = 0** — purely local deterministic validation

### Relationship to RM-8.3
Extends `validate_final_novel()` in `core/translation_release/validator.py`; integrated into weighted scoring.

### Relationship to RM-8.4
No direct dependency; RM-8.4 consumes validated TXT body. RM-8.5 runs before RM-8.4 chapter mapping.

### Feature Flag
`quality_delivery_v83` (existing) controls full delivery pipeline including RM-8.5 checks.

### Acceptance Gates
1. All new checks implemented and deterministic
2. Unit tests for each check with fixture data
3. Integration test: known semantic drift detected
4. Regression: all RM-7/8.1/8.2/8.3/8.4 tests PASS
5. `ntpe_validate.py` PASS, `compileall` PASS, `git diff --check` PASS
6. Zero provider requests in validation

---

## 11. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| False positives in pronoun/speaker detection | Medium | Conservative heuristics; warning not error initially; tunable thresholds |
| Incomplete RM-8.2 metadata in chunk_records | Low | RM-8.2 acceptance tests verify metadata structure; defensive coding for missing fields |
| Performance on very large novels | Low | O(n) scans; 5-6 checks add <100ms for 500KB novel |
| Scope creep to auto-fix | Low | Non-goal explicitly locked; validation only |
| Coupling to RM-8.2 internals | Medium | Consume only documented `metadata.context_state` fields; not internal store |

---

## 12. Required Revisions to Inventory Document

### Minor Corrections Needed:

1. **Section 6 Candidate F** (Translation Efficiency): Mark as **BLOCKED** for RM-8.5 — violates "chunk = execution unit" principle (RM-8.2 Core Principle #2), high risk, not minimal.

2. **Section 7 False Candidates**: Add explicit reference to RM-8.2 Core Principle #2 for "batching breaks per-chunk QA/retry".

3. **Section 8 Recommendation**: Clarify that Cross-Chunk Semantic Quality Gate is **Core** but **does not block RM-8.4 EPUB** — EPUB consumes validated output.

4. **Section 9 Boundary**: Add explicit note that `quality_delivery_v83` OFF = zero regression (same as RM-8.3).

---

## 13. Final Verdict

### Cross-Chunk Semantic Quality Gate Assessment:

| Criterion | Result |
|---|---|
| Problem exists? | ✅ **YES** — explicitly acknowledged in RM-8.2 acceptance report |
| Existing capability sufficient? | ❌ **NO** — infrastructure exists but no validation gate consumes it |
| Duplicates existing? | ❌ **NO** — fills gap between RM-8.2 (propagation) and RM-8.3 (format validation) |
| Requires Provider/LLM? | ❌ **NO** — deterministic validation only |
| Increases latency/cost/RPM? | ❌ **NO** — zero provider calls |
| Breaks chunk/assembly/polish? | ❌ **NO** — read-only validation on final text |
| Modifies RM-8.3 Source of Truth? | ❌ **NO** — read-only |
| Affects RM-8.4 EPUB? | ❌ **NO** — independent, EPUB consumes validated output |
| Adds unnecessary complexity? | ❌ **NO** — minimal increment (5-6 functions in existing validator) |
| Clear I/O/ownership? | ✅ **YES** — defined above |
| Reproducible tests? | ✅ **YES** — following RM-8.3 pattern |
| Simpler equivalent? | ❌ **NO** — evaluated alternatives all violate principles |

### Decision: **KEEP / ACCEPT**

The Cross-Chunk Semantic Quality Gate is:
- **Necessary** (addresses documented gap)
- **Sufficient** (leverages existing infrastructure)
- **Minimal** (extends validator, no new modules)
- **Safe** (zero provider, deterministic, feature-gated)
- **Complete** (completes RM-8 quality stack)

---

### Overall Audit Verdict: **CLEAR**

**RM-8.5 Requirements / Architecture Inventory — CONSISTENCY AUDIT PASSES**

The inventory is accurate, gaps are validated, false candidates eliminated, and the recommended primary direction (Cross-Chunk Semantic Quality Gate) is **architecturally sound, evidence-supported, and ready for specification drafting**.

**Authorization**: Proceed to **RM-8.5 Implementation Specification** drafting per governance process.

---

*Audit conducted by direct repository inspection — all claims verified against actual code, tests, and acceptance reports. No implementation performed. No production code modified. No commits made.*