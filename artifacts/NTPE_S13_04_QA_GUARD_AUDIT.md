# NTPE S13-04 — QA Guard Consolidation & Dead-Path Reconciliation Audit

Audit-only / no implementation. No production, test, schema, runtime, provider or
pipeline change. Closes evidence for residual **R28 - QA guard duplication; dead
`core/validator.py` / Stage-15 engine**.

## 0. Baseline

```text
Repository     : D:\Python\NTPE
Branch         : main
Baseline HEAD  : e08c1dc67e925a646c34ac82fb76650ddd67b003
origin/main    : e08c1dc67e925a646c34ac82fb76650ddd67b003
```

`git status --short` before and after this audit is identical (see §13). No
reset / clean / force-pull / force-push / discard performed.

## 1. Scope

Audited `core/`, `lts/`, `ui/`, `tests/` for every canonically reachable QA / validation /
quality-guard / output-validation / terminology-validation / structural-validation path,
tracing **caller -> guard -> result -> reader-facing behaviour**, not by name.

## 2. Audit A — Canonical QA Path

### 2.1 Reader-facing canonical flow (evidence)

```text
Reader Project / Translation
  -> ui/translation_studio/pages/project_page.py  (TXT)
     ui/translation_studio/translation_worker.py  (EPUB)
  -> TXT : lts/txt_translation_runtime.py::translate_txt
           -> _translate_txt_with_runtime_pipeline        (txt_translation_runtime.py:615)
     EPUB: core/epub_translation/runtime/adapter.py::translate_epub_translation_input
  -> RuntimeOrchestrator.execute                          (core/runtime_orchestrator/manager.py:154)
  -> TranslationEngine.translate_package_from_request     (manager.py:317)
  -> BasicTranslationQA.check                             (translation_engine.py:249)
  -> provider_result["qa"]
  -> EPUB: carried into EpubChunkResult.qa_report         (adapter.py:685,721)
     TXT : discarded; TXT runtime rebuilds its own qa_report
  -> TXT post-processing (txt_translation_runtime.py:920-975):
       run_quality_v5_phase1 + merge_quality_v5_into_runtime_qa
       analyze_translation_quality -> analyze_runtime_quality
       orchestrate_runtime_discipline (diagnostic)
  -> result["qa"]  (advisory; attached to package/result, not gating)
```

### 2.2 Findings

1. **QA is on the canonical production path** for both formats, but only as an
   *attached report*. There is no reader-facing gate that reads it.
2. **QA is advisory, not blocking, everywhere on the reader path.** EPUB aggregation
   status derives only from provider/chunk status (`adapter.py:741-810`); TXT result
   status derives from provider success/failure and output existence
   (`txt_translation_runtime.py:989-1003`). Neither consults `qa_report["passed"]`.
3. **No guard can block output** on the canonical path. Guards only produce diagnostics.
   (`qa_report` is stored, serialised into chunk JSON / package, and never raised on.)
4. **QA is persistence-independent**: reports are recomputed from text; the persisted
   `resume_state` keys are `status` / `source_hash` / `output_path`, never QA verdicts.
5. **No second QA pipeline.** The TXT stack (`BasicTranslationQA` -> `runtime_qa` ->
   `quality_v5` -> `discipline`) is a single sequential layer chain; EPUB uses a
   different (engine-only) stack. The UI implements no QA logic of its own: it only
   sets options (`project_page.py:757-777, 1179-1199, 1346-1353`). Confirmed by grep:
   `ui/` contains no QA detection code.

### 2.3 Format asymmetry (key evidence)

| Format | Guard that runs | Result consumed? |
|---|---|---|
| TXT | `BasicTranslationQA` (engine) + `runtime_qa` + `quality_v5` + `discipline` | engine QA **discarded**; runtime QA + v5 attached |
| EPUB | `BasicTranslationQA` (engine) only (+ `best_attempt`) | engine QA **carried** into `qa_report` |

- TXT: `provider_result` is read for `translation`/`output_path` only
  (`txt_translation_runtime.py:903-908`); `provider_result.get("qa")` is never read, and
  `BasicTranslationQA` is re-run for every chunk without effect. `BasicTranslationQA` is
  therefore a **redundant execution** on the TXT path.
- EPUB: `qa_report = provider_result.get("qa")` (`adapter.py:685`) -> `EpubChunkResult`.
  `runtime_qa` is **imported but never used** (`adapter.py:43`; only occurrence).

## 3. Audit B — Duplicate Guard Detection

Full inventory in `artifacts/NTPE_S13_04_QA_GUARD_INVENTORY.md`.

### 3.1 Overlapping responsibility (not strict duplicates)

| Responsibility | Implementation A | Implementation B | Same contract? |
|---|---|---|---|
| Korean residue | `basic_qa.py:16-22` (>=20, warning) | `runtime_qa.py:47,178` (policy max, error) | No (threshold/severity differ) |
| Length ratio | `basic_qa.py:24-32` (>200 / 0.25) | `runtime_qa.py:174-177` (policy min) | No |
| Locked-term missing | `basic_qa.py:34-41` | `runtime_qa.py:104-117` | No (schema differs) |
| Repeated lines | — | `runtime_qa.py:55` + `lts` `detect_repeated_lines` (`txt:1324`) | Wrapper duplication |
| Simplified Chinese | — | `runtime_qa.py:93` + `lts` `detect_simplified_chinese` (`txt:1337`) | Wrapper duplication |
| Forbidden/AI phrases, bad names | `core/validator.py:17-32,41-47` | — | Dead (no caller) |
| Terminology consistency | `core/quality/terminology_consistency.py` (Stage-15) | glossary QA (`runtime_qa` locked-term) | Dead vs canonical |

- `BasicTranslationQA` and `runtime_qa` are **parallel per-format implementations**, not a
  co-executing duplicate pair. By the Audit-B bar (responsibility + input + output +
  contract-effect all highly overlapping) they do **not** qualify as an in-pipeline
  consolidation candidate without changing EPUB/TXT behaviour.
- `analyze_translation_quality` (`txt:1388`) is a deliberate **backward-compat wrapper**
  that delegates to `analyze_runtime_quality` (docstring `txt:1389-1393`). This is
  normalisation, not duplication — KEEP.
- `lts.detect_repeated_lines` / `lts.detect_simplified_chinese` (`txt:1324,1337`)
  re-implement the same primitives already in `runtime_qa.py:55,93`. The canonical
  `analyze_translation_quality` does **not** call them; they remain as test/legacy API.
- `core/quality/` (Stage-15 QA engine) duplicates terminology / repetition / structure /
  coverage / completeness concerns that are independently handled on the canonical path,
  but it has **no production caller** (see §4).

### 3.2 Conclusion for B

There is **no evidence-based, in-pipeline duplicate** whose unification preserves the
current per-format contract without regression risk. Duplicate-looking code across the
EPUB and TXT stacks is format-specific, not redundant.

## 4. Audit C — Dead / Unreachable Paths

Reverse-traced imports, `__init__` exports, SDK, factory/registry, CLI/UI wiring.

### 4.1 Confirmed dead (zero callers repo-wide, including tests)

| Symbol | File | Evidence |
|---|---|---|
| `class Validator` (`core/validator.py`) | `core/validator.py:14` | Zero importers of `core.validator` (only sibling `.validator` imports in unrelated packages). No `Validator(` instantiation anywhere. |
| `should_soft_fail_naturalness` / `soft_fail_naturalness_report` | `runtime_qa.py:287,306` | Only occurrence is the module itself + an **unused import** in `txt_translation_runtime.py:32`. No caller. |
| `has_retry_worthy_naturalness_issue` | `txt_translation_runtime.py:1742` | No caller. |
| `qa_retry_delay_seconds` | `txt_translation_runtime.py:1418` | No caller. |
| `RuntimeQAPolicy` / `analyze_runtime_quality` import | `adapter.py:43` | Imported, never referenced in the file. |
| `soft_fail_naturalness_report` import | `txt_translation_runtime.py:32` | Imported, never referenced. |

### 4.2 Test-only

| Symbol | File | Evidence |
|---|---|---|
| `build_qa_retry_user_prompt` | `txt_translation_runtime.py:1655` | Callers are tests only (`tests/integration/launcher_stage18_10_*`, `tests/integration/translation_engine_v30_naturalness_guard_test.py`, `tests/integration/translation_adaptive_prompt_feedback_v553_test.py`); two of three test files are quarantined by `tests/conftest.py` (`launcher_*_test.py`, `integration/*_test.py`). No production caller. |

### 4.3 Inert / declared-but-unused contract

| Item | Evidence |
|---|---|
| `qa_fail_policy` | Declared `txt:128`, `batch_translation_runtime.py:115`, `ntpe_production_translate.py`/UI pass it, parsed `txt:2043`. **Never consumed** by any branch on the canonical runtime path. The old enforcement path (`qa_failed` resume status, `failed_chunk`, manifest `qa.fail_policy`) exists only in `lts/long_run_recovery.py`, `lts/batch_translation_runtime.py`, `lts/batch_runtime_monitor.py` as *resume-state reads*, not producers. |

### 4.4 Legacy subsystems without a production importer

| Area | Evidence |
|---|---|
| `engine/` (~83 KB, 15 modules) | Only imported by `core/translator.py:15` (`engine.nvidia`) and `tools/legacy_pipeline_launchers/*`. `core/translator.py` itself has **zero importers**. No reader-path importer. |
| `core/quality/` (33 files, Stage-15) | Importers are `engine/pipeline/*` (dead), `core/expansion/expansion_planner.py` (itself only used by dead/archived code), `tools/one_shots/ntpe_validate.py`, and legacy tests. `core/quality/quality_context.py` / `quality_result.py` **do not exist**; `__init__.py:50-82` swallows the `ImportError`, so `TranslationQualityEngine` etc. are always `None`. |
| `core/expansion/` | Only `core/expansion/__init__.py` + `style_expansion_engine.py` + archived launchers. |

Not dead but secondary (not reader-first): `TranslationOrchestrator` / `TranslationValidator`
(`core/translation_engine/orchestrator.py:62,87`) are used only by `sdk/client.py:11,37`.

## 5. Audit D — Contract Preservation

No canonical contract is touched by this audit (no code changed). Verified the guards
are **not** part of any CLOSED contract's enforcement:

| Contract | Enforcement location | QA role |
|---|---|---|
| Glossary precedence / hash binding | glossary loader + `resume_state["glossary_hash"]` (`txt:1969`; `adapter.py:320`), `verify_snapshot_file` | QA reads `locked_dictionary` only; does not gate |
| EPUB chapter ordering / non-linear semantics | `adapter.py:346-348,781`; `reader_chapter_map` | independent of QA |
| Offset contract | `core/epub_translation/contract/validation.py` | independent of QA |
| Output existence gate | `project_page.py:1031-1060`; `project_view_model.py:69-95` | QA not consulted |
| Recovery eligibility | `resume_state` status/source_hash (`txt:755-761`) | QA verdict not persisted |
| Provider/runtime route | `manager.py:317` -> `TranslationEngine` | QA is downstream of the call |

Conclusion: **QA is advisory maintenance territory; consolidation must not alter these.**

## 6. Audit E — Advisory vs Blocking Semantics

| Guard | Intended | Actual on canonical path |
|---|---|---|
| `analyze_runtime_quality` (TXT) | advisory (`qa_fail_policy` suggests retry/fail) | **ADVISORY** — result attached only |
| `BasicTranslationQA` | advisory | **ADVISORY / DISCARDED (TXT)**, ADVISORY (EPUB) |
| `quality_v5` unified gate | advisory report with `retry_required` | **ADVISORY** — `retry_required` never acted on in runtime |
| `orchestrate_runtime_discipline` | adaptive local-repair / retry decision | **DIAGNOSTIC ONLY** |
| `qa_fail_policy` | nominal retry/fail enforcement | **UNUSED / INERT** (semantic mismatch) |

### Semantic mismatches (explicitly listed)

1. **Nominal blocking, actually unused**: `qa_fail_policy` (`"retry"|"fail"|"warn"`) is
   declared, plumbed from CLI/UI, parsed into `TxtTranslationOptions`, and read into
   nothing. The reader path never retries or fails on QA.
2. **Nominal enforcement, actually diagnostic**: `orchestrate_runtime_discipline` is
   invoked with `text=chunk` — the **source** text, not the translation — and its
   possibly-repaired `outcome.text` (`runtime_orchestrator.py:91-98`) and `outcome.qa_report`
   are **discarded**; only `initial_action`/`final_action`/`revalidated` are stored
   (`txt:963-972`). Any local-repair effect is not applied to the output.
3. **Nominal advisory, actually redundant execution**: `BasicTranslationQA` runs for every
   TXT chunk via the engine but its result is overwritten and never read.

## 7. Audit F — Test Evidence

No tests were modified. Canonical suites re-run read-only.

| Suite | Result |
|---|---|
| `tests/runtime` (incl. `translation_runtime_provider_qa_test.py`) | **10 passed** |
| `tests/lts_stage_04/test_translation_qa.py` | **2 failed / 3 passed** |
| `tests/lts_stage_03` (adjacent) | 1 failed / partial (dry-run glossary metadata, unrelated) |
| `tests/contract` (QA-relevant files) | pass (`test_s1..s5c` QA fields are fixtures `qa_report={}`/`{"passed":True}`) |
| `tests/e2e`, `tests/reader_project` | QA appears only as fixture stubs (`qa_report=MappingProxyType(...)`); no QA-contract assertion |

### 7.1 The 2 failures are obsolete expectations, not live contract

`tests/lts_stage_04/test_translation_qa.py:38,69` assert the **removed** QA fail-policy
contract:

```text
test_translate_txt_qa_warn_records_qa_without_failing : result["status"]=="success",
        records[0]["qa"]["passed"] is False, manifest qa.fail_policy=="warn"
test_translate_txt_qa_fail_stops_chunk                : result["status"]=="failed",
        result["failed_chunk"]==1, resume state status=="qa_failed"
```

They fail with `AttributeError: 'FakeEngine' object has no attribute
'translate_package_from_request'` because the runtime moved to the `RuntimeOrchestrator`
path (`manager.py:317`), and even with a conforming engine the assertions cannot pass:
no production code produces `qa_failed`, `failed_chunk`, or a manifest `qa.fail_policy`.
These are **legacy behaviour residue**, consistent with residual R33 (~58 stale
expectations). They must **not** be "fixed" by restoring QA enforcement into the
canonical runtime.

### 7.2 QA tests that do validate production contract

- `tests/runtime/translation_runtime_provider_qa_test.py:33-38` verifies the public
  `analyze_runtime_quality` boundary and `RuntimeKOREAN_RESIDUE` (KEEP).
- `tests/lts_stage_04/test_translation_qa.py:19` verifies the canonical
  `analyze_translation_quality` codes (passes; KEEP).

## 8. Required Classification — Summary

| Area | Classification | Evidence | Recommendation |
|---|---|---|---|
| `core/translation_runtime/runtime_qa.py` (`analyze_runtime_quality`, `RuntimeQAPolicy`) | **CANONICAL / KEEP** | called `txt:1407`; tested `tests/runtime` | keep |
| `lts.analyze_translation_quality` (compat wrapper) | **CANONICAL / KEEP** | `txt:1388`; delegating docstring | keep |
| `BasicTranslationQA` | **CANONICAL / KEEP** (EPUB) · redundant on TXT | `adapter.py:685` carries result; `txt` discards | keep; document asymmetry |
| `quality_v5` unified gate | **CANONICAL / KEEP** (advisory) | `txt:933-940` | keep |
| `orchestrate_runtime_discipline` (diagnostic invocation) | **CONSOLIDATION CANDIDATE (semantic)** | source text in, repair discarded `txt:963-972` | fix invocation or document advisory |
| `soft_fail_naturalness_report` / `should_soft_fail_naturalness` | **DEAD CODE** | no caller | remove |
| `has_retry_worthy_naturalness_issue` | **DEAD CODE** | no caller | remove |
| `qa_retry_delay_seconds` | **DEAD CODE** | no caller | remove |
| `build_qa_retry_user_prompt` | **TEST-ONLY** (legacy) | test-only callers, quarantined | keep or archive with legacy tests |
| `qa_fail_policy` | **LEGACY / INERT** | declared, never consumed | remove or document advisory |
| `core/validator.py` (`Validator`) | **DEAD CODE** | zero importers | remove/archive |
| `TranslationValidator` / `TranslationOrchestrator` | **SECONDARY (SDK)** | `sdk/client.py` only | out of reader scope |
| `core/quality/` (Stage-15) | **LEGACY** (dismantled) | missing submodules, no prod caller | separate archive program |
| `engine/`, `core/translator.py`, `core/expansion/` | **LEGACY** | no reader-path importer | separate archive program |
| `core/translation_intelligence_corpus/offline_quality_gate.py` | **OFFLINE / TEST** | `lcr_offline_validation` only | out of reader scope |
| `core/knowledge_validation/` | **ADJACENT (not output QA)** | knowledge-layer schema/business rules | out of scope |
| `core/translation_naturalness/` (canonicalizer/collocation/voice) | **CANONICAL / KEEP** (not a gate) | `txt:924-928`; `delivery_pipeline.py:110-112` | keep; `analyze_voice_register` result discarded (diagnostic) |

`UNKNOWN` items: none — every audited guard was resolved to a caller or proven callerless.

## 9. Consolidation candidates (evidence)

**C1 (dead QA code, bounded, deletion-only):** `core/validator.py`; orphan functions
`should_soft_fail_naturalness`, `soft_fail_naturalness_report`, `has_retry_worthy_naturalness_issue`,
`qa_retry_delay_seconds`; unused imports `soft_fail_naturalness_report` (`txt:32`),
`RuntimeQAPolicy, analyze_runtime_quality` (`adapter.py:43`). Zero-caller proven.

**C2 (semantic mismatch, needs a decision, not a merge):** `orchestrate_runtime_discipline`
called with source text and its repair discarded; `qa_fail_policy` inert. Either wire
intent or downgrade to explicit diagnostic documentation.

**C3 (deferred / out of scope for QA consolidation):** `core/quality/`, `engine/`,
`core/translator.py`, `core/expansion/` — large legacy archive program; and the
`BasicTranslationQA` ↔ `runtime_qa` unification (format-contract risk).

## 10. Decision

**Decision A — Bounded consolidation** (see `artifacts/NTPE_S13_04_QA_DECISION.md`),
scoped strictly to C1 dead QA code; C2 as a documented decision; C3 deferred.

## 11. Recommended implementation boundary (future authorized task)

```text
ALLOWED  : delete/archive zero-caller QA dead code (C1); remove unused imports;
           correct/annotate the discipline invocation + qa_fail_policy semantics (C2).
FORBIDDEN: any change to runtime_qa detection, BasicTranslationQA, quality_v5,
           discipline enforcement, EPUB/TXT output status, or any CLOSED contract;
           no second QA pipeline; no test edits except removing/archiving tests that
           assert the removed QA-enforcement contract.
```

## 12. Blockers

None. Evidence is sufficient for a bounded decision. Discovery of subcontracts was not
required.

## 13. Execution Accounting

```text
Production Files Modified : 0
Tests Modified            : 0
Provider Execution        : 0
Network Execution         : 0
Real Translation          : 0
```

Pre-existing dirty state (unchanged, preserved):

```text
 M memory/character_memory_lts.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_S11_01_CAPABILITY_MATRIX.md
?? artifacts/NTPE_S11_01_POST_S10_PRODUCT_CAPABILITY_QUALITY_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_DESIGN.md
```

Repository hygiene: artifacts written only under `artifacts/`; no root noise; no scratch
tools created.

## 14. Result

```text
Canonical QA path      : single, layered, advisory-only; no second pipeline
QA guard inventory     : complete (see INVENTORY)
Duplicate findings     : no in-pipeline duplicate; format-specific parallel implementations
Dead-path findings     : core/validator.py + 4 orphan functions + 2 unused imports (zero callers)
Advisory/blocking      : advisory everywhere; qa_fail_policy inert; discipline enforcement discarded
Test evidence          : tests/runtime 10 passed; lts_stage_04 2 obsolete QA-enforcement failures
Decision               : A — Bounded consolidation (dead QA code only)
```

**FINAL: PASS**
