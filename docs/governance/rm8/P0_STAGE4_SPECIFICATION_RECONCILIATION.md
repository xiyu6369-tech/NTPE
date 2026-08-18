# P0 Stage 4 Specification Reconciliation Report

**Date:** 2026-08-18
**Scope:** Architecture Consolidation & Debt Resolution (P0 Stage 4)
**Baseline Commits:**
- Governance Baseline: 806ac7c8f45b44dbdf17d1ca81ae9ad590f52d72
- Stage 3 Complete: 6eba9dc82c240ac8018b5f4940dce4e8c5a07de0
- Current HEAD: (latest commit)

---

## 1. Executive Summary

This report reconciles the **Capability Value Audit** (RM-5.1 Pipeline Audit, RM-5.7.1 Capability Audits for Character, Glossary, Narrative, Scene, Style) with the **P0 Stage 4 Preflight Audit** (STAGE_4_PREFLIGHT_AUDIT.md) to determine:

1. What NTPE was originally intended to become
2. What NTPE actually contains now
3. Which capabilities are formal product capabilities vs. historical/experimental/canary
4. Where current implementation diverges from intended architecture
5. What the actual P0 Stage 4 scope should be

**Key Finding:** The reconciliation reveals a system where the **Runtime Pipeline (RM-6.4.0)** is the active default with full orchestration (session, checkpoint, trace, KnowledgeRuntime), while the **Legacy Pipeline** remains as a battle-tested fallback. The EPUB integration (Stage 3) is blocked at `CanonicalBookIntakeAdapter.ingest_extracted()` — the single missing implementation preventing TXT/EPUB canonical parity.

**Stage 4 is NOT a feature development stage.** It is a consolidation, hygiene, and architecture completion stage with 5 defined Batches.

---

## 2. Source Documents / Evidence

### Primary Governance Documents
| Document | Path | Role |
|----------|------|------|
| Repository Governance Baseline | `docs/governance/repository/REPOSITORY_GOVERNANCE_BASELINE.md` | Constitution |
| Repository Structure Spec | `docs/governance/repository/REPOSITORY_STRUCTURE_SPEC.md` | Directory map |
| Root Policy | `docs/governance/repository/ROOT_POLICY.md` | Root allowlist |
| Tools Policy | `docs/governance/repository/TOOLS_POLICY.md` | Tools categorization |
| Directory Ownership | `docs/governance/repository/DIRECTORY_OWNERSHIP.md` | Import boundaries |
| Archive Policy | `docs/governance/repository/ARCHIVE_POLICY.md` | Archival rules |

### Capability Value Audit (RM-5.1 + RM-5.7.1 series)
| Document | Path | Scope |
|----------|------|-------|
| RM-5.1 Gap Analysis | `docs/governance/rm5/RM_5_1_GAP_ANALYSIS.md` | ACTIVE/PARTIAL/DEAD/LEGACY classification |
| RM-5.1 Pipeline Audit Report | `docs/governance/rm5/RM_5_1_PIPELINE_AUDIT_REPORT.md` | 51-module evidence matrix |
| RM-5.1 Runtime Flow Map | `docs/governance/rm5/RM_5_1_RUNTIME_FLOW_MAP.md` | Production TXT flow trace |
| RM-5.1 Audit Execution Report | `docs/governance/rm5/RM_5_1_AUDIT_EXECUTION_REPORT.md` | Validation evidence |
| Character Capability Audit | `docs/governance/rm5/RM_5_7_1_CHARACTER_CAPABILITY_AUDIT.md` | CHAR-001 to CHAR-010 gaps |
| Glossary Capability Audit | `docs/governance/rm5/RM_5_7_1_GLOSSARY_CAPABILITY_AUDIT.md` | GLOSS-001 to GLOSS-009 gaps |
| Narrative Capability Audit | `docs/governance/rm5/RM_5_7_1_NARRATIVE_CAPABILITY_AUDIT.md` | NARR-001 to NARR-007 gaps |
| Scene Capability Audit | `docs/governance/rm5/RM_5_7_1_SCENE_CAPABILITY_AUDIT.md` | SCENE-001 to SCENE-007 gaps |
| Style Capability Audit | `docs/governance/rm5/RM_5_7_1_STYLE_CAPABILITY_AUDIT.md` | STYLE-001 to STYLE-008 gaps |

### Stage 4 Preflight Audit
| Document | Path | Scope |
|----------|------|-------|
| Stage 4 Preflight Audit | `STAGE_4_PREFLIGHT_AUDIT.md` | Architecture consolidation plan |

---

## 3. Original NTPE Architecture Intent

Based on the governance baseline, RM-5.1 audits, and capability audits, the original architecture intent was:

### 3.1 Intended Product Architecture (from Governance Baseline)

```
NTPE Translation Engine (Production)
├── Input Pipeline          → TXT (active) + EPUB (planned parity)
├── Canonical Intake        → BookIntakeProcessor (FROZEN) → BookPreparation → Segmentation → Chunking
├── Memory/Context Layer    → Character v2, Context/Scene v2, Narrative, Glossary, KnowledgeRuntime
├── Prompt Pipeline         → LiteraryPromptBuilder → PromptCompiler v5.5.2 → Discipline → Quality v5
├── Runtime Orchestration   → RuntimeOrchestrator (RM-6.4.0) + KnowledgeRuntime + Session/Checkpoint/Trace
├── Provider Layer          → NvidiaClient + AI Provider Manager (fallback, rate limit, retry)
├── Quality Pipeline        → Quality v5 (core) + TE v7.2 (feature-gated)
└── Output                  → Deterministic, checkpointable, resume-capable
```

### 3.2 Intended Knowledge Generation Architecture (RM-5.7.0 baseline)

The capability audits (RM-5.7.1 series) reveal an **offline knowledge generation architecture** that was designed but never fully implemented:

```
Knowledge Generation (Offline)
├── Source Ingestion        → Document Analyzer → *_auto.json
├── Extraction Agents       → CharacterExtractor, GlossaryExtractor, NarrativeExtractor, SceneExtractor, StyleExtractor (LLM-based)
├── Validation Engine       → Business rules (CH-001.., GL-001.., NR-001.., ST-001..)
├── Review & Approve        → Human-in-the-loop workflow
├── Compilation             → Unified artifacts per schema (character.json, glossary.json, narrative.json, scene.json, style.json)
└── Runtime Consumption     → KnowledgeRuntime loads bundles → PromptBuilder injection
```

**Critical Divergence:** The offline extraction agents **do not exist**. Current "extraction" is merge-only (v1.0 engines) or runtime-only guards (naturalness, voice, hallucination, collocation). The Knowledge Generation Architecture is a **design-only layer** with zero production implementation.

---

## 4. Current Architecture

### 4.1 Active Production Pipeline (Verified by RM-5.1)

```
Production TXT Translation (Active Default)
├── CLI                     → ntpe_production_translate.py (root entry)
├── TranslationRuntime      → core/translation_runtime/runtime.py (FROZEN)
├── LTS txt_translation_runtime.translate_txt()
├── _pipeline_mode() → "runtime" (env NTPE_RUNTIME_PIPELINE=runtime)
├── RuntimeOrchestrator     → core/runtime_orchestrator/manager.py (RM-6.4.0, complete)
│   ├── KnowledgeRuntimeManager
│   ├── PromptBuilder (with RM-8.2 extensions, feature-gated)
│   ├── TranslationRuntimeAdapter
│   ├── RuntimeSessionManager
│   ├── RuntimeCheckpointManager
│   └── RuntimeTraceCollector
├── TranslationEngine       → core/translation_engine/translation_engine.py
├── Provider Layer          → NvidiaClient + ProviderManager + Fallback + RateLimit
├── Post-Translation QA     → Quality v5 (runtime_integration, unified_quality_gate)
│   └── TE v7.2 integration (flags + budget wired, stores NOT wired)
└── Output                  → format_translation_output → save_file_result
```

### 4.2 Legacy Pipeline (Available via --pipeline=legacy)

```
Legacy TXT Translation (Fallback)
├── CLI                     → Same entry
├── TranslationRuntime      → Same
├── LTS txt_translation_runtime.translate_txt()
├── _pipeline_mode() → "legacy"
├── LiteraryPromptBuilder   → Direct prompt building (build_prompt_package)
├── TranslationEngine       → Same
├── Post-Translation QA     → Quality v5 + Discipline + Naturalness (same as runtime)
└── Output                  → Same
```

### 4.3 EPUB Integration Status (Stage 3 Complete, Stage 4 Blocked)

```
EPUB Path (Blocked)
├── EpubExtractionBoundary  → COMPLETE (security-hardened, validated)
├── ExtractedTextIntakeRequest → DEFINED
├── CanonicalBookIntakeAdapter → EXISTS (handles TXT via process()/process_path())
├── ❌ ingest_extracted()   → MISSING (single blocking implementation)
└── BookIntakeProcessor     → FROZEN (must not modify)
```

### 4.4 Memory/Context Systems — Production Reachability

| System | Implementation | Production Reachability | Status |
|--------|---------------|------------------------|--------|
| Character Memory v1 | `core/character_memory_engine.py` | ❌ None (offline only) | LEGACY |
| Character Memory v2 | `core/character_memory_v2/` (models, store, selection, normalization, lifecycle, deduplication) | ⚠️ File-based only via `load_json_pairs()` | PARTIAL |
| Character Resolver | `core/character_resolver.py` | ⚠️ Indirect (glossary_builder only) | PARTIAL |
| Glossary (file-based) | `glossary.txt`, `glossary_override.json` | ✅ Direct via `load_locked_dictionary()` | ACTIVE |
| Context/Scene Memory v2 | `core/context_scene_memory/` | ⚠️ Feature-gated (`quality_context_scene_v72`) | PARTIAL |
| Narrative Context (literary) | `core/literary/narrative_context.py` | ✅ Via LiteraryPromptBuilder | ACTIVE |
| Character Context (literary) | `core/literary/character_context.py` | ✅ Via LiteraryPromptBuilder | ACTIVE |
| KnowledgeRuntime | `core/knowledge_runtime/` | ⚠️ Optional soft bridge, not used in production | PARTIAL |
| Legacy Knowledge | `core/knowledge/` | ❌ Zero production imports | DEAD |

### 4.5 TE v7.2 Integration Status

| Component | Status |
|-----------|--------|
| Flags & Budget plumbing | ✅ Complete (CLI → TxtTranslationOptions → PromptBudget) |
| `apply_to_prompt_package` | ✅ Called in `build_prompt_package()` |
| Character/Context store wiring | ❌ Option fields exist, NO concrete instances passed |
| Kill switch | ✅ Implemented |
| Naturalness policy | ✅ Applied when flag enabled |

### 4.6 Entity Resolver Status

| Module | Implementation | Production Wiring |
|--------|---------------|-------------------|
| models.py | ✅ Complete | — |
| extractor.py | ✅ Complete | — |
| resolver.py | ✅ Complete | — |
| injector.py | ✅ Complete | — |
| PromptBuilder interface | ✅ `build_entity_mapping()` exists, handles None | **COMMENTED OUT** in runtime pipeline |

---

## 5. Architecture Divergence Matrix

| Dimension | Original Intent | Current Implementation | Divergence |
|-----------|----------------|------------------------|------------|
| **Input Parity** | TXT + EPUB same canonical path | TXT active, EPUB blocked at `ingest_extracted()` | **Critical Gap** |
| **Runtime Orchestration** | RM-6 full orchestration default | RM-6.4.0 complete, active default | Aligned |
| **Legacy Pipeline** | Transitional, eventual retirement | Battle-tested fallback, no parity test | **Risk: no automated parity evidence** |
| **Memory Layer** | Character v2 + Context/Scene v2 + Narrative + Glossary + KnowledgeRuntime unified | Fragmented: file-based (active), v2 stores (feature-gated), v1 (dead), literary (active) | **Partial implementation** |
| **Knowledge Generation** | Offline LLM-based extractors for all 5 domains | **ZERO extraction agents exist**; only merge (v1) or runtime guards | **Design-only, not implemented** |
| **TE v7.2** | Full quality integration with wired stores | Flags/budget wired, stores NOT wired | **Incomplete integration** |
| **Entity Resolution** | Runtime entity injection | Fully implemented, **commented out** | **Deliberate stub** |
| **Controlled Runtime** | Production scheduling/admission | 17 modules, **zero production reachability** | **Architectural dead code** |
| **Adaptive Context** | Production rollout hooks + canary | Hooks installed (no-op), 20+ canary modules unused in production | **Mixed: keep hooks, archive canary** |
| **Legacy Knowledge** | Replaced by KnowledgeRuntime | Explicitly avoided by KnowledgeRuntime loader | **Archive candidate** |
| **Root Hygiene** | Clean root per ROOT_POLICY | 10 utility scripts violating policy | **Hygiene violation** |

---

## 6. Formal Product Capabilities (Must Remain)

These capabilities are **actively used in production translation** and represent the core product value:

| Capability | Location | Evidence |
|------------|----------|----------|
| **TXT Input & Chunking** | `lts/txt_translation_runtime.py` | RM-5.1 ACTIVE |
| **Locked Dictionary (Glossary + Character Override)** | `load_locked_dictionary()` + files | RM-5.1 ACTIVE |
| **Literary Prompt Building** | `core/literary/` (narrative, character, glossary, policy) | RM-5.1 ACTIVE |
| **PromptCompiler v5.5.2** | `core/prompt_compiler/` | RM-5.1 ACTIVE |
| **Translation Discipline** | `core/translation_discipline/` | RM-5.1 ACTIVE |
| **Quality v5 Runtime Integration** | `core/translation_quality_v5/runtime_integration.py` | RM-5.1 ACTIVE |
| **Unified Quality Gate** | `core/translation_quality_v5/unified_quality_gate.py` | FROZEN |
| **Provider Layer (NvidiaClient + Manager + Fallback + RateLimit)** | `core/translation_engine/`, `core/ai_provider/` | RM-5.1 ACTIVE |
| **Runtime Orchestration (RM-6.4.0)** | `core/runtime_orchestrator/` | Preflight verified complete |
| **KnowledgeRuntime Manager** | `core/knowledge_runtime/` | Preflight verified |
| **Session/Checkpoint/Trace** | `core/runtime_session/`, `core/runtime_checkpoint/`, `core/runtime_trace/` | Preflight verified |
| **TranslationRuntime (FROZEN)** | `core/translation_runtime/runtime.py` | FROZEN |
| **Canonical Intake Contract** | `core/adapters/canonical_book_intake_adapter.py` | FROZEN |
| **BookIntakeProcessor (FROZEN)** | `core/book_intake/intake_package.py` | FROZEN |
| **BookPreparation/Segmentation/Chunking** | `core/book_preparation/`, `core/book_segmentation/`, `core/book_chunking/` | Tests/verification only |
| **EpubExtractionBoundary** | `core/adapters/epub_extraction_boundary.py` | Stage 3 complete |
| **EPUB Metadata/Chapter/Resource Preservation** | Extraction produces all required artifacts | Stage 3 complete |

---

## 7. Historical / Experimental / Canary Capabilities (Archival Candidates)

| Capability | Location | Production Reachability | Classification | Archive Readiness |
|------------|----------|------------------------|----------------|-------------------|
| **Controlled Runtime (17 modules)** | `core/controlled_runtime_*/` | ❌ Zero | ARCHIVE | READY_TO_ARCHIVE |
| **Adaptive Context Canary/Validation/Harness/Benchmark (20+ modules)** | `core/adaptive_context_canary*`, `_validation*`, `_harness*`, `_benchmark*`, `_evidence*`, `_ab`, `_resume` | ❌ CLI flags only | ARCHIVE | READY_TO_ARCHIVE |
| **Adaptive Context Provider CLI/Harness/Boundary/Preflight** | `core/adaptive_context_authorized_provider_*`, `_real_provider_*`, `_provider_evidence*`, `_provider_session_cli` | ❌ CLI only | ARCHIVE / MOVE TO TOOLS | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Adaptive Context Shadow/Rollout/Policy/Budget/Strategy/Anchor** | `core/adaptive_context_runtime_shadow`, `_production_rollout`, `_activation_policy`, `_profile_budget`, `_strategy_selection`, `_prompt_anchor` | ⚠️ Hooks installed (no-op) | KEEP HOOKS, ARCHIVE REST | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Legacy Quality (9 modules)** | `core/translation_quality_canary`, `_corpus`, `_corpus_governance`, `_defects`, `_framework_integration`, `_metrics`, `_provider_canary`, `_review_artifacts`, `_review_decision` | ❌ Zero | ARCHIVE | READY_TO_ARCHIVE |
| **Legacy Knowledge (`core/knowledge/` entire tree)** | `core/knowledge/` | ❌ Zero, explicitly avoided | ARCHIVE | READY_TO_ARCHIVE |
| **Character Memory v1 Engine** | `core/character_memory_engine.py` | ❌ None | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Character Database** | `core/character_database.py` | ❌ None | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Glossary Builder v1.1.1** | `core/glossary_builder.py` | ❌ None | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Knowledge Base Builder** | `core/knowledge_base_builder.py` | ❌ None | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Legacy Glossary Runtime** | `core/glossary.py` | ❌ None | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Legacy Context Builder/State** | `core/context/` (context_builder, character_state, scene_state, story_state, memory_engine, narrative_state) | ❌ None | DEAD PATH / ARCHIVE | READY_TO_ARCHIVE |
| **Legacy Prompt Engine** | `core/prompt_engine.py` | ❌ None | LEGACY / ARCHIVE | READY_TO_ARCHIVE |
| **Legacy Translator/Engine** | `core/translator.py`, `engine/nvidia.py` | ❌ None | LEGACY / ARCHIVE | READY_TO_ARCHIVE |
| **Translation Scheduler** | `core/translation_scheduler/` | ❌ Dead path | DEAD PATH / ARCHIVE | READY_TO_ARCHIVE |
| **Core Quality Engine** | `core/quality/` (quality_engine, quality_report, novel_engine, auto_repair) | ❌ None | DEAD PATH / ARCHIVE | READY_TO_ARCHIVE |
| **Document Normalizer/Analyzer** | `core/document_normalizer.py`, `core/document_analyzer.py` | ❌ None (standalone only) | LEGACY / ARCHIVE | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| **Legacy Chunker** | `core/chunker.py` | ❌ Replaced by LTS | LEGACY / ARCHIVE | READY_TO_ARCHIVE |

---

## 8. Memory / Entity / Context Reconciliation

### 8.1 Character Memory

| Aspect | Original Intent | Current Implementation | Production Reachability | Current Value | Divergence | Recommendation |
|--------|----------------|------------------------|------------------------|---------------|------------|----------------|
| **v1 Engine** | Merge multi-volume auto-candidates, apply overrides, export JSON/CSV | `character_memory_engine.py` — complete merge logic, confidence scoring, alias tracking | ❌ None (offline only) | Historical evidence, CSV reports | Replaced by v2 design | ARCHIVE after v2 migration |
| **v2 Store** | Structured fact store (13 FactTypes, 7 EvidenceTypes, immutable records, evidence ranking, conflict resolution, snapshots, token budgets) | `core/character_memory_v2/` — models, store, selection, normalization, lifecycle, deduplication complete | ⚠️ File-based `load_json_pairs()` only, NOT API-based | **High** — designed for runtime context injection | Not wired to runtime API | **Complete API wiring** (Batch 3) |
| **Resolver** | Alias resolution with priority hierarchy for runtime | `character_resolver.py` — complete with collision guard, longest-match, glossary integration | ⚠️ Indirect (glossary_builder only) | **High** — fixes name consistency | Not used in active translation runtime | **Wire to runtime** (Batch 3) |
| **Database** | Build match dictionary for translation | `character_database.py` — priority rules, regex patterns, multi-language | ❌ None | Downstream of v1 only | Obsolete path | ARCHIVE |

**Key Gap (CHAR-003):** No LLM-based CharacterExtractor agent exists. Current "extraction" is merge-only from Document Analyzer output.

### 8.2 Glossary

| Aspect | Original Intent | Current Implementation | Production Reachability | Current Value | Divergence | Recommendation |
|--------|----------------|------------------------|------------------------|---------------|------------|----------------|
| **Builder v1.1.1** | Merge auto-candidates, apply overrides, export structured glossary + alias index | `glossary_builder.py` — merge, classification, confidence, alias index | ❌ None | Structured offline artifact | Runtime uses text file instead | Migrate runtime to structured artifact |
| **Runtime (v1)** | Load text file, generate prompt block, enforce terms, fix output | `core/glossary.py` — text file loader, hardcoded fixes | ❌ None | **ACTIVE** via `load_locked_dictionary()` reading text files | **Active but legacy implementation** | **Migrate to structured artifact** |
| **Knowledge Base Builder** | Unify character + glossary into single knowledge base | `knowledge_base_builder.py` — alias index, locked index, prompt dictionary | ❌ None | Integration artifact | No runtime consumer | ARCHIVE |

**Key Gap (GLOSS-003, GLOSS-007):** No LLM-based GlossaryExtractor; runtime uses text file not structured artifact.

### 8.3 Context / Scene Memory

| Aspect | Original Intent | Current Implementation | Production Reachability | Current Value | Divergence | Recommendation |
|--------|----------------|------------------------|------------------------|---------------|------------|----------------|
| **Scene Memory v2** | Structured scene/context store (15 ContextTypes, SceneParticipant, UnresolvedReference, BoundaryType, evidence ranking, conflict resolution, snapshots) | `core/context_scene_memory/` — models, store, scene_state, context_selection complete | ⚠️ Feature-gated (`quality_context_scene_v72`) | **High** — designed for cross-chunk context | Only active when flag enabled | **Complete wiring** (remove feature gate after validation) |
| **Legacy Scene State** | Keyword-based location/weather/mood/object tracking | `core/context/scene_state.py` | ❌ None | Hardcoded Korean→Chinese mappings | Dead path | ARCHIVE |
| **Context Intelligence** | Runtime context analysis for prompt enhancement | `context_intelligence.py` — profile detection, snapshot, entity/location extraction, tone, narrative state | ✅ Active in both pipelines | **Active runtime analysis** | Keyword/regex only, no LLM semantic | Keep as runtime enhancer |

**Key Gap (SCENE-002, SCENE-003):** No LLM-based SceneExtractor; no scene boundary detection from source.

### 8.4 Narrative / Style Systems

| Aspect | Original Intent | Current Implementation | Production Reachability | Current Value | Divergence | Recommendation |
|--------|----------------|------------------------|------------------------|---------------|------------|----------------|
| **Narrative Types (Scene Memory)** | PlotPoint, Timeline, WorldRule schemas defined | `core/context_scene_memory/models.py` — complete type definitions | ❌ Types only, no extraction | Schema evidence only | **Types exist, zero pipeline** | Define NarrativeExtractor (future) |
| **Context Intelligence** | Narrative state detection, summarization, tone | 180-char summary, 5-state tone detection | ✅ Active | Limited runtime signal | Very limited scope | Keep as-is |
| **Prompt Intelligence** | Text profile detection, profile-aware directives | 5-profile classification, directive injection | ✅ Active | Coarse classification | No extraction, classification only | Keep as-is |
| **Style (Naturalness Suite)** | Canonicalization, collocation repair, freezing, hallucination guard, voice/register guard | 6 modules, all runtime guards | ✅ Active (defensive) | **Active quality guards** | **No positive style extraction** | Define StyleExtractor (future) |

**Key Gaps (NARR-002..005, STYLE-001..005):** Zero LLM-based extraction agents for narrative, scene, or style. All current capabilities are runtime analysis/guards only.

### 8.5 Entity Resolver

| Aspect | Original Intent | Current Implementation | Production Reachability | Current Value | Divergence | Recommendation |
|--------|----------------|------------------------|------------------------|---------------|------------|----------------|
| **Full Resolver** | Priority hierarchy (USER > RUNTIME > LEARNING > AUTO), extraction, injection | 4 modules complete (models, extractor, resolver, injector) | ❌ **Commented out** in runtime pipeline | **High potential** — fixes entity consistency | Deliberately stubbed | **Option A: Complete wiring** (Batch 3) |
| **PromptBuilder Interface** | Entity Mapping section after Character | `build_entity_mapping()` exists, handles None | ⚠️ Interface ready, no data | Ready | Waiting for resolver wiring | Wire or remove interface |

---

## 9. Runtime vs Legacy Reconciliation

| Dimension | Runtime Pipeline (Default) | Legacy Pipeline (Fallback) | Assessment |
|-----------|---------------------------|---------------------------|------------|
| **Orchestration** | RuntimeOrchestrator (RM-6.4.0) — Session, Checkpoint, Trace, KnowledgeRuntime | Direct LTS path, per-chunk resume_state.json only | Runtime superior for reliability |
| **Prompt Assembly** | PromptBuilder + KnowledgeRuntime + RM-8.2 extensions (feature-gated) | LiteraryPromptBuilder direct | Runtime more extensible |
| **Cross-Chunk Context** | Feature-gated via `quality_context_scene_v72` (Scene Memory v2) | Not available | Runtime exclusive capability |
| **Entity Injection** | Supported via metadata (stubbed) | Not wired | Runtime capability (if wired) |
| **Quality V5 Integration** | Post-translation (same) | Post-translation (same) | Parity |
| **Discipline Runtime** | Post-translation (same) | Post-translation (same) | Parity |
| **Provider Layer** | Same (NvidiaClient + Manager) | Same | Parity |
| **Checkpoint/Resume** | Full RM-6 checkpoint manager | Per-chunk JSON only | Runtime superior |
| **Trace/Observability** | Full event trace | None | Runtime superior |
| **Complexity** | Higher (RM-6 overhead) | Lower, battle-tested | Legacy simpler |
| **Parity Evidence** | **NO AUTOMATED PARITY TEST EXISTS** | Regression runs against both, no diff | **Critical Gap** |

**Conclusion:** Both pipelines should remain **until automated parity evidence is documented**. Legacy provides safety net; Runtime provides architectural completeness. Retirement of Legacy requires:
1. Automated parity test suite passing
2. Feature parity documented (cross-chunk context, entity injection, checkpoint/resume)
3. Production validation period with both active

---

## 10. EPUB Stage 3 → Stage 4 Gap

### Stage 3 Delivered (Commit 6eba9dc)
- ✅ `EpubExtractionBoundary` — complete, security-hardened, validated
- ✅ `ExtractedTextIntakeRequest` — defined with all required fields
- ✅ `CanonicalBookIntakeAdapter` — exists, handles TXT via `process()`/`process_path()`
- ✅ `BookIntakeProcessor` — frozen, working
- ✅ Unit tests for extraction boundary and adapter

### Stage 4 Gap (Single Blocking Implementation)
```
MISSING: CanonicalBookIntakeAdapter.ingest_extracted(request: ExtractedTextIntakeRequest) -> CanonicalIntakeResult

Required implementation:
1. Validate extraction result (status, warnings)
2. Create SourceIdentity from original_file_hash
3. Run BookIntakeProcessor on extracted_text (encoding/language/quality)
4. Preserve chapter_map, metadata, resources in CanonicalIntakeResult
5. Return CanonicalIntakeResult with submission_eligible flag
```

**This is the ONLY production code change required for EPUB parity.** All other Stage 4 work is consolidation/hygiene.

---

## 11. Archive Safety Review

Per ARCHIVE_POLICY and Preflight Audit, every archive candidate assessed:

| Candidate | Prod Reach | Test Reach | Frozen Contract Dep | Hist Evidence | Compat Dep | Doc Dep | Artifact Dep | Hidden Import Risk | Reversible | Future Batch Safe | Classification |
|-----------|------------|------------|---------------------|---------------|------------|---------|--------------|-------------------|------------|-------------------|----------------|
| Controlled Runtime (17) | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low (trial contract only) | ✅ | ✅ | READY_TO_ARCHIVE |
| Adaptive Context Canary/Val/Harness/Bench (20+) | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Adaptive Context Provider CLI/Harness/Boundary | ❌ (CLI only) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP (move to tools first) |
| Adaptive Context Shadow/Rollout/Policy/Strategy | ⚠️ Hooks | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | Low (hooks no-op) | ✅ | ⚠️ | KEEP HOOKS, ARCHIVE REST |
| Legacy Quality (9) | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Legacy Knowledge (`core/knowledge/`) | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low (explicitly avoided) | ✅ | ✅ | READY_TO_ARCHIVE |
| Character v1 Engine | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ (CSV/JSON outputs) | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Character Database | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ (JSON output) | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Glossary Builder v1 | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ (JSON/CSV) | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Knowledge Base Builder | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ (JSON) | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Legacy Glossary Runtime | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Legacy Context Builder/State | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Legacy Prompt Engine | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Legacy Translator/Engine | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Translation Scheduler | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Core Quality Engine | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |
| Document Normalizer/Analyzer | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | ARCHIVE_AFTER_DEPENDENCY_CLEANUP |
| Legacy Chunker | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | Low | ✅ | ✅ | READY_TO_ARCHIVE |

**Critical Safety Rule:** No archival action in this task. All archival occurs in Batch 4 with validation baseline after each archive.

---

## 12. Frozen Contracts (Explicitly Protected)

Per Preflight Audit and Governance Baseline, these contracts are **FROZEN — NO MODIFICATION ALLOWED**:

| Contract | Location | Protection Basis |
|----------|----------|------------------|
| **BookIntakeProcessor** | `core/book_intake/intake_package.py` | FROZEN per Preflight §4, Governance |
| **Canonical Intake Contract** | `core/adapters/canonical_book_intake_adapter.py` | FROZEN per Preflight §13 |
| **TranslationRuntime** | `core/translation_runtime/runtime.py` | FROZEN per Preflight §13 |
| **Provider Boundary** | `core/ai_provider/` + `core/translation_runtime/runtime_provider.py` | FROZEN per Preflight §13 |
| **Checkpoint Identity** | `core/runtime_checkpoint/models.py` | FROZEN per Preflight §13 |
| **Deterministic Identity** | `core/translation_runtime/runtime_contract.py` | FROZEN per Preflight §13 |
| **Artifact Isolation** | `core/translation_runtime/runtime_contract.py` | FROZEN per Preflight §13 |
| **Quality Gate** | `core/translation_quality_v5/unified_quality_gate.py` | FROZEN per Preflight §13 |
| **Fail-closed Behavior** | Throughout pipeline | FROZEN per Preflight §13 |
| **Historical Evidence** | `artifacts/`, `docs/releases/` | PRESERVED per Archive Policy |

**No Stage 4 Batch may silently break these.** All Batches must validate against `ntpe_validate.py` baseline.

---

## 13. Required Architecture Corrections

Based on the divergence matrix, these corrections are required (not optional):

| Correction | Reason | Batch |
|------------|--------|-------|
| **Implement `CanonicalBookIntakeAdapter.ingest_extracted()`** | EPUB/TXT canonical parity — single blocking gap | Batch 2 |
| **Move 10 root utility scripts to `tools/`** | Root Policy violation (ROOT_POLICY.md) | Batch 1 |
| **Wire Character Memory v2 API to runtime** (replace file-based `load_json_pairs()`) | Formal product capability designed for runtime, currently unused | Batch 3 |
| **Wire Character Resolver to runtime** | Formal capability, fully implemented, deliberately stubbed | Batch 3 |
| **Wire Entity Resolver to runtime** (Option A) or remove PromptBuilder interface (Option B) | Deliberate stub, interface exists | Batch 3 |
| **Complete TE v7.2 store wiring** (CharacterMemoryStore v2, ContextMemoryStore instances) | Flags/budget wired, stores not passed | Batch 3 |
| **Remove `quality_context_scene_v72` feature gate** (after validation) | Scene Memory v2 is formal capability, should be default | Batch 3/5 |
| **Add automated Legacy ↔ Runtime parity test** | Critical missing evidence for Legacy retirement decision | Batch 5 |
| **Archive zero-reachability modules** | Governance compliance, reduce complexity | Batch 4 |

---

## 14. Proposed P0 Stage 4 Batches

### Batch 1: Preflight & Root Hygiene (No Production Code Changes)
- **Batch ID:** P0-S4-B1
- **Purpose:** Achieve Root Policy compliance; establish clean baseline
- **Problem Being Solved:** 10 utility scripts violate ROOT_POLICY.md at repository root
- **Current Gap:** Root contains provider controls, validators, evaluation scripts that belong in `tools/`
- **Expected Outcome:** Clean root (only entry points, metadata, config); all utilities in `tools/` subdirectories
- **Production Files Potentially Affected:** None (root scripts only)
- **Frozen Contracts Protected:** All (no production code touched)
- **Files Explicitly Forbidden to Modify:** All core/, tests/, lts/ production code
- **Dependencies:** None
- **Validation Requirements:** `python ntpe_validate.py` → ALL PASS; `python -m compileall` → 0 errors; `git diff --check` → clean
- **Acceptance Criteria:** Root passes validator; 10 files relocated to correct `tools/` categories
- **Rollback Considerations:** Git revert; files moved not deleted
- **Commit Boundary:** Single commit "P0 Stage 4 Batch 1: Root hygiene — move 10 scripts to tools/"
- **Push Boundary:** Push after validation passes

### Batch 2: EPUB Integration (Additive Only)
- **Batch ID:** P0-S4-B2
- **Purpose:** Unblock EPUB → canonical intake → translation path
- **Problem Being Solved:** Stage 3 delivered extraction but `ingest_extracted()` missing — EPUB cannot enter translation pipeline
- **Current Gap:** Single method implementation in `CanonicalBookIntakeAdapter`
- **Expected Outcome:** EPUB files translate via same canonical path as TXT; chapter mapping, metadata, resources preserved
- **Production Files Potentially Affected:** `core/adapters/canonical_book_intake_adapter.py` (ADDITIVE only — new method)
- **Frozen Contracts Protected:** BookIntakeProcessor (unchanged), Canonical Intake Contract (extended), TranslationRuntime
- **Files Explicitly Forbidden to Modify:** BookIntakeProcessor, TranslationRuntime, Provider Boundary, Quality Gate
- **Dependencies:** Batch 1 complete (clean baseline)
- **Validation Requirements:** `ntpe_validate.py` ALL PASS; unit test for EPUB → Canonical Intake → Book Preparation; manual EPUB translation smoke test
- **Acceptance Criteria:** EPUB translates end-to-end; TXT path unchanged; chapter_map/metadata preserved in output artifacts
- **Rollback Considerations:** Git revert single method; additive change only
- **Commit Boundary:** Single commit "P0 Stage 4 Batch 2: Implement CanonicalBookIntakeAdapter.ingest_extracted() for EPUB parity"
- **Push Boundary:** Push after validation + smoke test

### Batch 3: Memory/Context/Entity Wiring & TE v7.2 Completion
- **Batch ID:** P0-S4-B3
- **Purpose:** Activate formal product capabilities currently feature-gated or stubbed
- **Problem Being Solved:** Character v2, Context/Scene v2, Entity Resolver, TE v7.2 stores — all implemented but not wired to production runtime
- **Current Gap:** File-based character loading; Entity Resolver commented out; TE v7.2 store fields empty; Scene Memory feature-gated
- **Expected Outcome:** Runtime uses CharacterMemory v2 API; Entity Resolver active; TE v7.2 stores wired; Scene Memory default-on (gate removed after validation)
- **Production Files Potentially Affected:** `lts/txt_translation_runtime.py` (wiring changes), `core/prompt_runtime/builder.py` (entity injection), TE v7.2 adapter
- **Frozen Contracts Protected:** All frozen contracts (wiring only, no contract changes)
- **Files Explicitly Forbidden to Modify:** BookIntakeProcessor, TranslationRuntime, Provider Boundary, Quality Gate, Checkpoint Identity
- **Dependencies:** Batch 1, 2 complete
- **Validation Requirements:** `ntpe_validate.py` ALL PASS; regression tests pass (both pipelines); character/entity/context injection verified in output
- **Acceptance Criteria:** Character v2 API used (not file-based); Entity Resolver injects mappings; TE v7.2 stores populated; Scene Memory active by default; both pipelines produce equivalent quality
- **Rollback Considerations:** Feature flags allow gradual rollback; git revert wiring changes
- **Commit Boundary:** Single commit "P0 Stage 4 Batch 3: Wire Character v2, Entity Resolver, TE v7.2 stores, enable Scene Memory"
- **Push Boundary:** Push after full regression validation

### Batch 4: Archive Zero-Reachability Modules
- **Batch ID:** P0-S4-B4
- **Purpose:** Remove architectural dead code; comply with governance; reduce complexity
- **Problem Being Solved:** 60+ modules with zero production reachability pollute core/; violate "core/ is production-only" principle
- **Current Gap:** Controlled Runtime, Adaptive Context canary, Legacy Quality, Legacy Knowledge, Legacy systems all in core/
- **Expected Outcome:** Archived to `archive/` with frozen manifests; core/ contains only production-reachable code
- **Production Files Potentially Affected:** None (archive targets have zero production imports)
- **Frozen Contracts Protected:** All (verified zero dependency before each archive)
- **Files Explicitly Forbidden to Modify:** Any production-reachable code; frozen contracts
- **Dependencies:** Batch 1, 2, 3 complete (wiring done before archival)
- **Validation Requirements:** `ntpe_validate.py` ALL PASS **after each archive sub-batch**; full test suite; verify no import breaks
- **Acceptance Criteria:** All archive candidates moved; manifests created; validator passes; tests pass; core/ import graph clean
- **Rollback Considerations:** Archive is copy-restore (not move-delete); SHA-256 manifests enable exact restoration
- **Commit Boundary:** Multiple commits per archive category (Controlled Runtime, Adaptive Context canary, Legacy Quality, Legacy Knowledge, Legacy Systems)
- **Push Boundary:** Push after each sub-batch validates

### Batch 5: Legacy Pipeline Parity Documentation & Deprecation Decision
- **Batch ID:** P0-S4-B5
- **Purpose:** Produce evidence for Legacy retirement decision; document feature parity
- **Problem Being Solved:** No automated parity test exists; retirement decision cannot be evidence-based
- **Current Gap:** Regression runs against both pipelines but no automated diff; feature matrix incomplete
- **Expected Outcome:** Parity matrix documented; automated parity test added; deprecation timeline decided (or not)
- **Production Files Potentially Affected:** Test files only (new parity test); documentation
- **Frozen Contracts Protected:** All
- **Files Explicitly Forbidden to Modify:** Production runtime code
- **Dependencies:** Batch 1-4 complete
- **Validation Requirements:** Parity test passes (or documents differences); `ntpe_validate.py` ALL PASS
- **Acceptance Criteria:** Parity matrix complete; automated test in CI; decision recorded (retain/deprecate/retire)
- **Rollback Considerations:** Documentation only; no production risk
- **Commit Boundary:** Single commit "P0 Stage 4 Batch 5: Legacy/Runtime parity documentation and deprecation decision"
- **Push Boundary:** Push after documentation complete

---

## 15. Batch Dependency Graph

```
P0-S4-B1 (Root Hygiene)
    │
    ├──→ P0-S4-B2 (EPUB Integration) ──→ P0-S4-B3 (Memory/Context/Entity Wiring)
    │                                        │
    │                                        └──→ P0-S4-B4 (Archive Zero-Reachability)
    │                                                      │
    └──────────────────────────────────────────────────────→ P0-S4-B5 (Parity Documentation)
```

**Critical Path:** B1 → B2 → B3 → B4 → B5 (sequential, each validates before next)

---

## 16. Validation Strategy

### Per-Batch Validation (Mandatory)
```powershell
# After EVERY batch commit:
python ntpe_validate.py          # ALL PASS
python -m compileall .           # 0 errors
git diff --check                 # clean
pytest tests/ -x                 # Full test suite passes
```

### Batch-Specific Validation
| Batch | Additional Validation |
|-------|----------------------|
| B1 | Root allowlist compliance; tools/ structure compliance |
| B2 | EPUB translation smoke test; TXT regression unchanged; chapter_map/metadata in artifacts |
| B3 | Both pipelines regression; character/entity/context injection verified; TE v7.2 flags functional |
| B4 | After EACH archive sub-batch: validator + full test suite; verify no import errors |
| B5 | Parity test executes; matrix document complete; decision recorded |

### Quality Gates
- **Translation Quality:** No regression in literary evaluation scores
- **Performance:** No significant latency increase (>5% threshold)
- **Reliability:** Checkpoint/resume works in both pipelines
- **Determinism:** Same input → same output (fingerprint verified)

---

## 17. Acceptance Criteria (Stage 4 Complete)

| Criterion | Status Target |
|-----------|---------------|
| Root Policy compliant (0 violations) | ✅ |
| EPUB translates via canonical path (TXT/EPUB parity) | ✅ |
| Character Memory v2 API wired (file-based replaced) | ✅ |
| Character Resolver active in runtime | ✅ |
| Entity Resolver wired (Option A) or interface removed (Option B) | ✅ |
| TE v7.2 stores wired (Character + Context) | ✅ |
| Scene Memory v2 default-on (feature gate removed) | ✅ |
| All zero-reachability modules archived with manifests | ✅ |
| Legacy/Runtime parity test automated and documented | ✅ |
| Deprecation decision for Legacy Pipeline recorded | ✅ |
| All validation baselines pass throughout | ✅ |
| No frozen contract modified | ✅ |

---

## 18. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking Legacy pipeline during B3 wiring | Medium | High | Keep Legacy until B5 parity evidence; feature flags for rollback |
| EPUB integration breaking TXT intake (B2) | Low | Medium | Additive implementation only; BookIntakeProcessor untouched |
| Archive removing hidden dependency (B4) | Low | High | Verify zero production imports per ARCHIVE_POLICY; validate after each sub-batch |
| Root hygiene breaking CI (B1) | Low | Low | Move to tools/, update any references; validator catches issues |
| TE v7.2 store wiring causing quality regression (B3) | Medium | Medium | Kill switch (`quality_integration_kill_switch_v72`) available; gradual rollout |
| Entity Resolver wiring introducing prompt bloat (B3) | Low | Medium | PromptBudget limits; monitor token usage |
| Parity test revealing fundamental incompatibility (B5) | Medium | High | Document differences; decide retain/deprecate based on evidence |

---

## 19. Unresolved Questions

1. **Entity Resolver Decision (Batch 3):** Option A (complete wiring) vs Option B (remove interface). Requires product owner decision on whether resolver adds translation quality value.

2. **Legacy Pipeline Retirement Timeline (Batch 5):** Parity evidence may show Legacy is still required for certain edge cases. Decision: retain indefinitely / deprecate with timeline / retire immediately.

3. **TE v7.2 Store Wiring Source (Batch 3):** CharacterMemoryStore v2 and ContextMemoryStore instances must be instantiated and populated. Source: file-based migration? Runtime learning? Human-approved seeds? Not specified in current architecture.

4. **Scene Memory v2 Default-On Timing (Batch 3/5):** Remove feature gate immediately after B3 validation, or wait for B5 parity evidence? Current recommendation: remove after B3 validation passes.

5. **Knowledge Generation Architecture (Future):** The RM-5.7.0 offline extraction agents (CharacterExtractor, GlossaryExtractor, NarrativeExtractor, SceneExtractor, StyleExtractor) are **design-only**. Whether to implement in P1+ is unresolved.

---

## 20. Final Recommendation

### Specification Reconciliation Status: **CLEAR**

**P0 Stage 4 Formal Specification may now be prepared.**

### Rationale:
1. **All evidence sources reconciled** — Capability Value Audit (RM-5.1 + RM-5.7.1 series) and P0 Stage 4 Preflight Audit agree on current state
2. **Divergences explicitly documented** — No silent assumptions; every gap identified
3. **Frozen contracts identified and protected** — 10 contracts, no Batch modifies them
4. **Archive safety reviewed** — All candidates classified with readiness; no archival in this task
5. **Batches justified by mandatory rules** — Each Batch solves a specific problem (quality, stability, hygiene, architecture completion, obsolete complexity removal)
6. **Dependencies ordered** — Critical path clear, validation gates defined
7. **Stage 3 baseline respected** — EPUB gap isolated to single additive implementation
8. **Governance compliance** — All Batches comply with REPOSITORY_GOVERNANCE_BASELINE.md

### Next Step:
**Prepare P0 Stage 4 Formal Specification** — detailed implementation specification for each Batch with exact file changes, test requirements, and acceptance criteria. Do NOT begin implementation until specification is reviewed and approved.

---

## Appendix: Key Commit References

| Milestone | Commit | Description |
|-----------|--------|-------------|
| Governance Baseline | 806ac7c8f45b44dbdf17d1ca81ae9ad590f52d72 | REPOSITORY_GOVERNANCE_BASELINE.md |
| Stage 1A+1B Productization | a0d6fc1 | Governance + Deterministic Identity |
| Stage 2 Legacy Path Fix | ca1c36f | Provenance metadata persistence |
| **Stage 3 EPUB Complete** | **6eba9dc82c240ac8018b5f4940dce4e8c5a07de0** | **EpubExtractionBoundary implemented** |
| RM-8.5 Phase 1 | 3199039 | Translation release validator |
| RM-8.5 Phase 2 | 1ee85bf | Specification correction |

---

**Report Generated:** 2026-08-18
**Authorization:** READ-ONLY / SPECIFICATION RECONCILIATION ONLY
**No production code modified. No archival executed. No implementation performed.**