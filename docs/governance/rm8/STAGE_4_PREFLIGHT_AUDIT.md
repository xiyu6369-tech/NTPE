# NTPE Stage 4 Preflight Audit

**Date:** 2026-08-17
**Scope:** Architecture Consolidation & Debt Resolution (P0 Stage 4)
**Commit Baseline:** Current HEAD

---

## 1. Production Entry Points

### Active Entry Points (Root)
| File | Purpose | Status |
|------|---------|--------|
| `ntpe_production_translate.py` | **Official production CLI** — txt/batch/regression/evaluate/corpus/doctor | ✅ Active |
| `ntpe_launcher.py` | GUI/offline launcher product foundation (Stage 1) | ✅ Active |
| `ntpe_batch_monitor.py` | Thin wrapper → `lts.batch_runtime_monitor` | ✅ Active |
| `ntpe_validate.py` | Project validator (required dirs, imports, compile, structure, pytest) | ✅ Active |

### Root Files Requiring Relocation (tools/)
| File | Recommended Location | Reason |
|------|---------------------|--------|
| `ntpe_controlled_real_provider_retry.py` | `tools/provider_controls/` | Provider control utility |
| `ntpe_provider_audit.py` | `tools/provider_utils/` | Provider audit utility |
| `ntpe_provider_benchmark_session.py` | `tools/provider_controls/` | Provider benchmarking |
| `ntpe_provider_setup.py` | `tools/provider_utils/` | Provider setup utility |
| `ntpe_provider_verify.py` | `tools/provider_utils/` | Provider verification |
| `ntpe_single_real_provider_invocation.py` | `tools/provider_controls/` | Single provider invocation |
| `ntpe_literary_evaluation.py` | `tools/validators/` or `tools/one_shots/` | Evaluation script |
| `ntpe_literary_regression.py` | `tools/validators/` or `tools/one_shots/` | Regression runner |

### Root Policy Compliance
- **PASS**: No Stage Scripts, Verification Scripts, Temporary Utilities, Experimental Modules, One-shot Tools in root
- **VIOLATION**: 10 utility scripts in root that must move to `tools/` subdirectories

---

## 2. Runtime Pipeline Trace

### Pipeline Mode Switch
```
NTPE_RUNTIME_PIPELINE env var (runtime/legacy, default: runtime)
```

### Runtime Pipeline (Active Default)
```
CLI (ntpe_production_translate.py)
    ↓
TranslationRuntime (core/translation_runtime/runtime.py)
    ↓
LTS txt_translation_runtime.translate_txt()
    ↓
_pipeline_mode() → "runtime"
    ↓
_translate_txt_with_runtime_pipeline()
    ↓
RuntimeOrchestrator (core/runtime_orchestrator/manager.py)
    ↓
KnowledgeRuntimeManager → PromptBuilder → TranslationRuntimeAdapter
    ↓
RuntimeSessionManager → RuntimeCheckpointManager → RuntimeTraceCollector
    ↓
TranslationEngine
```

**Components Verified:**
- ✅ `RuntimeOrchestrator` — fully implemented, version `rm-6.4.0`
- ✅ `KnowledgeRuntimeManager` — loads bundles, builds MergedRuntime
- ✅ `PromptBuilder` — assembles PromptAssembly with RM-8.2 extensions (feature-gated)
- ✅ `TranslationRuntimeAdapter` — prepares TranslationRequest
- ✅ `RuntimeSessionManager` — session lifecycle (CREATED/RUNNING/COMPLETED/FAILED)
- ✅ `RuntimeCheckpointManager` — checkpoint create/validate/resume
- ✅ `RuntimeTraceCollector` — event trace (SESSION_CREATED, CHUNK_START, CHUNK_FINISH, etc.)
- ✅ `TranslationEngine` — provider execution

### Legacy Pipeline (Available via --pipeline=legacy)
```
CLI
    ↓
TranslationRuntime
    ↓
LTS txt_translation_runtime.translate_txt()
    ↓
_pipeline_mode() → "legacy"
    ↓
Direct prompt building via LiteraryPromptBuilder
    ↓
build_prompt_package() → translate_package_with_retry()
    ↓
TranslationEngine
    ↓
Post-translation QA (runtime_qa, quality_v5, discipline, naturalness)
```

**Key Differences:**
| Aspect | Runtime Pipeline | Legacy Pipeline |
|--------|-----------------|-----------------|
| Prompt Assembly | PromptBuilder + KnowledgeRuntime | LiteraryPromptBuilder (direct) |
| Session/Checkpoint/Trace | Full RM-6 orchestration | Per-chunk resume_state.json only |
| Cross-chunk Context (RM-8.2) | Feature-gated (quality_context_scene_v72) | Not available |
| Entity Injection (RM-7.2) | Supported via metadata | Not wired (commented out) |
| Quality V5 Integration | Post-translation (same as legacy) | Post-translation |
| Discipline Runtime | Post-translation (same as legacy) | Post-translation |

### Parity Evidence
- Both pipelines produce identical post-translation quality processing
- Runtime pipeline adds: session management, checkpoint/resume, trace, cross-chunk context (when enabled)
- Legacy pipeline is simpler, battle-tested, no RM-6 overhead
- **No parity test currently exists** — regression tests run against both but no automated diff

---

## 3. EPUB Integration Gap

### Current State
```
EPUB
    ↓
EpubExtractionBoundary (core/adapters/epub_extraction_boundary.py)
    ↓
EpubExtractionResult { extracted_text, metadata, chapter_map, resources, manifest }
    ↓
ExtractedTextIntakeRequest { extracted_text, original_file_hash, epub_metadata, chapter_map, ... }
    ↓
❌ CanonicalBookIntakeAdapter.ingest_extracted() — NOT IMPLEMENTED
```

### Missing Implementation
```python
# Required in CanonicalBookIntakeAdapter:
def ingest_extracted(self, request: ExtractedTextIntakeRequest) -> CanonicalIntakeResult:
    # 1. Validate extraction result (status, warnings)
    # 2. Create SourceIdentity from original_file_hash
    # 3. Run BookIntakeProcessor on extracted_text (encoding/language/quality)
    # 4. Preserve chapter_map, metadata, resources in CanonicalIntakeResult
    # 5. Return CanonicalIntakeResult with submission_eligible flag
```

### Requirements (from Brief)
- ✅ Not breaking BookIntakeProcessor frozen contract
- ✅ Not duplicating BookIntakeProcessor core logic
- ✅ Deterministic
- ✅ Fail-closed
- ✅ Offline intake
- ✅ Preserve EPUB metadata / chapter mapping / resource tracking
- ✅ TXT & EPUB enter same canonical intake path

### Related Assets
- ✅ `EpubExtractionBoundary` — complete, validated, security-hardened
- ✅ `ExtractedTextIntakeRequest` — defined in epub_extraction_boundary.py:91
- ✅ `CanonicalBookIntakeAdapter` — exists, handles TXT via `process()` and `process_path()`
- ✅ `BookIntakeProcessor` — frozen, processes raw bytes → BookIntakeResult
- ✅ Unit tests: `tests/unit/adapters/test_epub_extraction_boundary.py`, `tests/unit/adapters/test_canonical_book_intake_adapter.py`

---

## 4. Book Preparation Mainline

### Verified Mainline (Frozen Contracts)
```
CanonicalBookIntakeAdapter.process() / process_path()
        ↓
BookIntakeProcessor.process()  ← FROZEN — do not modify core behavior
        ↓
BookIntakeResult { text, encoding, language, quality_report, status }
        ↓
BookPreparationProcessor (core/book_preparation/processor.py)
        ↓
Segmentation (core/book_segmentation)
        ↓
Chunking (core/book_chunking)
```

### BookIntakeProcessor — FROZEN
- Input: source_path (Path)
- Output: BookIntakeResult (immutable dataclass)
- Components: SourceFileReader → EncodingDetector → Decoder → TextCorruptionDetector → SourceLanguageDetector
- **Must not modify core behavior**

### BookPreparationProcessor
- Immutable result with fingerprints
- Cross-stage consistency
- Deterministic preparation
- Status: Active, maintained

---

## 5. Memory Systems — Production Reachability

### Character Memory v2 (core/character_memory_v2/)
| Module | Production Import | Status |
|--------|------------------|--------|
| `models.py` | `lts.txt_translation_runtime` (via character_memory_path) | ✅ Used |
| `store.py` | Not directly imported by runtime | ⚠️ Indirect |
| `selection.py` | Not imported | ❌ Unused |
| `normalization.py` | Not imported | ❌ Unused |
| `lifecycle.py` | Not imported | ❌ Unused |
| `deduplication.py` | Not imported | ❌ Unused |

**Runtime Usage:** `lts/txt_translation_runtime.py` loads `memory/character_memory_lts.json` via `load_json_pairs()` — **file-based, not API-based**

### Glossary
| Location | Production Import |
|----------|------------------|
| `glossary.txt` (root) | `load_locked_dictionary()` in txt_translation_runtime |
| `glossary_override.json` | Same |
| `character_override.json` | Same |
| No dedicated Glossary module in core/ | File-based only |

### Context/Scene Memory (core/context_scene_memory/)
| Module | Production Import |
|--------|------------------|
| `models.py` | `lts/txt_translation_runtime.py` (runtime pipeline, feature-gated) |
| `store.py` | `lts/txt_translation_runtime.py` (runtime pipeline, feature-gated) |
| `scene_state.py` | `lts/txt_translation_runtime.py` (runtime pipeline, feature-gated) |
| `context_selection.py` | `lts/txt_translation_runtime.py` (runtime pipeline, feature-gated) |

**Feature Gate:** `quality_context_scene_v72` (default: OFF)
- Only active when `--quality-context-scene-v72` flag passed
- Not used in legacy pipeline
- Not used in batch runtime unless explicitly enabled

### Narrative/Style Memory
| Module | Production Import |
|--------|------------------|
| `core/narrative/` | Not imported by runtime |
| `core/intelligence/narrative_engine.py` | Only in runtime pipeline (feature-gated) |
| `core/literary/` | Used by LiteraryPromptBuilder (legacy & runtime) |

---

## 6. TE v7.2 Integration (translation_quality_integration_v72)

### Components
| Component | Module | Production Wiring |
|-----------|--------|------------------|
| `PromptBudget` | `translation_quality_integration_v72.models` | Passed via TxtTranslationOptions |
| `QualityIntegrationFlags` | `translation_quality_integration_v72.flags` | CLI flags → options |
| `apply_to_prompt_package` | `translation_quality_integration_v72.adapter` | Called in `build_prompt_package()` |
| `quality_character_store_v72` | `translation_quality_integration_v72` | Option field, not yet wired to CharacterMemory v2 |
| `quality_context_scene_store_v72` | `translation_quality_integration_v72` | Option field, not yet wired to ContextMemoryStore |
| `naturalness_v72` | `translation_quality_integration_v72.renderer.NATURALNESS_POLICY` | Applied when flag enabled |

### Integration Points
1. **TxtTranslationOptions** carries all v7.2 flags and store references
2. **build_prompt_package()** calls `apply_translation_quality_integration_v72()` at end
3. **Runtime pipeline** passes stores via metadata when `quality_context_scene_v72` enabled
4. **Character/Context stores** — option fields exist but **no concrete wiring** to v2 memory stores yet

### Status
- ✅ Flags and budget plumbing complete
- ⚠️ Store wiring: option fields exist but no actual CharacterMemoryStore v2 / ContextMemoryStore instances passed in production
- ✅ Kill switch implemented (`quality_integration_kill_switch_v72`)
- ✅ PromptBudget model defined

---

## 7. Entity Resolver (core/entity_resolver/)

### Implementation Status
| Module | Status |
|--------|--------|
| `models.py` | ✅ Complete (ResolvedEntity, EntityInjectionSet, ExtractedEntity, InjectionSource) |
| `extractor.py` | ✅ Complete (EntityExtractor, KOREAN_NAME_PATTERN, build_known_entities_from_runtime) |
| `resolver.py` | ✅ Complete (EntityResolver, priority hierarchy: USER > RUNTIME > LEARNING > AUTO) |
| `injector.py` | ✅ Complete (EntityInjector, build_entity_mapping_section) |

### Production Wiring
```python
# In lts/txt_translation_runtime.py:779-781 (runtime pipeline)
# entity_injection_set = None
# if entity_resolver_available:
#     entity_injection_set = entity_resolver.resolve(chunk)
```

**Currently:** Commented out, always `None`

### PromptBuilder Interface
```python
# core/prompt_runtime/builder.py:109
sections.append(build_entity_mapping(runtime, self._entity_injection_set))
```
- Section builder exists and handles `None` gracefully
- Section name: "Entity Mapping" (fixed position after Character)

### Decision Required
- **Option A:** Complete wiring — instantiate EntityResolver in runtime pipeline, pass to PromptBuilder
- **Option B:** Remove `entity_injection_set` from PromptBuilder metadata and interface (fail-closed stub)

**Recommendation:** Option A if resolver adds translation quality value; Option B if not production-ready.

---

## 8. Controlled Runtime (core/controlled_runtime_*/)

### Module Count: 17 directories
```
controlled_runtime_adapter
controlled_runtime_atomic_authorization_consumption
controlled_runtime_atomic_scheduling_consumption
controlled_runtime_authorization_consumption
controlled_runtime_execution_authorization
controlled_runtime_execution_envelope
controlled_runtime_execution_plan
controlled_runtime_handoff_boundary
controlled_runtime_queue_admission
controlled_runtime_queue_admission_authorization
controlled_runtime_queue_admission_authorization_consumption
controlled_runtime_queue_admission_record
controlled_runtime_queue_admission_record_consumption
controlled_runtime_scheduling_authorization
controlled_runtime_scheduling_dispatch
controlled_runtime_scheduling_envelope
controlled_runtime_scheduling_envelope_consumption
controlled_runtime_submission
controlled_translation_runtime_integration
controlled_multi_chunk_translation_canary
```

### Production Reachability Audit
| Check | Result |
|-------|--------|
| Imported by `ntpe_production_translate.py` | ❌ No |
| Imported by `TranslationRuntime` | ❌ No |
| Imported by `RuntimeOrchestrator` | ❌ No |
| Imported by `LTS txt/batch runtime` | ❌ No |
| Imported by `TranslationEngine` | ❌ No |
| Imported by `Quality` modules | ❌ No |
| Imported by `core/translation_scheduler` | ✅ `ControlledRuntimeTrialContract`, `ControlledRuntimeTrialAdmissionGate` (trial only) |
| Used in tests/verification | ✅ Extensive (unit + integration + acceptance) |
| Used in canary | ✅ `controlled_multi_chunk_translation_canary` |

### Frozen Contract Dependencies
- No frozen contract (BookIntakeProcessor, TranslationRuntime, Provider boundary, Checkpoint identity) depends on Controlled Runtime

### Recommendation
**ARCHIVE** — 17 modules, architecturally complete but zero production reachability. Only trial contract in translation_scheduler references it.

---

## 9. Adaptive Context (core/adaptive_context*/)

### Module Count: 24 directories
```
adaptive_context
adaptive_context_activation_policy
adaptive_context_authorized_provider_cli
adaptive_context_authorized_provider_harness
adaptive_context_canary
adaptive_context_canary_ab
adaptive_context_canary_resume
adaptive_context_canary_validation
adaptive_context_controlled_provider_retry
adaptive_context_integration
adaptive_context_production_benchmark
adaptive_context_production_rollout
adaptive_context_production_validation
adaptive_context_profile_budget
adaptive_context_prompt_anchor
adaptive_context_provider_benchmark_session
adaptive_context_provider_evidence
adaptive_context_provider_evidence_pipeline
adaptive_context_provider_execution_freeze
adaptive_context_provider_session_cli
adaptive_context_real_provider_boundary
adaptive_context_real_provider_preflight
adaptive_context_runtime_shadow
adaptive_context_single_real_invocation
adaptive_context_strategy_selection
```

### Production Reachability Audit
| Check | Result |
|-------|--------|
| Imported by `ntpe_production_translate.py` | ✅ **Yes** — extensive imports for CLI flags (canary, shadow, rollout, policy, budget, strategy, benchmark) |
| Imported by `TranslationRuntime` | ✅ `install_txt_runtime_shadow_hook()`, `install_production_rollout_hook()` called at module load |
| Imported by `LTS txt/batch runtime` | ❌ No direct imports (hooks installed at TranslationRuntime level) |
| Imported by `RuntimeOrchestrator` | ❌ No |
| Imported by `TranslationEngine` | ❌ No |
| Used in tests/verification | ✅ Extensive canary/validation/benchmark tests |
| CLI flags exposed | ✅ 30+ flags in `ntpe_production_translate.py` regression subcommand |

### Production Hooks Installed
```python
# ntpe_production_translate.py:78-79
install_txt_runtime_shadow_hook()      # no-op unless shadow mode
install_production_rollout_hook()      # no-op unless rollout enabled
```

### Components by Category
| Category | Modules | Production Value |
|----------|---------|------------------|
| **Canary/Validation** | adaptive_context_canary, _validation, _ab, _resume | Research/validation only |
| **Production Rollout** | adaptive_context_production_rollout, _validation, _benchmark, _policy | Feature-gated hooks |
| **Strategy/Budget** | adaptive_context_strategy_selection, _profile_budget, _activation_policy | Decision support (not in pipeline) |
| **Provider Controls** | adaptive_context_authorized_provider_cli, _harness, _boundary, _preflight, _evidence* | Benchmarking/harness only |
| **Prompt Anchor** | adaptive_context_prompt_anchor | Internal utility |
| **Shadow** | adaptive_context_runtime_shadow | Shadow comparison only |

### Recommendation
- **Keep production hooks** (`runtime_shadow`, `production_rollout`) — installed but no-op by default
- **Archive canary/validation/harness/benchmark modules** to `tools/canary/` or `archive/`
- **Move CLI-only modules** (`authorized_provider_cli`, `provider_session_cli`) to `tools/provider_controls/`
- **Keep `adaptive_context` core** if used by hooks; otherwise archive

---

## 10. Legacy Quality Systems (translation_quality_*)

### translation_quality_v5 — CORE (MUST KEEP)
- ✅ `runtime_integration.py` — `run_quality_v5_phase1()`, `merge_quality_v5_into_runtime_qa()`
- ✅ `unified_quality_gate.py` — `attach_unified_report()`
- ✅ Used in both legacy and runtime pipelines
- ✅ **Do not remove**

### Modules with Zero Production Imports (Archive Candidates)
| Module | Production Import? | Used In |
|--------|-------------------|---------|
| `translation_quality_canary` | ❌ | Tests only |
| `translation_quality_corpus` | ❌ | Tests only |
| `translation_quality_corpus_governance` | ❌ | Tests only |
| `translation_quality_defects` | ❌ | Tests only |
| `translation_quality_framework_integration` | ❌ | Tests only |
| `translation_quality_metrics` | ❌ | Tests only |
| `translation_quality_provider_canary` | ❌ | Tests only |
| `translation_quality_review_artifacts` | ❌ | Tests only |
| `translation_quality_review_decision` | ❌ | Tests only |

**Note:** `translation_quality_integration_v72` is separate (TE v7.2) and actively wired.

---

## 11. Legacy Knowledge System (core/knowledge/ vs core/knowledge_runtime/)

### Dependency Check
```python
# core/knowledge_runtime/loader.py:20
# "no import from core.knowledge"
```
- ✅ **No dependency** — KnowledgeRuntime loader explicitly avoids core/knowledge
- KnowledgeRuntime uses plain dict source, no coupling to core/knowledge packages

### core/knowledge/ Structure
```
core/knowledge/
├── adapters/
├── api/
├── cache/
├── compatibility/ (legacy_mapper → v2 packages)
├── io/
├── maintenance/
├── providers/
├── repositories/
├── runtime/ (separate runtime manifest, not KnowledgeRuntime)
├── semantic/
├── snapshot/
└── synchronization/
```

### Production Reachability
| Check | Result |
|-------|--------|
| Imported by TranslationRuntime | ❌ No |
| Imported by RuntimeOrchestrator | ❌ No |
| Imported by LTS pipeline | ❌ No |
| Imported by KnowledgeRuntime | ❌ No (explicitly avoided) |
| Used in tests | ✅ Some unit tests |

### Recommendation
**Archive `core/knowledge/`** — Legacy knowledge system, fully replaced by `core/knowledge_runtime/` for production pipeline. The `compatibility/legacy_mapper` exists only to map old paths to v2 packages in `artifacts/knowledge_packages/v1/`.

---

## 12. Root Hygiene Violations

### Files to Relocate (10 files)
| Root File | Target Location |
|-----------|----------------|
| `ntpe_controlled_real_provider_retry.py` | `tools/provider_controls/` |
| `ntpe_provider_audit.py` | `tools/provider_utils/` |
| `ntpe_provider_benchmark_session.py` | `tools/provider_controls/` |
| `ntpe_provider_setup.py` | `tools/provider_utils/` |
| `ntpe_provider_verify.py` | `tools/provider_utils/` |
| `ntpe_single_real_provider_invocation.py` | `tools/provider_controls/` |
| `ntpe_literary_evaluation.py` | `tools/validators/` |
| `ntpe_literary_regression.py` | `tools/validators/` |
| `launcher_translate.py` | **Keep** (compat wrapper) or `tools/launchers/` |
| `ntpe_launcher.py` | **Keep** (entry point) or `tools/launchers/` |

### Root Policy Compliance
- ✅ Entry points: `ntpe_production_translate.py`, `ntpe_launcher.py`, `ntpe_batch_monitor.py`, `ntpe_validate.py`
- ✅ Compatibility wrapper: `launcher_translate.py` (prog="launcher_translate.py")
- ✅ README, LICENSE, git metadata, minimal config
- ❌ 10 utility scripts in root violating Root Policy

---

## 13. Frozen Contracts — No Modification Allowed

| Contract | Location | Status |
|----------|----------|--------|
| BookIntakeProcessor | `core/book_intake/intake_package.py` | ✅ FROZEN |
| Canonical Intake Contract | `core/adapters/canonical_book_intake_adapter.py` | ✅ FROZEN |
| TranslationRuntime | `core/translation_runtime/runtime.py` | ✅ FROZEN |
| Provider Boundary | `core/ai_provider/` + `core/translation_runtime/runtime_provider.py` | ✅ FROZEN |
| Checkpoint Identity | `core/runtime_checkpoint/models.py` | ✅ FROZEN |
| Deterministic Identity | `core/translation_runtime/runtime_contract.py` | ✅ FROZEN |
| Artifact Isolation | `core/translation_runtime/runtime_contract.py` | ✅ FROZEN |
| Quality Gate | `core/translation_quality_v5/unified_quality_gate.py` | ✅ FROZEN |
| Fail-closed Behavior | Throughout | ✅ FROZEN |
| Historical Evidence | `artifacts/`, `docs/releases/` | ✅ PRESERVED |

---

## 14. Validation Baseline

```powershell
# All must pass before/after each batch
python ntpe_validate.py          # ALL PASS
python -m compileall .           # 0 errors
git diff --check                 # clean
```

### Current Baseline (Verified)
```
====================================
NTPE Project Validation Report
====================================
Required directories   PASS  5 directories found
Legacy entrypoints     PASS  archive OK (3/3 legacy preserved)
Core imports           PASS  7 required imports OK
Optional imports       PASS  4 optional imports OK
Python compile         PASS  2944 Python files compile
Python cache           PASS  No Python cache artifacts found
Test inventory         PASS  886 pytest tests; 2 relocated verification wrappers
Root Python layout     PASS  13 root Python files; layout policy satisfied
------------------------------------
ALL PASS
```

---

## 15. EPUB Minimum Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| EPUB → Extraction → Canonical Intake → Book Preparation → Chunking → Translation Runtime → Quality Gate → Output | ❌ Blocked at Canonical Intake |
| Chapter mapping preserved | ✅ Extraction produces ChapterBoundary[] |
| Metadata preserved | ✅ EpubMetadata in ExtractionResult |
| Resource tracking | ✅ ResourceRef[] in ExtractionManifest |
| Source fingerprint | ✅ SHA256 of original + extracted |
| TXT/EPUB same canonical path | ❌ EPUB missing `ingest_extracted()` |
| No manual TXT conversion needed | ❌ Requires implementation |

---

## 16. Stage 4 Preflight Summary

### Critical Gaps (Must Fix)
1. **EPUB Integration** — `CanonicalBookIntakeAdapter.ingest_extracted()` missing
2. **Root Hygiene** — 10 scripts in root violating policy
3. **Entity Resolver** — Stubbed in PromptBuilder, not wired in runtime

### Archive Candidates (Zero Production Reachability)
1. **Controlled Runtime** — 17 modules, only trial contract reference
2. **Adaptive Context (canary/harness/benchmark)** — 20+ modules, only CLI flags/hooks in production
3. **Legacy Quality** — 9 modules (except v5 and v7.2 integration)
4. **Legacy Knowledge** — Entire `core/knowledge/` tree

### Keep & Consolidate
1. **Runtime Pipeline** — Active default, RM-6.4.0 complete
2. **Legacy Pipeline** — Keep until parity evidence documented
3. **Memory Systems** — Character v2, Context/Scene (feature-gated)
4. **TE v7.2** — Flags/budget wired, store wiring incomplete
5. **Book Intake/Preparation** — Frozen, working
6. **Translation Engine/Provider/Quality v5** — Core production

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking Legacy pipeline during consolidation | Medium | High | Keep legacy until parity tests pass |
| EPUB integration breaking TXT intake | Low | Medium | Implement `ingest_extracted()` as additive path |
| Archive removing hidden dependency | Low | High | Verify zero production imports before archive |
| Root hygiene breaking CI | Low | Low | Move to tools/, update any references |

---

## 17. Recommended Stage 4 Execution Order

### Batch 1: Preflight & Root Hygiene (No Production Code Changes)
- [ ] Complete this audit document
- [ ] Move 10 root scripts to `tools/` subdirectories
- [ ] Run validation baseline

### Batch 2: EPUB Integration (Additive Only)
- [ ] Implement `CanonicalBookIntakeAdapter.ingest_extracted()`
- [ ] Add unit test for EPUB → Canonical Intake → Book Preparation
- [ ] Run validation baseline

### Batch 3: Entity Resolver Decision
- [ ] Complete wiring OR remove interface stub
- [ ] Run validation baseline

### Batch 4: Archive Zero-Reachability Modules
- [ ] Archive Controlled Runtime (17 modules)
- [ ] Archive Adaptive Context canary/harness/benchmark (20+ modules)
- [ ] Archive Legacy Quality (9 modules, keep v5 + v7.2)
- [ ] Archive Legacy Knowledge (`core/knowledge/`)
- [ ] Run validation baseline after each archive

### Batch 5: Legacy Pipeline Parity Documentation
- [ ] Document feature parity matrix (runtime vs legacy)
- [ ] Add regression test comparing both pipelines
- [ ] Decide deprecation timeline

---

## 18. Stage 4 Status

**PREFLIGHT COMPLETE — READY FOR BATCH 1 EXECUTION**

All evidence collected. No production code modified. Validation baseline confirmed.