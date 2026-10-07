# NTPE S13-04 — QA Guard Inventory

Companion to `artifacts/NTPE_S13_04_QA_GUARD_AUDIT.md`. Baseline HEAD `e08c1dc`.
Audit-only; no code modified.

Classification vocabulary: `CANONICAL / KEEP`, `CONSOLIDATION CANDIDATE`, `DEAD CODE`,
`LEGACY`, `TEST-ONLY`, `DEFERRED`, `UNKNOWN`.

## 1. Canonical-path guard inventory

| Guard | File | Caller (production) | Responsibility | Result | Canonical? |
|---|---|---|---|---|---|
| `BasicTranslationQA.check` | `core/translation_engine/basic_qa.py:6` | `TranslationEngine.translate_package` / `translate_package_from_request` (`translation_engine.py:117,249`) | Korean residue, short length, locked-name missing | `{"passed","issues",...}` -> `provider_result["qa"]` | CANONICAL (EPUB carries; TXT discards) |
| `analyze_runtime_quality` | `core/translation_runtime/runtime_qa.py:124` | `analyze_translation_quality` (`txt:1407`); `TranslationRuntime.analyze_quality` (`runtime.py:259`) | length / Korean / repeats / simplified / dialogue / naturalness / locked-term / quality-lock | `{"passed","enabled","issues","metrics"}` | CANONICAL (TXT) |
| `RuntimeQAPolicy` | `runtime_qa.py:25` | `analyze_translation_quality` (`txt:1396`); `TranslationRuntime` (`runtime.py:48`) | policy envelope | dataclass | CANONICAL (TXT) |
| `analyze_translation_quality` | `lts/txt_translation_runtime.py:1388` | `_translate_txt_with_runtime_pipeline` (`txt:954`); `lts/quality_validation.py:111` | back-compat wrapper delegating to `runtime_qa` | same as runtime_qa | CANONICAL / KEEP (wrapper) |
| `run_quality_v5_phase1` | `core/translation_quality_v5/runtime_integration.py` | `txt:933` | v5 quality baseline/phase1 | report | CANONICAL (TXT advisory) |
| `merge_quality_v5_into_runtime_qa` -> `run_unified_quality_gate` | `core/translation_quality_v5/runtime_integration.py:91` / `unified_quality_gate.py:70` | `txt:938` | merge v5 + legacy into unified report; dedup; discipline enforce | unified report | CANONICAL (TXT advisory) |
| `attach_unified_report` | `unified_quality_gate.py:175` | `txt:975` | attach v5.3.1 fields | dict | CANONICAL (TXT) |
| `orchestrate_runtime_discipline` | `core/translation_discipline/runtime_orchestrator.py:101` | `txt:963` | adaptive local-repair / retry decision | `DisciplineRuntimeOutcome` (text discarded) | CANONICAL invocation, DIAGNOSTIC ONLY |
| `DisciplineQualityEnforcer` / `UnifiedQualityGateAdapter` | `core/translation_discipline/quality_enforcement.py:59` | `run_unified_quality_gate` (`unified_quality_gate.py:126`) | enforce/normalise unified decision | report | CANONICAL (via v5) |
| `canonicalize_novel_chinese` / `apply_literary_collocation_guard` / `analyze_voice_register` | `core/translation_naturalness/*` | `txt:924-928`; `delivery_pipeline.py:110-112` | post-process normalisation / analysis | result (voice result discarded) | CANONICAL / KEEP (not a gate) |
| glossary snapshot validation (`verify_snapshot_file`, hash gate) | glossary/store modules | TXT/EPUB launch | glossary binding | raises on invalid | CANONICAL (separate contract) |
| EPUB ZIP security guards (`_validate_zip_security`) | epub extraction | EPUB intake | entry/size/traversal/zip-bomb | raises | CANONICAL (separate contract) |
| `validate_epub_translation_chunk` (offset) | `core/epub_translation/contract/validation.py` | EPUB adapter E2E | chunk offset contract | raises | CANONICAL (separate contract) |
| `TranslationValidator.validate` | `core/translation_engine/validator.py` | `TranslationOrchestrator.process_segment` (`orchestrator.py:87`) | length/Korean/etc. | `ValidationResult` | SECONDARY (SDK only) |

## 2. Dead / orphaned QA symbols

| Guard / function | File:line | Caller | Responsibility | Result | Canonical? |
|---|---|---|---|---|---|
| `Validator` | `core/validator.py:14` | none | forbidden/AI phrases, bad names, Korean, length, repeats, glossary terms | `ValidationResult` | DEAD CODE |
| `should_soft_fail_naturalness` | `runtime_qa.py:287` | none | balanced naturalness-only detection | bool | DEAD CODE |
| `soft_fail_naturalness_report` | `runtime_qa.py:306` | none (unused import `txt:32`) | downgrade naturalness-only failure | dict | DEAD CODE |
| `has_retry_worthy_naturalness_issue` | `txt:1742` | none | detect retry-worthy naturalness | bool | DEAD CODE |
| `qa_retry_delay_seconds` | `txt:1418` | none | QA retry backoff | float | DEAD CODE |
| `build_qa_retry_user_prompt` | `txt:1655` | tests only | build issue-directed retry prompt | str | TEST-ONLY (legacy) |
| `lts.detect_repeated_lines` / `lts.detect_simplified_chinese` | `txt:1324,1337` | tests / legacy | primitive detectors duplicating `runtime_qa.py:55,93` | list | LEGACY / TEST-ONLY |

## 3. Unused imports in canonical files

| Import | File:line | Evidence |
|---|---|---|
| `RuntimeQAPolicy, analyze_runtime_quality` | `core/epub_translation/runtime/adapter.py:43` | only occurrence in file; never referenced |
| `soft_fail_naturalness_report` | `lts/txt_translation_runtime.py:32` | only occurrence in file; never referenced |

## 4. Inert declared contract

| Item | File:line | Evidence |
|---|---|---|
| `qa_fail_policy` option | `txt:128`; `batch_translation_runtime.py:115`; UI/CLI pass-through | declared + parsed (`txt:2043`), consumed by no branch on the runtime path |
| resume statuses `qa_failed` / `failed_chunk` | `lts/long_run_recovery.py:116`; `lts/batch_translation_runtime.py:236`; `lts/batch_runtime_monitor.py:51` | read-only consumers; no producer on the canonical path |

## 5. Legacy QA subsystems (no production caller)

| Subsystem | Files | Importer evidence | Canonical? |
|---|---|---|---|
| Stage-15 quality engine | `core/quality/` (33 files) | `engine/pipeline/*` (dead), `core/expansion/*` (dead), `tools/one_shots/ntpe_validate.py`, legacy tests; `quality_context.py`/`quality_result.py` missing (`__init__.py:50-82` swallows ImportError) | LEGACY |
| legacy engine pipeline | `engine/` (15 modules, ~83 KB) | `core/translator.py:15`, `tools/legacy_pipeline_launchers/*` | LEGACY |
| `core/translator.py` | `core/translator.py` | zero importers | LEGACY |
| `core/expansion/` | `core/expansion/*` | dead engine + archived launchers | LEGACY |
| TIC offline quality gate | `core/translation_intelligence_corpus/offline_quality_gate.py` (232 lines) | `lcr_offline_validation/executors.py:14` | OFFLINE / TEST |
| knowledge validation | `core/knowledge_validation/*` | knowledge-layer only | ADJACENT (not output QA) |
| resource placeholders | `core/translation_resources/qa_resource.py` | own package + tests | LEGACY placeholder |

## 6. Summary counts

```text
CANONICAL / KEEP guards on reader path : runtime_qa(+policy), BasicTranslationQA,
      analyze_translation_quality(wrapper), quality_v5 stack, naturalness post-process,
      glossary/EPUB/offset security validators (separate contracts)
DEAD CODE                              : core/validator.py + 4 orphan functions
TEST-ONLY                              : build_qa_retry_user_prompt (+lts primitive wrappers)
UNUSED IMPORTS                         : 2
INERT CONTRACT                         : qa_fail_policy
LEGACY subsystems                      : core/quality, engine, core/translator, core/expansion
SECONDARY (SDK, not reader-first)      : TranslationOrchestrator + TranslationValidator
UNKNOWN                                : none
```
