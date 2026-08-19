# RM-8.2 Implementation Specification ??Consistency Audit Report

**Date:** 2026-08-10
**Specification Under Review:** `docs/governance/rm8/RM_8_2_IMPLEMENTATION_SPECIFICATION.md` (Draft)
**Audit Basis:**
- RM-8 Preflight Report (`RM_8_PREFLIGHT_REPORT.md`)
- RM-8.2 Pre-Implementation Audit (`RM_8_2_PRE_IMPLEMENTATION_AUDIT.md`)
- RM-8.2 Preflight Report (`RM_8_2_PREFLIGHT_REPORT.md`)
- RM-8.1 Implementation Specification & Acceptance Report (baseline)
- Existing Chunking Rules (`core/translation_runtime/runtime_chunk.py`)
- NTPE Repository Governance Baseline (`docs/governance/repository/REPOSITORY_GOVERNANCE_BASELINE.md`)
- Context/Scene/Narrative Models (`core/context_scene_memory/models.py`, `scene_state.py`, `context_selection.py`)

---

## EXECUTIVE SUMMARY

**VERDICT: CONDITIONAL PASS ??Specification requires targeted revisions before Implementation authorization.**

The RM-8.2 Implementation Specification is **architecturally sound** and **correctly maps to existing NTPE infrastructure**. It properly reuses `ContextMemoryStore`, `select_context_for_translation()`, `SceneMemoryRecord`, `transition_scene()`, `NarrativeIntelligenceEngine`, `PromptAssembly`, and `RuntimeOrchestrator` ??satisfying the "wiring existing components" mandate.

**However, 5 specific issues violate the hard boundaries declared by the user and must be fixed before Implementation proceeds:**

| # | Hard Boundary | Issue | Severity |
|---|---------------|-------|----------|
| 1 | **Chunking Rules Unchanged** | Spec §3.1 creates `BoundaryResult` with `scene_id`/`chapter_id` auto-generation (`_generate_scene_id()`) that **mimics chunking logic** ??risks becoming a "second chunking engine" | HIGH |
| 2 | **Only Connect Existing Capabilities** | Spec §3.1??.4 introduces **5 new dataclasses** (`BoundaryResult`, `ContextStatePayload`, 4 section builders) when existing models (`BoundaryType`, `ContextSelectionResult`, `SceneMemoryRecord`, `NarrativeState`) could be extended/wrapped | MEDIUM |
| 3 | **Context Enters Production Prompt** | Spec §3.3 adds `Context` section **between Style and Chunk** ??but `SECTION_ORDER` change affects ALL prompts, not just RM-8.2 paths; no feature flag | MEDIUM |
| 4 | **Conservative Boundary Detection** | Spec §4 `detect_boundary()` returns `SCENE_TRANSITION` at confidence 0.3??.6 for heuristics ??**violates "explicit evidence priority"**; `UNKNOWN_TRANSITION` should be default for uncertain cases | HIGH |
| 5 | **Resume/Checkpoint** | Spec §6.3 adds `to_dict/from_dict` to `NarrativeState` but **does not wire it into checkpoint payload** ??`context_store_snapshot` captured but `narrative_state` not persisted/restored | MEDIUM |

**Non-blocking observations (advisory):**
- Spec §9 Phase 7 says "RM-8.2 Specification review ??then commit" ??correct gate
- Spec correctly forbids modifying `split_text()`, `DEFAULT_CHUNK_SIZE`, RM-7 pipeline, provider calls
- Spec correctly uses existing `ContextMemoryStore.snapshot()` for checkpoint
- Acceptance test matrix (§8.1) covers 7 required scenarios with reader-outcome focus

---

## DETAILED AUDIT BY HARD BOUNDARY

---

### 1. CHUNKING RULES COMPLETELY UNCHANGED

**Requirement:** RM-8.2 only consumes existing chunks. No re-chunking. Paragraph splitting only for future TOC/structure, never translation boundaries.

**Specification Status:** **MOSTLY COMPLIANT with one critical violation**

| Check | Status | Evidence |
|-------|--------|----------|
| `split_text()` untouched | ??PASS | Spec §1.2 explicitly forbids modifying `split_text()` or `DEFAULT_CHUNK_SIZE` |
| Chunk = execution unit | ??PASS | Spec §2 data flow shows per-chunk loop unchanged |
| Scene/Chapter ??Chunk | ??PASS | Spec §9 Compliance Checklist items 3, 6, 7, 9, 11 confirm |
| Boundary detection = metadata only | ?��? **VIOLATION** | Spec §4 `_generate_scene_id()` creates `auto_scene_<hash>` IDs ??**this IS chunking logic** (hash-based scene ID from chunk text) |

**Critical Finding:** The `detect_boundary()` function in §4 uses `_generate_scene_id(chunk)` which:
- Hashes the chunk text (`chunk[:100]`) to create a scene ID
- This effectively **derives scene boundaries from chunk content**, not from explicit markers
- While it doesn't modify chunks, it **creates scene IDs that mimic chunking behavior**
- The Pre-Implementation Audit (§3.3) explicitly lists "Scene/Chapter Boundary Detector" as **Missing (D)** ??this is new implementation, not wiring

**Required Fix:**
- Remove `_generate_scene_id()` from `detect_boundary()`
- For heuristic detections (location/time/speaker), return `BoundaryType.UNKNOWN_TRANSITION` with `scene_id=None`
- Only assign `scene_id`/`chapter_id` when **explicit markers** are found (Chapter/Scene patterns)
- Scene ID generation for new scenes should happen in `transition_scene()` (existing logic), not in boundary detection

---

### 2. ONLY CONNECT EXISTING CONTEXT / SCENE / NARRATIVE CAPABILITIES

**Requirement:** Reuse existing models/functions. No duplicate types. "New Types" in spec must be justified.

**Specification Status:** **PARTIAL COMPLIANCE ??5 new dataclasses where 2-3 would suffice**

| New Type in Spec | Existing Equivalent | Reuse Possible? | Verdict |
|------------------|---------------------|-----------------|---------|
| `BoundaryResult` (§3.1) | `BoundaryType` enum + dict metadata | ??Yes ??return `(BoundaryType, dict)` tuple or extend `BoundaryType` with payload | **OVER-ENGINEERED** |
| `ContextStatePayload` (§3.2) | `ContextSelectionResult` + `SceneMemoryRecord.to_dict()` + `NarrativeState.to_dict()` | ??Yes ??compose from existing | **OVER-ENGINEERED** |
| `build_context_selection` (§3.4) | New section | ?��? Needed ??no existing "Context" section | **ACCEPTABLE** |
| `build_character_extended` (§3.4) | `build_character` + `ContextSelectionResult.selected_character_memories` | ??Yes ??extend existing `build_character` with optional param | **OVER-ENGINEERED** |
| `build_scene_extended` (§3.4) | `build_scene` + `SceneMemoryRecord` | ??Yes ??extend existing `build_scene` with optional `scene_state` param | **OVER-ENGINEERED** |
| `build_narrative_extended` (§3.4) | `build_narrative` + `NarrativeState.to_dict()` | ??Yes ??extend existing `build_narrative` | **OVER-ENGINEERED** |

**Root Cause:** The spec treats "extension" as "new parallel builders" rather than "parameterize existing builders."

**Required Fix:**
- Replace `BoundaryResult` with: `BoundaryType` return + optional metadata dict
- Replace `ContextStatePayload` with composed dict from existing serializable objects
- Change `build_character_extended` ??`build_character(runtime, character_memories=...)`
- Change `build_scene_extended` ??`build_scene(runtime, scene_state=...)`
- Change `build_narrative_extended` ??`build_narrative(runtime, narrative_state=...)`
- This reduces new code by ~40% and eliminates parallel maintenance burden

---

### 3. CONTEXT MUST TRULY ENTER PRODUCTION PROMPT

**Requirement:** Not just data creation ??must verify `Chunk N ??Context Update ??Chunk N+1 ??Context Selected ??Prompt Assembly ??Translation`.

**Specification Status:** **ARCHITECTURALLY CORRECT but missing feature flag**

| Check | Status | Evidence |
|-------|--------|----------|
| Context selection called per chunk | ??PASS | Spec §5.1 line 559-567 calls `select_context_for_translation()` |
| Scene state retrieved per chunk | ??PASS | Spec §5.1 line 600 `context_store.get_scene(current_scene_id)` |
| Narrative engine updated per chunk | ??PASS | Spec §5.1 line 570-572 `narrative_engine.analyze_chunk()` + `get_context_for_prompt()` |
| Extended metadata passed to orchestrator | ??PASS | Spec §5.1 line 589-602 passes `context_selection`, `scene_state`, `narrative_state` |
| PromptBuilder receives extensions | ??PASS | Spec §5.2 line 637-643 passes to `PromptBuilder` |
| Section builders use extended data | ??PASS | Spec §3.3-3.4 new builders consume the data |

**Critical Gap:** **No feature flag / profile guard** for the new `Context` section in `SECTION_ORDER`.

Spec §3.4 adds `"Context"` to `SECTION_ORDER` globally:
```python
SECTION_ORDER = (
    "System", "Character", "Entity Mapping", "Glossary",
    "Scene", "Narrative", "Style", "Context",  # NEW
    "Chunk",
)
```

This affects **ALL prompt assemblies**, including:
- Legacy pipeline (if it uses `PromptBuilder`)
- RM-8.1 literary quality runs
- Any existing tests

**Required Fix:**
- Add `enable_cross_chunk_context: bool = False` to `PromptBuilder.__init__`
- Only insert `"Context"` section and use extended builders when `True`
- Gate via `TxtTranslationOptions.quality_context_scene_v72` (already exists per Pre-Implementation Audit §3.2)
- This preserves backward compatibility and allows gradual rollout

---

### 4. BOUNDARY DETECTION MUST BE CONSERVATIVE

**Requirement:** Explicit evidence priority. `SAME_SCENE` default. No false scene transitions. Not a second chunking engine.

**Specification Status:** **VIOLATION ??Heuristic confidence thresholds too low**

Spec §4 `detect_boundary()` returns `SCENE_TRANSITION` at:
- Location shift: **confidence 0.6** (line 458)
- Time shift + paragraph break: **confidence 0.5** (line 469)
- Speaker change at paragraph boundary: **confidence 0.3** (line 479)

**This violates the "explicit evidence priority" rule:**
- Korean markers (`?�N?�`, `?�N?�`, `***`, `Chapter N`) ??0.9-0.95 ??CORRECT
- Heuristics ??0.3-0.6 ??**TOO HIGH** ??will trigger false transitions

**Pre-Implementation Audit §3.3** classifies "Scene/Chapter Boundary Detector" as **D (Missing)** ??this is new code, not existing capability. The audit says: "Auto-detect scene/chapter transitions from source text (Korean markers: `?�X?�`, `?�X?�`, `---`, blank lines, location shifts)"

**Required Fix:**
- Heuristic detections (location/time/speaker) MUST return `BoundaryType.UNKNOWN_TRANSITION` with low confidence
- Only `CHAPTER_TRANSITION` and `SCENE_TRANSITION` for **explicit markers** (patterns in `CHAPTER_PATTERNS`, `SCENE_PATTERNS`)
- `UNKNOWN_TRANSITION` signals "boundary detected but type uncertain" ??downstream `transition_scene()` with `UNKNOWN_TRANSITION` correctly does **no expiry** (see `scene_state.py:120-121`)
- This preserves conservative behavior: explicit markers = transition; uncertainty = no transition

---

### 5. RESUME / CHECKPOINT MUST PRESERVE CROSS-CHUNK STATE

**Requirement:** `ContextMemoryStore` and `NarrativeState` restore on checkpoint resume. Fresh/resume parity.

**Specification Status:** **PARTIAL ??ContextMemoryStore wired, NarrativeState not wired**

| Component | Checkpoint Capture | Restore Logic | Status |
|-----------|-------------------|---------------|--------|
| `ContextMemoryStore` | ??Spec §5.3 line 666 `context_store.snapshot()` | ??Spec §5.3 line 680-683 restores from `context_store_snapshot` | **PASS** |
| `NarrativeState` | ?��? Spec §6.3 adds `to_dict/from_dict` | ??**Not included in checkpoint metadata** | **FAIL** |
| `SceneMemoryRecord` | ??Captured via store snapshot | ??Restored via store | **PASS** |
| `current_scene_id`, `current_chapter_id` | ??Not captured | ??Not restored | **FAIL** |
| `prev_chunk_text` (for boundary detection) | ?��? Spec §6.2 mentions "stored in resume_state" | ??Not in checkpoint payload | **FAIL** |

**Spec §6.2 Resume Flow** mentions:
```
4. Continue chunk loop from chunk 6 with restored store
5. Boundary detection uses prev_chunk_text from chunk 5 (stored in resume_state)
```
But the checkpoint payload (§6.1) doesn't include `prev_chunk_text` or `narrative_state`.

**Required Fix:**
- Extend checkpoint metadata to include:
  ```json
  "narrative_state_snapshot": narrative_engine.state.to_dict(),
  "current_scene_id": "...",
  "current_chapter_id": "...",
  "prev_chunk_text": "...",  // or hash reference
  ```
- Update `restore_checkpoint()` to return these for orchestrator rehydration
- Verify `NarrativeIntelligenceEngine` can be constructed from restored state

---

### 6. NO NEW PROVIDER REQUESTS

**Requirement:** All context/scene/narrative = existing runtime capabilities. No LLM judge, no extra API calls.

**Specification Status:** **PASS**

| Check | Status | Evidence |
|-------|--------|----------|
| Boundary detection | ??PASS | Pure Python regex/heuristics (§4) |
| Context selection | ??PASS | `select_context_for_translation()` ??token budgeting, no LLM |
| Scene transition | ??PASS | `transition_scene()` ??in-memory state mutation |
| Narrative engine | ??PASS | `NarrativeIntelligenceEngine.analyze_chunk()` ??rule-based, no provider (Preflight §2.1) |
| Prompt assembly | ??PASS | `PromptBuilder.build()` ??string construction |
| Orchestrator.execute() | ??PASS | Same call path, extended metadata only |
| TranslationEngine | ??PASS | Unchanged ??consumes `TranslationRequest` |

**Confirmed:** Zero new provider calls in any code path.

---

### 7. ACCEPTANCE MUST PROVE READER OUTCOME

**Requirement:** Demonstrate `Chunk N ??Context Update ??Chunk N+1 ??Context Selected ??Prompt Assembly ??Translation`

**Specification Status:** **PASS ??Test matrix correctly targets reader outcomes**

Spec §8.1 Test Matrix:

| Scenario | Verification | Reader Outcome |
|----------|--------------|----------------|
| same-scene | Context accumulates; scene_version stable; fingerprint evolves | Continuity maintained |
| scene-break | `transition_scene()` called; SCENE_SCOPE expired; new scene_id | Clean scene transition |
| chapter-break | `transition_chapter()` called; SCENE+CHAPTER expired; new chapter_id | Clean chapter transition |
| unknown-boundary | `UNKNOWN_TRANSITION` or low-confidence; conservative expiry | No false transitions |
| checkpoint/resume | Store restored; narrative state restored; prompt hashes match | Resume = fresh |
| chunk-crosses-scene | Boundary recorded in metadata; NO re-chunking; transition before NEXT chunk | Chunking unchanged |
| scene-crosses-chunks | scene_id stable; context accumulates; participants persist | Multi-chunk scene continuity |

**Golden Master Test (§8.2)** correctly verifies:
- Deterministic prompt hashes across runs
- Context fingerprint continuity per chunk
- Scene transition expiry behavior
- Resume restores context store

**One Gap:** Test fixture (§8.3) needs explicit pronoun/dialogue/POV continuity assertions beyond prompt hashes. Recommend adding:
- `test_pronoun_resolution_across_chunks()`
- `test_dialogue_speaker_continuity()`
- `test_narrative_pov_stability()`

---

## CROSS-REFERENCE WITH GOVERNANCE BASELINE

| Governance Rule | Spec Compliance |
|-----------------|-----------------|
| Root Policy: No stage scripts at root | ??Spec only modifies `core/`, `lts/`, `tests/` |
| Tools Directory Structure | ??No new tools created |
| Archive Never Imported | ??No archive imports |
| Future Contribution Rule | ?��? New files (`boundary_detector.py`, test files) must pass `ntpe_validate.py` |
| Directory Ownership | ??`core/translation_runtime/`, `core/prompt_runtime/`, `core/runtime_checkpoint/` are correct homes |

---

## RM-7 CLOSED BOUNDARY CONFIRMATION

Spec §1.2, §9.9, §9.12 correctly forbid:
- Modifying RM-7 Entity Resolution / Review / Learning pipeline
- Entity injection is optional (`None` if not available) ??read-only

**RM-8.1 Acceptance Report** confirms literary quality enforcement complete and isolated from RM-8.2 scope.

---

## RECOMMENDED SPECIFICATION REVISIONS (Before Implementation Authorization)

### Mandatory (Blockers)

1. **Remove `_generate_scene_id()` from `detect_boundary()`** ??return `UNKNOWN_TRANSITION` for heuristics
2. **Reduce new dataclasses** ??compose `ContextStatePayload` from existing serializable objects; parameterize existing section builders instead of creating parallel ones
3. **Add feature flag** for `Context` section and extended builders (`enable_cross_chunk_context`)
4. **Fix boundary detection confidence** ??heuristics ??`UNKNOWN_TRANSITION` (conservative)
5. **Wire NarrativeState + current_scene_id + prev_chunk_text into checkpoint** payload and restore

### Advisory (Non-Blocking)

6. Add pronoun/dialogue/POV continuity assertions to acceptance tests
7. Document `TxtTranslationOptions` flags that gate RM-8.2 features
8. Verify `ntpe_validate.py` passes with new file placements

---

## FINAL VERDICT

| Audit Criterion | Result |
|-----------------|--------|
| RM-8 Preflight alignment | ??PASS |
| RM-8.2 Pre-Implementation Audit alignment | ??PASS (with noted gaps) |
| Existing Chunking Rules unchanged | ?��? **CONDITIONAL** ??fix `_generate_scene_id()` |
| Paragraph splitting ??translation chunks | ??PASS |
| NTPE Architecture / Governance compliance | ??PASS |
| RM-7 CLOSED boundary respected | ??PASS |
| **Overall** | **CONDITIONAL PASS** |

---

**NEXT STEP:** Specification author must address 5 mandatory revisions above. Re-review after revisions. **No Implementation until audit CLEAR.**

---

*End of RM-8.2 Specification Review / Consistency Audit*
