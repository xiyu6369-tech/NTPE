# RM-8.5 Implementation Specification ??Strict Consistency Audit

**Baseline**: NTPE main branch, RM-8.4 final commit `e4af617` (CLEAR)
**Audit Target**: `docs/governance/rm8/RM_8_5_IMPLEMENTATION_SPECIFICATION.md`
**Date**: 2026-08-13
**Standard**: Stricter than previous audit ??data source verification, deterministic vs semantic separation, false-positive/negative analysis, schema necessity

---

## 1. Data Source Verification ??What Actually Exists in chunk_records

### 1.1 Actual `chunk_records[i].metadata.context_state` Structure (from runtime)

```python
# Composed in lts/txt_translation_runtime.py:784-791
context_state_metadata = {
    "context_selection_fingerprint": selection.fingerprint,           # str (SHA256)
    "scene_id": current_scene_id,                                     # str
    "scene_version": context_store.get_scene(current_scene_id).scene_version,  # int
    "narrative": narrative_context,                                   # dict (from NarrativeState.to_prompt_context())
    "boundary": boundary.to_dict(),                                   # dict (BoundaryResult)
    "selected_context_ids": tuple(r.item_id for r in selection.selected_records),  # tuple[str]
}
```

### 1.2 What IS Available (Serialized in chunk_records)

| Field | Type | Content | Reliable for Gate? |
|---|---|---|---|
| `scene_id` | str | Current scene identifier | ??Yes |
| `scene_version` | int | Scene version counter | ??Yes |
| `chapter_id` | str | Current chapter identifier | ??Yes |
| `boundary.type` | str | `same_scene` \| `scene_transition` \| `chapter_transition` \| `unknown_transition` | ??Yes |
| `boundary.scene_id` | str \| None | Target scene_id | ??Yes |
| `boundary.chapter_id` | str \| None | Target chapter_id | ??Yes |
| `narrative.perspective` | str | `first_person` \| `second_person` \| `third_person` \| `unknown` | ??Yes |
| `narrative.voice` | str | `neutral` \| `dialogue_driven` \| `descriptive` \| `balanced` | ??Yes |
| `narrative.tense` | str | `past` \| `present` \| `undetermined` | ??Yes |
| `narrative.emotional_tone` | str | `neutral` \| `tense` \| `calm` \| `joyful` \| `sad` \| `angry` \| `fearful` \| `mixed` | ??Yes |
| `narrative.focus` | str | e.g., `mode=narration_heavy; scene_transitions=2` | ?†Ô? Parsing needed |
| `narrative.transitions` | list[str] | e.g., `["nar_1", "nar_2"]` | ?†Ô? Limited utility |
| `selected_context_ids` | tuple[str] | **Only IDs** (e.g., `("ctx_abc123", "ctx_def456")`) | ??No values |
| `context_selection_fingerprint` | str | SHA256 of selection | ??Opaque |

### 1.3 What is NOT Available in chunk_records (Critical Gaps)

| Missing Data | Where It Lives | Accessible in Validator? |
|---|---|---|
| **Actual context values** (`TERMINOLOGY_STATE`, `RELATIONSHIP_STATE`, etc.) | `ContextMemoryStore.contexts` (live only) | ??No ??only IDs in `selected_context_ids` |
| **Scene `active_speaker`** | `SceneMemoryRecord.active_speaker` (live only) | ??Not serialized in chunk_records |
| **Scene `participants`** | `SceneMemoryRecord.participants` (live only) | ??Not serialized |
| **Scene `point_of_view`** | `SceneMemoryRecord.point_of_view` (live only) | ??Not serialized |
| **Unresolved references** | `SceneMemoryRecord.unresolved_references` (live only) | ??Not serialized |
| **Source chunk text** (Korean) | `record.source.chunk_text` | ??Only if `record.source` exists |
| **Translation per chunk** | NOT in chunk_records (only in chunk files) | ??No ??validator only gets final `text` |

**Evidence**: `runtime_orchestrator/manager.py:155-159` shows `scene_state` and `narrative_state` are passed to `execute()` metadata but **only when `enable_cross_chunk_context=True`**. They are NOT persisted into `chunk_records` by the runtime.

---

## 2. Gate-by-Gate Audit

### GATE 1: `pronoun_consistency` (proposed: major)

| Aspect | Assessment |
|---|---|
| **Input** | `text` (final assembled TXT), `chunk_records` with `context_state` |
| **Observable Evidence** | Pronoun characters in `text`: ‰ª?Â•?ÂÆ?Á•?????‰Ω?Â¶????ëÂÄ?‰Ω†ÂÄ?‰ªñÂÄ?Â•πÂÄ??†ÂÄ?Á•ÇÂÄ?|
| **Deterministic Rule** | Split `text` by chunk boundaries ??for each `same_scene` boundary, compare pronoun categories in last 200 chars of chunk N vs first 200 chars of chunk N+1 |
| **False-Positive Risk** | **HIGH** ??Pronoun category shift ??semantic error. Legitimate: perspective shift, quoted dialogue, narrative focus change, character disguise, pronoun avoiding repetition. No access to `active_speaker` or `participants` to disambiguate. |
| **False-Negative Risk** | **HIGH** ??Same pronoun used for different referents (‰ªñ‚?‰ª?but different person). Cannot detect without entity resolution. |
| **Severity Justification** | `major` ??but heuristic cannot reliably distinguish error from style |
| **Fail-Open/Closed** | Must be **fail-open** (warning only) ??deterministic heuristic ??semantic correctness |
| **Verdict** | **BLOCKED** ??Insufficient evidence in chunk_records; heuristic unreliable without entity/coref data |

---

### GATE 2: `speaker_attribution_stability` (proposed: major)

| Aspect | Assessment |
|---|---|
| **Input** | `text`, `chunk_records` with `context_state` |
| **Observable Evidence** | Dialogue markers: `??..?ç`, `??..?è`, `"..."` in `text` |
| **Deterministic Rule** | Scan dialogue segments ??attribute to speaker ??track across chunks |
| **Critical Missing Data** | **`active_speaker` NOT in chunk_records** ??only in live `SceneMemoryRecord` |
| **False-Positive Risk** | **EXTREME** ??Cannot know who is speaking without `active_speaker` or speaker attribution in context. Dialogue markers alone don't identify speaker. |
| **False-Negative Risk** | **HIGH** ??Speaker changes without explicit attribution (common in Korean narrative) undetectable. |
| **Severity Justification** | Cannot be `major` ??no reliable deterministic signal |
| **Fail-Open/Closed** | N/A ??insufficient data |
| **Verdict** | **BLOCKED** ??Required data (`active_speaker`, `participants`) not serialized in chunk_records |

---

### GATE 3: `narrative_pov_continuity` (proposed: major)

| Aspect | Assessment |
|---|---|
| **Input** | `text`, `chunk_records` with `narrative.perspective` |
| **Observable Evidence** | `narrative.perspective` per chunk: `first_person` \| `second_person` \| `third_person` \| `unknown` |
| **Deterministic Rule** | For consecutive chunks with `boundary.type == "same_scene"`, flag if `perspective` changes |
| **False-Positive Risk** | **LOW-MEDIUM** ??Perspective change within same scene IS an error. But `unknown` values common for Korean source; transition detection conservative. |
| **False-Negative Risk** | **MEDIUM** ??Perspective may drift without `narrative.perspective` changing (e.g., limited?íomniscient within same label). |
| **Severity Justification** | `major` ??Perspective shift disorients readers; data exists |
| **Fail-Open/Closed** | **Fail-open** (warning) ??`unknown` values make strict fail-closed unsafe |
| **Verdict** | **CONDITIONAL PASS** ??Data exists, rule is deterministic, but must handle `unknown` conservatively. Severity: `major` but fail-open. |

---

### GATE 4: `tense_voice_consistency` (proposed: major)

| Aspect | Assessment |
|---|---|
| **Input** | `text`, `chunk_records` with `narrative.tense`, `narrative.voice` |
| **Observable Evidence** | `narrative.tense`: `past`/`present`/`undetermined`; `narrative.voice`: `neutral`/`dialogue_driven`/`descriptive`/`balanced` |
| **Deterministic Rule** | For consecutive chunks with `boundary.type == "same_scene"`, flag if `tense` or `voice` changes |
| **False-Positive Risk** | **LOW-MEDIUM** ??Tense/voice change within scene is generally error. But `undetermined` values common. |
| **False-Negative Risk** | **MEDIUM** ??Subtle voice drift (e.g., neutral?ídialogue_driven) not captured by categorical labels. |
| **Severity Justification** | `major` ??Tense/voice consistency is core narrative quality |
| **Fail-Open/Closed** | **Fail-open** ??`undetermined` values require conservative handling |
| **Verdict** | **CONDITIONAL PASS** ??Data exists, rule deterministic, fail-open required. |

---

### GATE 5: `emotional_tone_coherence` (proposed: minor)

| Aspect | Assessment |
|---|---|
| **Input** | `text`, `chunk_records` with `narrative.emotional_tone` |
| **Observable Evidence** | `narrative.emotional_tone`: `neutral`/`tense`/`calm`/`joyful`/`sad`/`angry`/`fearful`/`mixed` |
| **Deterministic Rule** | Define tone distance matrix ??flag abrupt shifts (e.g., `neutral`?î`tense`, `joyful`?î`sad`) within `same_scene` |
| **False-Positive Risk** | **HIGH** ??Tone shifts are literary devices (contrast, irony, transition). No semantic understanding of justification. |
| **False-Negative Risk** | **HIGH** ??Gradual tone drift undetected; categorical labels too coarse. |
| **Severity Justification** | `minor` ??Subjective; heuristic cannot reliably distinguish device from error |
| **Fail-Open/Closed** | **Must be fail-open (info/minor)** ??Cannot be enforcement gate |
| **Verdict** | **BLOCKED** ??Heuristic ??semantic coherence; high false-positive; tone is artistic choice |

---

### GATE 6: `cross_chunk_entity_consistency` (proposed: major)

| Aspect | Assessment |
|---|---|
| **Input** | `text`, `chunk_records` with `selected_context_ids`, `locked_dictionary` |
| **Observable Evidence** | **NONE in chunk_records** ??`selected_context_ids` are opaque IDs (e.g., `ctx_abc123`). Actual `TERMINOLOGY_STATE` values (`source_term` ??`translated_term`) live only in `ContextMemoryStore.contexts` (runtime memory, not serialized). |
| **Deterministic Rule** | Cannot be implemented ??no access to entity mappings per chunk |
| **False-Positive Risk** | N/A ??no data |
| **False-Negative Risk** | N/A ??no data |
| **Severity Justification** | N/A |
| **Verdict** | **BLOCKED** ??Required data (`TERMINOLOGY_STATE` values) NOT in chunk_records. Would require serializing full `ContextSelectionResult` or `ContextMemoryStore` snapshot. |

---

## 3. Deterministic vs Semantic Correctness Separation

| Gate | Deterministic? | Semantic Correctness Claimed? | Audit Finding |
|---|---|---|---|
| `pronoun_consistency` | ??Yes (regex on text) | ??No ??pronoun category shift ??error | Heuristic ??semantic |
| `speaker_attribution` | ??No (missing data) | ??No | Impossible |
| `narrative_pov_continuity` | ??Yes (categorical compare) | ?†Ô? Partial ??perspective label change ??error | Deterministic signal exists |
| `tense_voice_consistency` | ??Yes (categorical compare) | ?†Ô? Partial ??tense/voice label change ??error | Deterministic signal exists |
| `emotional_tone_coherence` | ??Yes (tone matrix) | ??No ??tone shift ??error | Heuristic ??semantic |
| `cross_chunk_entity` | ??No (missing data) | ??No | Impossible |

**Key Principle**: Deterministic ??Semantic Correctness. A deterministic rule that flags "perspective changed" is valid as a **signal**, not a **verdict**. Severity must reflect uncertainty.

---

## 4. Schema Modification Necessity (`metadata.py` / `models.py`)

### Current `QualityCertificate` (6 dimension scores):
1. `literary_quality_score`
2. `format_consistency_score`
3. `term_lock_compliance_score`
4. `completeness_score`
5. `context_continuity_score`

### Proposed 6 Additional Scores:
- `pronoun_consistency_score`
- `speaker_attribution_score`
- `narrative_pov_score`
- `tense_voice_score`
- `emotional_tone_score`
- `cross_chunk_entity_score`

### Audit Finding:
**Only 2 gates have viable data** (`narrative_pov_continuity`, `tense_voice_consistency`). Adding 6 schema fields for 2 viable gates is **over-engineering**.

**Recommendation**:
- Do NOT modify `QualityCertificate` schema for speculative gates
- Extend `ValidationCheck.details` with gate-specific metrics (already supported)
- Add dimension scores ONLY for gates that pass audit
- `checks` dict in `QualityCertificate` already captures all check scores ??no schema change needed for reporting

---

## 5. Feature Flag Verification (`quality_delivery_v83` OFF)

**Code Path** (`delivery_pipeline.py:100-146`):
```python
def run_delivery_pipeline(..., options: TxtTranslationOptions, ...):
    # Only called if:
    if getattr(options, "quality_delivery_v83", False) and not options.dry_run:
        # ... entire pipeline including validate_final_novel()
```

**Validator Call** (`delivery_pipeline.py:130-137`):
```python
qc_result = validate_final_novel(
    text=polished_text,
    locked_dictionary=locked_dictionary,
    chunk_records=chunk_records,
    literary_quality_aggregate=literary_quality_aggregate,
    options=options,
    matched_terms=matched_terms,
)
```

**Finding**: ??**CONFIRMED** ??When `quality_delivery_v83=False` (default), `run_delivery_pipeline()` is never called. Validator never executes. Zero regression.

---

## 6. TXT Source of Truth Integrity

**Validator Input**: `text` parameter = RM-8.3 polished TXT body (final assembled novel)

**Validator Behavior**: Read-only analysis. No modification of `text`. No re-assembly, no re-polish, no re-translate.

**Finding**: ??**CONFIRMED** ??Validator is pure function: `(text, chunk_records, ...) ??ValidationResult`. No side effects on Source of Truth.

---

## 7. No Re-Chunk/Assemble/Polish/Translate

**Validator Scope**: Post-delivery validation gate only. Runs AFTER:
1. Translation complete (all chunks)
2. Assembly complete (`"\n\n".join(translated_chunks)`)
3. Polish complete (`polish_full_novel()`)
4. Canonicalization complete

**Finding**: ??**CONFIRMED** ??Validator is final gate. No pipeline re-execution.

---

## 8. RM-8.4 EPUB Independence

**EPUB Packaging** (`delivery_pipeline.py:196-226`):
```python
if "epub" in formats:
    # Build ReaderChapterMap from polished_text + chunk_records
    reader_chapter_map = build_reader_chapter_map(...)
    # pack_epub() uses ReaderChapterMap positions to slice polished_text
```

**Dependency Direction**:
- RM-8.5 (validator) ??produces `ValidationResult` ??`QualityCertificate`
- RM-8.4 (EPUB) ??consumes `polished_text` + `ReaderChapterMap` ??produces EPUB
- **No reverse dependency** ??EPUB does not read `ValidationResult` or `QualityCertificate`

**Finding**: ??**CONFIRMED** ??RM-8.4 EPUB completely independent of RM-8.5. EPUB failure never blocks Core (graceful fallback).

---

## 9. Final Gate Assessment Summary

| Gate | Verdict | Reason |
|---|---|---|
| `pronoun_consistency` | **BLOCKED** | Heuristic unreliable; no coref data; high FP/FN |
| `speaker_attribution_stability` | **BLOCKED** | Required data (`active_speaker`) not in chunk_records |
| `narrative_pov_continuity` | **CONDITIONAL PASS** | Data exists; deterministic; fail-open (major?íminor) |
| `tense_voice_consistency` | **CONDITIONAL PASS** | Data exists; deterministic; fail-open (major?íminor) |
| `emotional_tone_coherence` | **BLOCKED** | Tone shift ??error; artistic choice; high FP |
| `cross_chunk_entity_consistency` | **BLOCKED** | Required data (`TERMINOLOGY_STATE` values) not in chunk_records |

---

## 10. Revised RM-8.5 Scope Recommendation

### MINIMAL VIABLE RM-8.5 (2 Gates Only)

| Gate | Severity | Behavior |
|---|---|---|
| `narrative_pov_continuity` | `minor` (fail-open) | Flag unauthorized perspective changes within same scene |
| `tense_voice_consistency` | `minor` (fail-open) | Flag unauthorized tense/voice changes within same scene |

### Implementation Changes Required:

1. **`validator.py`**: Add 2 `_check_*` functions, register in `validate_final_novel()`
2. **`models.py`**: **NO CHANGE** ??use existing `checks` dict in `QualityCertificate`
3. **`metadata.py`**: **NO CHANGE** ??`generate_quality_certificate()` already maps `check_scores` dynamically
4. **Tests**: Unit tests for 2 gates + golden master

### Deferred Gates (Future RM):
- `pronoun_consistency` ??Requires entity/coref data in chunk_records (RM-8.6+)
- `speaker_attribution_stability` ??Requires `active_speaker` serialization (RM-8.6+)
- `cross_chunk_entity_consistency` ??Requires `TERMINOLOGY_STATE` serialization (RM-8.6+)
- `emotional_tone_coherence` ??Fundamentally heuristic; not suitable for gate

---

## 11. Final Audit Decision

### ??SPECIFICATION AS WRITTEN: **BLOCKED**

**Reasons**:
1. 4 of 6 gates lack required data in chunk_records
2. 3 of 6 gates confuse deterministic heuristic with semantic correctness
3. Schema changes proposed for gates that cannot be implemented
4. Severity assignments don't match evidence reliability

### ??MINIMAL RM-8.5 (2 Gates): **CLEAR ??Phase 1**

**Authorized Scope**:
- `narrative_pov_continuity` (minor, fail-open)
- `tense_voice_consistency` (minor, fail-open)

**Required Specification Revisions**:
1. Remove 4 blocked gates from specification
2. Change severity of 2 passing gates from `major` to `minor` (fail-open)
3. Remove `QualityCertificate` schema modifications (unnecessary)
4. Update test specifications for 2 gates only
5. Explicitly document fail-open behavior and `unknown` value handling

---

**Audit Authority**: This audit is based on actual repository inspection of data structures in `chunk_records`, runtime serialization paths, and validator integration. No implementation performed. No production code modified.

**Next Step**: Specification author must revise per above, then re-submit for audit clearance before Phase 1 implementation.

---

## 12. Post-Revision Audit (2026-08-13) ??REVISED SPECIFICATION

### 12.1 Revised Specification Review

The specification at `docs/governance/rm8/RM_8_5_IMPLEMENTATION_SPECIFICATION.md` has been revised per Section 11 findings.

### 12.2 Gate-by-Gate Verification of Revised Spec

| Gate | Revised Spec Status | Audit Finding |
|---|---|---|
| `pronoun_consistency` | **REMOVED** | ??Correct ??blocked in original audit |
| `speaker_attribution_stability` | **REMOVED** | ??Correct ??blocked in original audit |
| `emotional_tone_coherence` | **REMOVED** | ??Correct ??blocked in original audit |
| `cross_chunk_entity_consistency` | **REMOVED** | ??Correct ??blocked in original audit |
| `narrative_pov_continuity` | **KEPT** ??severity `minor`, FAIL-OPEN | ??Matches Conditional Pass ??data exists, deterministic |
| `tense_voice_consistency` | **KEPT** ??severity `minor`, FAIL-OPEN | ??Matches Conditional Pass ??data exists, deterministic |

### 12.3 Architecture Verification

| Aspect | Revised Spec | Audit Requirement | Match |
|---|---|---|---|
| QualityCertificate modifications | **NONE** | No schema change needed | ??|
| metadata.py modifications | **NONE** | No change needed | ??|
| models.py modifications | **NONE** | No change needed | ??|
| validator.py only | **YES** | Single module, no new deps | ??|
| Fail-open mandatory | **EXPLICIT** | Required for both gates | ??|
| `unknown` = no false positive | **EXPLICIT** | Required for both gates | ??|
| Feature-gated (`quality_delivery_v83`) | **YES** | Default OFF, zero regression | ??|
| No TXT modification | **READ-ONLY** | Source of Truth integrity | ??|
| No re-chunk/assemble/polish | **YES** | Post-delivery gate only | ??|
| EPUB independence | **CONFIRMED** | No reverse dependency | ??|

### 12.4 Test Specification Verification

| Test Requirement | Revised Spec | Audit Verification |
|---|---|---|
| `narrative_pov_continuity` unit tests | **INCLUDED** | ??Pass/fail/unknown/transition/missing all covered |
| `tense_voice_consistency` unit tests | **INCLUDED** | ??Pass/fail/unknown/transition/missing all covered |
| `unknown` no-false-positive test | **EXPLICIT** | ??`test_*_unknown_is_no_false_positive` |
| Missing context fail-open test | **EXPLICIT** | ??`test_*_missing_context_is_fail_open` |
| Severity = minor verified | **EXPLICIT** | ??Assertions in tests |

### 12.5 Final Audit Decision ??REVISED SPECIFICATION

### ??REVISED SPECIFICATION: **CLEAR ??Phase 1 Implementation Authorized**

**Authorized Scope**:
- `narrative_pov_continuity` (minor, fail-open, unknown=no-false-positive)
- `tense_voice_consistency` (minor, fail-open, unknown=no-false-positive)

**Implementation Files**:
- `core/translation_release/validator.py` ??ADD 2 `_check_*` functions, register in `validate_final_novel()`
- `tests/unit/translation_release/test_validator.py` ??EXTEND with 2 gate test suites

**NO Changes To**:
- `core/translation_release/metadata.py`
- `core/translation_release/models.py`
- Any other RM-8.3 files

**Rollout**:
1. Phase 1: Implement 2 checks in `validator.py` with FAIL-OPEN
2. Phase 2: Register in `validate_final_novel()`
3. Phase 3: Run unit tests (`pytest tests/unit/translation_release/test_validator.py -k "pov or tense"`)
4. Phase 4: Canary with `quality_delivery_v83=True`
5. Phase 5: Full regression suite
6. Phase 6: Specification Review ??commit

---

**Audit Authority**: This audit is based on actual repository inspection of data structures in `chunk_records`, runtime serialization paths, and validator integration. No implementation performed. No production code modified.

**Status**: **CLEAR** ??Phase 1 Implementation Authorized
