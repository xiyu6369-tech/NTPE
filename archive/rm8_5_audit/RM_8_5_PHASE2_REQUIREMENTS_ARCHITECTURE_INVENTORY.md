# RM-8.5 Phase 2 — Requirements / Architecture Inventory Report

**Status**: READ-ONLY ANALYSIS — No production code modified
**Date**: 2026-08-14
**Baseline**: origin/main == local main at 3199039 (Phase 1 committed)
**Governance Path**: docs/governance/rm8/ → artifacts/rm8_5_audit/

---

## 1. RM-8.5 Phase 1 — Actual State Inventory

### 1.1 What Phase 1 Actually Delivered (Verified from Code)

| Item | Implementation | Location |
|------|----------------|----------|
| Validator Extended | validate_final_novel() + 2 new _check_* functions | core/translation_release/validator.py:119-123, 410-617 |
| Check 1 | narrative_pov_continuity (minor, FAIL-OPEN) | validator.py:410-507 |
| Check 2 | tense_voice_consistency (minor, FAIL-OPEN) | validator.py:510-617 |
| Feature Flag | quality_delivery_v83 (default OFF) | validator.py:121, txt_translation_runtime.py:146 |
| Tests | 49 unit tests for 2 gates + feature flag | tests/unit/translation_release/test_validator.py:405-895 |
| Integration | Called from delivery_pipeline.py:130-137 | Only when quality_delivery_v83=True |

### 1.2 Verified Principles Enforced in Phase 1

| Principle | Evidence |
|-----------|----------|
| Deterministic | Pure Python, no LLM/provider calls |
| FAIL-OPEN mandatory | Both checks wrap in try/except, return passed=True, score=100 on any error |
| unknown = no false positive | Explicit checks: if perspective == "unknown": continue (POV), if tense == "unknown": continue (tense) |
| Minor severity only | Both registered as severity="minor" |
| No QualityCertificate changes | Uses existing ValidationCheck.details dict |
| No metadata.py/models.py changes | Confirmed - zero modifications |
| Feature-gated | Only runs when options.quality_delivery_v83=True |
| Zero regression when OFF | delivery_pipeline.py never calls validator when flag OFF |

### 1.3 Test Results (Verified)

- RM-8.5 Semantic Tests: 49 PASS
- translation_release total: 187 PASS / 2 skipped
- ntpe_validate.py: PASS
- compileall: 0 errors

---

## 2. RM-8.2 to 8.5 Runtime / Data-Flow Inventory

### 2.1 What IS Serialized in chunk_records (Available to Validator)

Extracted from lts/txt_translation_runtime.py:784-791 and core/intelligence/narrative_state.py:34-46:

| Field | Source | Type | Values | Reliable for Gate |
|-------|--------|------|--------|:-----------------:|
| scene_id | ContextMemoryStore | str | e.g., "scene_3" | Yes |
| scene_version | ContextMemoryStore | int | e.g., 2 | Yes |
| chapter_id | Boundary detector | str | e.g., "chapter_1" | Yes |
| boundary.type | BoundaryResult.to_dict() | str | same_scene / scene_transition / chapter_transition / unknown_transition | Yes |
| boundary.scene_id | BoundaryResult | str / None | Target scene | Yes |
| boundary.chapter_id | BoundaryResult | str / None | Target chapter | Yes |
| boundary.confidence | BoundaryResult | float | 0.2-0.95 | Yes |
| narrative.perspective | NarrativeState.to_prompt_context() | str | first_person / second_person / third_person / unknown | Yes |
| narrative.voice | NarrativeState.to_prompt_context() | str | neutral / dialogue_driven / descriptive / balanced | Yes |
| narrative.tense | NarrativeState.to_prompt_context() | str | past / present / undetermined | Yes |
| narrative.emotional_tone | NarrativeState.to_prompt_context() | str | neutral / tense / calm / joyful / sad / angry / fearful / mixed | Parsing needed |
| narrative.focus | NarrativeState.to_prompt_context() | str | e.g., "mode=narration_heavy; scene_transitions=2" | Parsing needed |
| narrative.transitions | NarrativeState.to_prompt_context() | list[str] | e.g., ["nar_1", "nar_2"] | Limited utility |
| narrative.metadata.updates | NarrativeState.to_prompt_context() | int | Update counter | Yes |
| context_selection_fingerprint | ContextSelectionResult | str | SHA256 | Opaque |
| selected_context_ids | ContextSelectionResult | tuple[str] | IDs only (e.g., ("ctx_abc", "ctx_def")) | No values |

### 2.2 What is NOT Serialized (Runtime-Only / Opaque)

| Missing Data | Where It Lives | Accessible in Validator |
|--------------|----------------|:----------------------:|
| Actual context values (TERMINOLOGY_STATE, RELATIONSHIP_STATE, etc.) | ContextMemoryStore.contexts (live) | No — only IDs in selected_context_ids |
| Scene active_speaker | SceneMemoryRecord.active_speaker | Not serialized |
| Scene participants | SceneMemoryRecord.participants | Not serialized |
| Scene point_of_view | SceneMemoryRecord.point_of_view | Not serialized |
| Unresolved references | SceneMemoryRecord.unresolved_references | Not serialized |
| Source chunk text (Korean) | record.source.chunk_text | Only if record.source exists |
| Translation per chunk | Chunk files only | Validator gets final text only |
| Entity injection set | Runtime metadata (optional) | Not in chunk_records |

Evidence: txt_translation_runtime.py:827-832 shows scene_state and narrative_state passed to execute() metadata but NOT persisted into chunk_records.

---

## 3. Candidate Quality Problem Evaluation Matrix

### 3.1 Already Solved by Phase 1 (DO NOT RE-DO)

| Problem | Phase 1 Check | Data Source | Status |
|---------|---------------|-------------|--------|
| Perspective continuity within scene | narrative_pov_continuity | narrative.perspective | DONE |
| Tense consistency within scene | tense_voice_consistency | narrative.tense | DONE |
| Voice consistency within scene | tense_voice_consistency | narrative.voice | DONE |

---

### 3.2 Category A: Reliable Runtime Evidence Exists (Phase 2 Candidates)

| Candidate Gate | Evidence Available | Deterministic | FP Risk | FN Risk | Provider Cost | SoT Risk | Phase 1 Overlap |
|----------------|-------------------|:-------------:|:-------:|:-------:|:-------------:|:--------:|:---------------:|
| Scene transition validation | boundary.type, scene_id, chapter_id | Yes | Low | Low | 0 | 0 | No |
| Chapter boundary enforcement | boundary.type == "chapter_transition" | Yes | Low | Low | 0 | 0 | No |
| Scene version monotonicity | scene_version per chunk | Yes | Low | Low | 0 | 0 | No |
| Context selection fingerprint stability | context_selection_fingerprint | Yes | Medium | Low | 0 | 0 | No |
| Narrative update counter monotonicity | narrative.metadata.updates | Yes | Low | Low | 0 | 0 | No |

---

### 3.3 Category B: Runtime Evidence Exists But Semantic Insufficiency

| Candidate Gate | Evidence Available | Why Insufficient |
|----------------|-------------------|------------------|
| Emotional tone coherence | narrative.emotional_tone | Tone shifts are literary devices (contrast, irony, transition). Categorical labels too coarse. No semantic understanding of justification. |
| Focus/narrative mode consistency | narrative.focus (parsed) | String parsing needed; mode=narration_heavy vs mode=dialogue_heavy are stylistic, not errors. |
| Narrative transitions tracking | narrative.transitions list | Only segment IDs where transitions detected; no semantic meaning for validation. |

Verdict: These are heuristic signals, not semantic correctness gates. Must remain info/minor severity with FAIL-OPEN.

---

### 3.4 Category C: Requires Missing Runtime Data (BLOCKED)

| Candidate Gate | Missing Data | Required Serialization |
|----------------|--------------|------------------------|
| Pronoun consistency / coreference | Entity/coref data, participants, active_speaker | Full SceneMemoryRecord + ContextMemoryStore snapshot |
| Speaker attribution stability | active_speaker, participants with speaker roles | SceneMemoryRecord.active_speaker + SceneParticipant with speaker flags |
| Cross-chunk entity consistency | TERMINOLOGY_STATE values (source to target mappings) | ContextMemoryRecord with ContextType.TERMINOLOGY_STATE serialized |
| Relationship consistency | RELATIONSHIP_STATE values | ContextMemoryRecord with ContextType.RELATIONSHIP_STATE serialized |
| Unresolved reference tracking | unresolved_references | SceneMemoryRecord.unresolved_references serialized |

Verdict: BLOCKED for Phase 2. Would require RM-8.6+ serialization work. Phase 2 MUST NOT invent heuristic proxies.

---

### 3.5 Category D: LLM/Provider Layer (EXPLICITLY EXCLUDED)

| Candidate | Why Excluded |
|-----------|--------------|
| Semantic equivalence (Korean to Chinese) | Requires LLM judge |
| Translation quality scoring | Requires provider calls |
| Style/fluency assessment | Requires LLM |
| Cultural nuance validation | Requires LLM |

Verdict: These are Quality Layer problems, not deterministic validator problems. Explicitly excluded by governance.

---

## 4. Candidate Gates Evaluation Matrix for Phase 2

| Gate | Category | Data in chunk_records | Deterministic | FP Risk | FN Risk | Provider Cost | SoT Risk | Phase 1 Overlap | Phase 2 Viability |
|------|----------|:---------------------:|:-------------:|:-------:|:-------:|:-------------:|:--------:|:---------------:|:-----------------:|
| Scene transition validation | A | Yes | Yes | Low | Low | 0 | 0 | No | HIGH |
| Chapter boundary enforcement | A | Yes | Yes | Low | Low | 0 | 0 | No | HIGH |
| Scene version monotonicity | A | Yes | Yes | Low | Low | 0 | 0 | No | HIGH |
| Context fingerprint stability | A | Yes | Yes | Med | Low | 0 | 0 | No | MEDIUM |
| Narrative update monotonicity | A | Yes | Yes | Low | Low | 0 | 0 | No | MEDIUM |
| Emotional tone coherence | B | Yes | Yes | High | High | 0 | 0 | No | LOW (info only) |
| Focus/mode consistency | B | Parse needed | Yes | High | Med | 0 | 0 | No | LOW (info only) |
| Pronoun/coref consistency | C | No | No | N/A | N/A | 0 | 0 | No | BLOCKED |
| Speaker attribution | C | No | No | N/A | N/A | 0 | 0 | No | BLOCKED |
| Entity consistency | C | No | No | N/A | N/A | 0 | 0 | No | BLOCKED |
| Relationship consistency | C | No | No | N/A | N/A | 0 | 0 | No | BLOCKED |
| LLM semantic gates | D | N/A | No | N/A | N/A | >0 | N/A | No | EXCLUDED |

---

## 5. Explicitly Excluded Candidates (Non-Starters for Phase 2)

| Candidate | Exclusion Reason | Governance Rule |
|-----------|------------------|-----------------|
| Pronoun/coreference consistency | No entity data in chunk_records; heuristic would be pure guesswork | Principle 3: No heuristic without reliable data |
| Speaker attribution | active_speaker not serialized; dialogue markers don't identify speaker | Principle 2: No invented enum/field |
| Cross-chunk entity consistency | TERMINOLOGY_STATE values not in chunk_records | Principle 1: RM-8.2 contract only |
| Emotional tone as quality gate | Tone shifts = literary device; categorical labels too coarse | Principle 3: Deterministic != semantic correctness |
| LLM-based semantic validation | Requires provider calls | Principle 6: No Provider/LLM/Network |
| Auto-fix/correction | Modifies Source of Truth | Principle 9: No gate blocks Core Delivery |
| New QualityCertificate dimensions | 6 proposed for 2 viable gates = over-engineering | Audit finding: schema change unnecessary |

---

## 6. Phase 2 Recommended Primary Direction

Based on the inventory, Phase 2 should focus on Category A gates only:

### Primary Candidates (High Viability):

1. **Scene Transition Validation** (minor, FAIL-OPEN)
   - Verify boundary.type transitions are consistent with scene_id/chapter_id changes
   - Flag: scene_transition without scene_id change, chapter_transition without chapter_id change
   - Data: boundary.type, boundary.scene_id, boundary.chapter_id, scene_id, chapter_id

2. **Chapter Boundary Enforcement** (minor, FAIL-OPEN)
   - Verify chapter transitions only occur at explicit markers
   - Flag: chapter_id changes without boundary.type == "chapter_transition"
   - Data: chapter_id per chunk, boundary.type

3. **Scene Version Monotonicity** (minor, FAIL-OPEN)
   - Verify scene_version increments monotonically within a scene_id
   - Flag: version decrease or gap > 1 without transition
   - Data: scene_id, scene_version

4. **Context Selection Fingerprint Stability** (info, FAIL-OPEN)
   - Verify context_selection_fingerprint doesn't change unexpectedly within same scene
   - Flag: fingerprint change without scene_transition/chapter_transition
   - Data: context_selection_fingerprint, boundary.type

5. **Narrative Update Counter Monotonicity** (info, FAIL-OPEN)
   - Verify narrative.metadata.updates increments monotonically
   - Flag: counter decrease or reset without chapter transition
   - Data: narrative.metadata.updates, chapter_id

### Secondary Candidates (Lower Priority, Info Severity Only):

- Emotional tone drift detection (info only, FAIL-OPEN, explicitly heuristic)
- Focus/narrative mode consistency (info only, FAIL-OPEN)

---

## 7. Phase 2 Preliminary Architecture Boundary

```
RM-8.5 Phase 2 = Deterministic Cross-Chunk Structural Validation Gates
```

### Scope IN:
- Read-only consumption of existing chunk_records.metadata.context_state
- New _check_* functions in core/translation_release/validator.py only
- Feature-gated by existing quality_delivery_v83 (default OFF)
- FAIL-OPEN mandatory (any error/unknown -> pass)
- Minor/info severity only
- No QualityCertificate schema changes (use existing checks dict)
- No metadata.py/models.py modifications

### Scope OUT (Explicitly Prohibited):
- Modifying RM-8.2 runtime (ContextMemoryStore, NarrativeEngine, BoundaryDetector)
- Serializing new fields into chunk_records (active_speaker, participants, etc.)
- Any heuristic without serialized evidence (Category C)
- Any LLM/Provider/Network calls (Category D)
- Re-chunk, re-assemble, re-polish, re-translate
- Modifying TXT Source of Truth
- New validator framework (extend existing only)
- QualityCertificate dimension score additions
- Auto-fix/correction
- Root-level report scripts (governance -> docs/governance/rm8/, evidence -> artifacts/rm8_5_audit/)

---

## 8. Final Verdict

### READY FOR SPECIFICATION

**Rationale**:
1. Phase 1 is CLOSED and verified — 49/49 tests PASS, integration confirmed, zero regression
2. Category A gates have reliable serialized evidence — 5 viable candidates with deterministic rules
3. Category C/D gates explicitly BLOCKED/EXCLUDED — prevents scope creep
4. Architecture boundary is clear — extends existing validator only, no runtime changes
5. Governance constraints satisfied — FAIL-OPEN, minor severity, feature-gated, no Provider cost

### Specification Required:
1. RM-8.5 Phase 2 Implementation Specification -> docs/governance/rm8/RM_8_5_PHASE2_IMPLEMENTATION_SPECIFICATION.md
2. Candidate gate algorithms (5 primary, 2 secondary)
3. Test specifications for each gate
4. Integration verification with existing quality_delivery_v83 flag

### Next Step:
Architecture Acceptance Review -> if CLEAR -> Phase 2 Specification -> Consistency Audit -> Implementation Authorization

---

**Report Location**: This inventory saved to artifacts/rm8_5_audit/RM_8_5_PHASE2_REQUIREMENTS_ARCHITECTURE_INVENTORY.md per governance (not repository root).