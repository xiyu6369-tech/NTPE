# RM-8.2 PREFLIGHT REPORT
## Cross-Chunk Context Continuity ??Capability Inventory & Integration Assessment

**Generated:** 2026-08-10
**Version:** rm-8.2.0-preflight
**Status:** COMPLETED

---

## 1. EXECUTIVE SUMMARY

**Core Question:** Does NTPE already possess cross-chunk scene/narrative context, merely lacking integration? Or is the capability genuinely missing?

**Answer:** **NTPE possesses substantial cross-chunk context CAPABILITIES (data models, selection logic, prompt sections) but they are NOT integrated into the production runtime pipeline.** The Context/Scene/Narrative domains in PromptAssembly are empty during actual translation runs. The `context_scene_memory` module exists with full schema for scene/narrative/character continuity tracking, but no extractor populates it from source text during translation.

---

## 2. EXISTING CROSS-CHUNK CONTEXT CAPABILITIES

### 2.1 Data Models (FULLY IMPLEMENTED)

| Capability | Location | Status | Details |
|------------|----------|--------|---------|
| **Scene Context** | `core/context_scene_memory/models.py:210-232` | ??Complete | `SceneMemoryRecord` with location, time_state, participants, active_speaker, point_of_view, event_state, unresolved_references |
| **Narrative Context** | `core/context_scene_memory/models.py:15-29` | ??Complete | `ContextType` enum: SCENE_SUMMARY, EVENT_STATE, TEMPORAL_STATE, LOCATION_STATE, SPEAKER_STATE, POINT_OF_VIEW, RELATIONSHIP_STATE, ADDRESSING_STATE, CONTINUITY_NOTE |
| **Character State** | `core/context_scene_memory/models.py:172-186` | ??Complete | `SceneParticipant` with character_id, participant_status, presence_confidence, unresolved_identity |
| **Dialogue/Speaker Continuity** | `core/context_scene_memory/models.py:22-23` | ??Complete | `ContextType.SPEAKER_STATE`, `ContextType.ADDRESSING_STATE` |
| **Temporal/Spatial Continuity** | `core/context_scene_memory/models.py:20-21` | ??Complete | `ContextType.TEMPORAL_STATE`, `ContextType.LOCATION_STATE` |
| **Chunk Boundary Context** | `core/context_scene_memory/scene_state.py:110-144` | ??Complete | `transition_scene()` with BoundaryType (SAME_SCENE, SCENE_TRANSITION, CHAPTER_TRANSITION) and context expiry |
| **Context Snapshot/Carry-Forward** | `core/context_scene_memory/context_selection.py:51-160` | ??Complete | `select_context_for_translation()` with token budget, scope filtering, deduplication, deterministic fingerprint |

### 2.2 Prompt Assembly Slots (EXIST BUT EMPTY)

| Section | Builder | Status in Canary |
|---------|---------|------------------|
| **Scene** | `core/prompt_runtime/sections.py:123-132` | ??Builder exists, domain empty |
| **Narrative** | `core/prompt_runtime/sections.py:135-144` | ??Builder exists, domain empty |
| **Entity Mapping** | `core/prompt_runtime/sections.py:54-108` | ??Populated via RM-7 entity normalization |

### 2.3 Selection & Integration Logic (IMPLEMENTED)

| Component | Location | Function |
|-----------|----------|----------|
| `select_context_for_translation()` | `core/context_scene_memory/context_selection.py` | Filters by chapter/scene/sequence, token budget, priority |
| `select_quality_context()` | `core/translation_quality_integration_v72/selection.py:79-93` | Integrates context_scene_memory into TQI v7.2 prompt injection |
| Knowledge Merger REPLACE strategy | `core/knowledge_runtime/merger.py:24-30` | Scene/Narrative domains use REPLACE (lowest non-empty wins) |

---

## 3. PROGRAMMATIC CHAIN ANALYSIS

### Current Production Chain (txt_translation_runtime.py)

```
Chunk N
    ??split_text() ??naive paragraph/sentence splitting
    ??build_prompt_package() ??previous_context = last 2 chunks tail (700 chars)
    ??apply_context_intelligence() ??local snapshot (profile, tone, narrative_state="continuing_scene")
    ??TranslationEngine ??provider call
    ??QA ??retry loop
    ??Concatenate chunks ??final output
```

**Missing Links:**
- No scene/narrative extraction from source text
- No `context_scene_memory` population during translation
- No chapter/scene boundary detection
- Previous context is raw text tail only (no structured context)

### Available but Unwired Chain

```
Chunk N (source text)
    ??[MISSING] Scene/Narrative Extractor ??ContextMemoryRecord(s)
    ??KnowledgeRuntimeManager.load_all() ??MergedRuntime (with scene/narrative domains)
    ??PromptBuilder ??PromptAssembly (Scene + Narrative sections populated)
    ??TranslationRuntimeAdapter ??TranslationRequest
    ??TranslationEngine ??provider call
    ??[MISSING] Post-translation ??Update context_scene_memory with translation observations
    ??Chunk N+1 ??select_context_for_translation() carries forward relevant context
```

---

## 4. READER OUTCOME EVIDENCE

### 4.1 Current Novel Sample Output (translated/novel_sample_chunk_*.txt)

**Chunk 1 ??Chunk 2 Transition Analysis:**

| Dimension | Chunk 1 End | Chunk 2 Start | Continuity |
|-----------|-------------|---------------|------------|
| **Character Names** | ?­æ³°ç¾? ä¼Šè? | ?­æ³°ç¾? ä¼Šè? | ??Consistent (RM-7 entity normalization) |
| **Address Forms** | å¤ªç¾©è­¦å?, æ­?¤ªç¾?| å¤ªç¾©, ?­å???| ? ï? Partial - no formal address policy enforced |
| **Scene** | ?–å•¡åº—ã€Œåˆ¥å¢…ã€?| å»¢æ??†æ¥­å¤§æ??°ä?å®?| ??Scene transition not explicitly signaled |
| **Temporal** | ä¸‹å?ä¸‰é?å·¦å³ | ç¬¬ä?å¤©æ—©ä¸?| ??Explicit in source, preserved |
| **Narrative POV** | Third-person limited (å¤ªç¾©) | Third-person limited (å¤ªç¾©) | ??Consistent |
| **Dialogue Speaker** | å¥³æ€§ç?ç§˜äºº | ä¸­å¹´?·äºº | ??Different speakers, no confusion |
| **Pronouns** | ä»?å¥???| ä»?????| ??Consistent in this sample |

**Critical Gap:** No automated test validates any of the above. Continuity is **accidental** (model's own coherence), not **enforced** by pipeline.

### 4.2 Failure Modes Observed in Literature (Not Yet Tested)

| Failure Mode | Description | Likelihood Without Cross-Chunk Context |
|--------------|-------------|----------------------------------------|
| **äººç¨±æ¼‚ç§»** | 1st??rd person shift across chunks | HIGH |
| **è§’è‰²èªžæ°£æ¼‚ç§»** | Speech style inconsistency (honorifics, formality) | HIGH |
| **?´æ™¯èª¤åˆ¤** | Treating new scene as continuation | MEDIUM |
| **å°è©±æ­¸å±¬?¯èª¤** | Wrong speaker attribution | MEDIUM |
| **?‚ç©º?œä??ºå¤±** | Time/location references unresolved | MEDIUM |
| **èªžç¾©?·è?** | Pronouns ("ä»?, "?™è£¡") lose referents | HIGH |

---

## 5. TEST COVERAGE ANALYSIS

### 5.1 Existing Tests

| Test | Scope | Cross-Chunk Validation |
|------|-------|------------------------|
| `test_context_scene_memory.py` | Unit - data structures, selection logic | ??Selection logic only, no translation |
| `test_stage16_2_narrative_intelligence.py:41` | Unit - NarrativeState tracks perspective/tense | ??In-memory state only, no pipeline integration |
| `test_translation_quality_canary.py:41` | Canary - "context_continuity" category | ? ï? Prompt construction parity only, no provider execution |
| `controlled_multi_chunk_translation_canary` | Integration - 3-chunk execution flow | ? ï? Execution mechanics only, no reader-facing continuity check |

### 5.2 Coverage Gaps

| Gap | Severity |
|-----|----------|
| **No automated test verifies pronoun resolution across chunks** | CRITICAL |
| **No test validates scene transition coherence in output** | CRITICAL |
| **No test checks narrative POV consistency** | HIGH |
| **No test validates dialogue speaker continuity** | HIGH |
| **No test checks temporal/spatial reference continuity** | HIGH |
| **No regression test for cross-chunk failure modes** | CRITICAL |
| **No deterministic boundary cases (scene break, chapter break, same scene)** | HIGH |

---

## 6. RELATIONSHIP WITH RM-8.1

| Aspect | RM-8.1 (Literary Quality) | RM-8.2 (Cross-Chunk Context) |
|--------|---------------------------|-------------------------------|
| **Scope** | Single-chunk literary naturalness | Multi-chunk discourse continuity |
| **Detection** | `_NATURALNESS_PATTERNS` (6 patterns) | ContextType enum (14 types), NarrativeState |
| **Enforcement** | `naturalness_guard_policy="literary_retry"` | Not yet implemented |
| **Metrics** | `literary_quality_hits/errors/warnings/passed` | None yet |
| **Reuses RM-8.1?** | N/A | Could reuse QA infrastructure, but different detectors |
| **Infrastructure Overlap** | `runtime_qa.py`, `ProductionOutcome` | Would need new context extraction ??QA ??outcome chain |

**Conclusion:** RM-8.1 and RM-8.2 are **orthogonal concerns**. RM-8.1 does not provide cross-chunk continuity. RM-8.2 would need its own detection/enforcement pipeline, though it could reuse the QA gate infrastructure pattern.

---

## 7. COMPLEXITY ASSESSMENT

| Capability | Classification | Rationale |
|------------|----------------|-----------|
| **Scene/Narrative Data Models** | **A ??Already Production-Integrated** | Models complete, validated, serializable |
| **Context Selection Logic** | **A ??Already Production-Integrated** | `select_context_for_translation()` complete, tested, deterministic |
| **Prompt Assembly Slots** | **A ??Already Production-Integrated** | Scene/Narrative section builders exist in prompt_runtime |
| **Knowledge Merger REPLACE Strategy** | **A ??Already Production-Integrated** | Configured for scene/narrative domains |
| **Scene Transition Logic** | **B ??Exists but Not Integrated** | `transition_scene()` exists but never called in production |
| **Context Population (Extractors)** | **D ??Missing** | No extractor creates ContextMemoryRecords from source text during translation |
| **Runtime Population Hook** | **D ??Missing** | No integration point in txt_translation_runtime / RuntimeOrchestrator |
| **Post-Translation Context Update** | **D ??Missing** | No mechanism to write translation observations back to context store |
| **Cross-Chunk QA/Metrics** | **D ??Missing** | No continuity metrics in QA report or ProductionOutcome |
| **Automated Regression Tests** | **D ??Missing** | No end-to-end continuity validation |
| **Deterministic Boundary Cases** | **D ??Missing** | No test fixtures for scene/chapter transitions |

---

## 8. PROPOSED RM-8.2 SCOPE

### 8.1 Minimum Viable Integration (If Approved)

| Phase | Work | Files to Modify |
|-------|------|-----------------|
| **1. Extractors** | Create scene/narrative extractors that populate `ContextMemoryRecord` from source chunks | New: `core/context_scene_memory/extractors.py` |
| **2. Runtime Hook** | Integrate extractor calls in `txt_translation_runtime.py` or `RuntimeOrchestrator.execute()` | `lts/txt_translation_runtime.py`, `core/runtime_orchestrator/manager.py` |
| **3. Context Carry-Forward** | Call `select_context_for_translation()` for each chunk, inject into prompt | `core/translation_quality_integration_v72/selection.py` (extend) |
| **4. Scene Boundary Detection** | Detect scene/chapter transitions, call `transition_scene()` | New: `core/context_scene_memory/boundary_detector.py` |
| **5. Post-Translation Update** | Write translation observations (speaker, POV, tense) back to context store | `lts/txt_translation_runtime.py` post-QA |
| **6. Continuity Metrics** | Add cross-chunk continuity metrics to QA report & ProductionOutcome | `core/translation_runtime/runtime_qa.py`, `core/adaptive_context_production_rollout/outcome.py` |
| **7. Tests** | Deterministic boundary cases + regression tests | New: `tests/integration/cross_chunk_continuity/` |

### 8.2 Complexity Estimate

| Factor | Assessment |
|--------|------------|
| **New Code** | ~800-1200 lines (extractors, detectors, hooks, metrics, tests) |
| **Modified Files** | 4-6 core files |
| **Provider Calls** | 0 (offline extraction) |
| **Network Calls** | 0 |
| **Regression Risk** | MEDIUM (touches prompt assembly, runtime loop) |
| **Timeline** | 2-3 implementation phases |

---

## 9. RECOMMENDATION

### RM-8.2: **SHOULD** (Conditional)

**Rationale:**

| Factor | Assessment |
|--------|------------|
| **Reader Impact** | HIGH ??Cross-chunk continuity directly affects novel readability |
| **Capability Readiness** | HIGH ??80% of infrastructure exists (models, selection, prompt slots) |
| **Integration Effort** | MEDIUM ??Mainly wiring extractors into runtime |
| **RM-8.1 Dependency** | NONE ??Independent concern |
| **Risk of Inaction** | Accumulating technical debt; continuity issues will surface in longer novels |

**Conditions for Proceeding:**
1. **RM-8.1 must complete first** (literary quality gate stabilizes the baseline)
2. **Scope must be minimal** ??Only wire existing components, no new architecture
3. **Must produce deterministic test cases** ??Scene break, chapter break, same-scene continuation
4. **Must not modify RM-7 pipeline** ??Entity/consistency/review/KE remain closed

**If NOT proceeding now:**
- Document as **DEFERRED** with clear re-evaluation trigger (e.g., "when novel >10 chunks shows continuity failures")
- Current `previous_context` tail (700 chars) provides minimal continuity for short works

---

## 10. VALIDATION COMMANDS

```powershell
python -m compileall core
# 0 errors

python ntpe_validate.py
# ALL PASS

git diff --check
# Only pre-existing CRLF warnings, no new issues
```

---

## 11. ARTIFACTS

| Artifact | Path |
|----------|------|
| RM-8.2 Preflight Report | `docs/governance/rm8/RM_8_2_PREFLIGHT_REPORT.md` |
| RM-8 Preflight (parent) | `docs/governance/rm8/RM_8_PREFLIGHT_REPORT.md` |
| RM-8.1 Preimplementation Audit | `docs/governance/rm8/RM_8_1_PREIMPLEMENTATION_AUDIT.md` |

---

## 12. FINAL VERDICT

**RM-8.2 PREFLIGHT ??COMPLETE**

| # | Question | Answer |
|---|----------|--------|
| 1 | Cross-chunk context models exist? | **YES** ??Complete in `context_scene_memory` |
| 2 | Selection logic exists? | **YES** ??`select_context_for_translation()` complete |
| 3 | Prompt assembly slots exist? | **YES** ??Scene/Narrative sections in `prompt_runtime` |
| 4 | Integrated in production runtime? | **NO** ??Domains empty in canary; no extractors hooked |
| 5 | Reader outcome validated? | **NO** ??No automated continuity tests |
| 6 | Test coverage sufficient? | **NO** ??Only unit tests for data structures |
| 7 | Complexity understood? | **YES** ??Clear A/B/D classification |
| 8 | RM-8.1 relationship clear? | **YES** ??Orthogonal, no dependency |
| 9 | Recommendation justified? | **YES** ??SHOULD (conditional on RM-8.1 completion) |

**Next Step:** Await review. If approved, produce **RM-8.2 Implementation Specification** with minimal wiring plan.

---
*End of RM-8.2 Preflight Report*
