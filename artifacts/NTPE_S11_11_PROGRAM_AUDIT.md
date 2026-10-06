# NTPE S11-11 — Program-Level Capability, Quality & Residual Gap Reconciliation Audit

Audit / reconciliation only. No production, test, schema, runtime, provider or TXT change.

## 0. Baseline

```text
Baseline HEAD : 12731902048b2551d7ab12137deb4c2206a78b6d
Actual HEAD   : 12731902048b2551d7ab12137deb4c2206a78b6d (audit commit appended separately)
Branch        : main
S11-01 baseline (historical) : 1655b25 / s10-complete
```

Pre-existing dirty state preserved (untouched, not staged): `memory/character_memory_lts.json`,
the four `tests/literary/outputs/*` residuals (`PS-03/README.md` remains deleted), and the
untracked S11-01/S11-02 artifacts.

## 1. Method

Re-derived current truth from the repository at `1273190` (source inspection, import/reference
scans, artifact cross-check), not by copying S11-01. The only production change between the
S11-01 baseline and now is the S11-09 repair in `core/adapters/epub_extraction_boundary.py`
plus its tests; every other capability was re-confirmed by direct reference/usage checks.

## 2. S11 Closure Evidence (three EPUB chains)

```text
Spine Ordering:          S11-02 audit -> S11-03 repair -> S11-04 E2E = CLOSED
Non-Linear Semantics:    S11-05 audit -> S11-06 repair -> S11-07 E2E = CLOSED
TOC Fallback:            S11-08 audit -> S11-09 repair -> S11-10 E2E = CLOSED
```

- Spine ordering: extraction emits every spine item in ascending `spine_position`;
  `chapter_id = ch{spine_position:04d}`. Verified by S11-03/S11-04 and re-locked by
  S11-10 in the persisted final EPUB.
- Non-linear semantics: `linear="no"` items retained in place with `is_linear=False`;
  final itemrefs `[None,"no",None,"no",None]`. Verified by S11-06/S11-07/S11-10.
- TOC fallback: R1 standard EPUB3 `nav > ol > li` traversal, R2 canonical manifest-href
  lookup, R3 empty/whitespace rejection, precedence
  `h1 > h2 > <title> > nav/NCX label > "Chapter N"`. Verified by S11-09 and by S11-10
  reading the production `nav.xhtml` back from the persisted artifact.

No active EPUB correctness gap from S11-01 remains, unless new independent evidence is found.

## 3. S11-01 Claims Reconciliation

| S11-01 finding | Old state | Current state | Evidence | Decision |
|---|---|---|---|---|
| C1 EPUB spine ordering | ACTIVE GAP | CLOSED | S11-03/S11-04/S11-10; `epub_extraction_boundary.py` ascending `spine_position` | CLOSED |
| C2 TOC fallback | ACTIVE GAP | CLOSED | S11-08/S11-09/S11-10 | CLOSED |
| C3 QA consolidation / dead code | REFACTOR (maintainability) | unchanged | `core/validator.py` and Stage-15 quality engine have no production importers; no correctness risk demonstrated | MAINTENANCE / REFACTOR OPPORTUNITY |
| C4 legacy / orphan archive | ARCHIVE candidate | unchanged + new nuance | `engine/`, `core/translator.py` unreferenced; **but** `core.translation_release.reader_structure.models` is imported by the canonical `core/epub_translation/reader_chapter_map.py:19` | ARCHIVE CANDIDATE (split first) |
| C5 output portability / stale `available` | REFACTOR | partially mitigated | UI derives availability from the filesystem at render (`ui/translation_studio/project_view_model.py:69-105`); persisted `available` is not used to gate Open Result | LIMITATION / DEFERRED |
| C6 Glossary product integration | INTEGRATE or DEFER | unchanged NOT IMPLEMENTED | all UI call sites hardcode `glossary_path=None` (`project_page.py:707,993,1154`, `controller.py:46,205`); no Project glossary contract; no runtime injection | ACTIVE PRODUCT GAP / DEFERRED (product decision) |
| C7 S7 literary calibration | DEFER | unchanged, still blocked | `artifacts/NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md`: `NOT AUTHORIZED`; external evaluators + reference data missing | DEFERRED (quality-program gap) |

## 4. Capability Reconciliation (current truth)

### 4.1 EPUB

- Correctness: **PASS** — all three S11 chains CLOSED; F1/F2/F3 (S10) CLOSED; no new defect.
- Remaining limitations (not correctness defects, not S11-caused):
  1. **Original TOC structural fidelity**: production passes `toc_entries=()`
     (`project_page.py:1133`, `controller.py:184`); the packager rebuilds navigation
     one-entry-per-chapter (`epub_packager.py:468-513`). Nesting/fragments/sections in the
     source nav are not preserved. Recorded by S11-08 as a known loss layer.
  2. **Fixed-layout**: detected and recorded in the manifest with a warning; no
     layout-specific rendering.
- Classification: **B — PRODUCTION USABLE WITH DOCUMENTED LIMITATION** (correctness clean;
  limitations are deferred product enhancements).

### 4.2 TXT

- Unchanged by S11. Real path: `lts/txt_translation_runtime.py` → canonical engine;
  `ReaderProject` persistence; resume/recovery; Open Result. Strong test coverage.
- Classification: **A — PRODUCTION READY**. No S11 impact.

### 4.3 Project Persistence

- `ProjectStore` at `<NTPE_HOME>/projects/<id>/project.json`, atomic `os.replace`,
  schema v1, SHA-256 source identity. Fresh restart read-back re-verified in S11-10.
- Schema v1 is sufficient for all currently committed product behavior; Glossary/memory
  are intentionally runtime-referenced, not embedded.
- Classification: **A** (with non-blocking orphan/TTL cleanup absent).

### 4.4 Recovery

- `check_recovery_eligibility` 7 deterministic gates; normal translation ≠ recovery;
  execute path lives in the runtime (`resume=True`). S10-03 recovery E2E passes.
- Classification: **A**. No active gap.

### 4.5 Output / Artifact Portability

- `OutputRecord{output_dir, artifact_path, artifact_kind, available}`; per-project and
  per-identifier isolation.
- Question A (absolute-path portability): real but **portability limitation**, not a
  correctness defect — relocating `NTPE_HOME` yields the truthful `結果檔案不存在`.
- Question B (stale `available`): the persisted flag can go stale, but the UI recomputes
  `output_exists` from the filesystem and gates controls on that, so it is not a
  reader-facing correctness defect.
- Question C: **DEFERRED enhancement / maintenance debt**, not an active blocker.
- Classification: **B — PRODUCTION USABLE WITH KNOWN LIMITATION**.

### 4.6 Translation Studio

- All reader-facing controls real/wired; S8 honesty contract still holds. UI tests patch
  the runtime by design (wiring/state only); E2E exercises the real pipeline with only
  runtime execution injected.
- Classification: **A**.

### 4.7 Launcher

- Two shells (`ui/translation_studio`, `ui/translation_launcher`) over canonical runtimes;
  ownership documented. No hidden second translation route.
- Classification: **A**.

### 4.8 CLI

- `cli/` provides config/plugin/manifest/benchmark/project-style internal commands plus
  `translate`. The CLI `project` workspace model is separate from `ReaderProject` by
  design. Presence of internal commands does not make the CLI product surface broken.
- Classification: **B (limited user surface), KEEP**.

### 4.9 Glossary

- Re-confirmed NOT IMPLEMENTED: backend builder/schema/`SeriesGlossary` exist
  (`core/glossary_builder.py`), but no UI, no Project glossary contract, no runtime
  injection (all UI call sites `glossary_path=None`).
- Classification: **ACTIVE PRODUCT GAP / DEFERRED** — requires a product-contract decision;
  backend presence does not make it product-ready. No implementation in S11-11.

### 4.10 Character Memory

- `quality_character_memory_v72: bool = False` default-off in every options surface
  (`lts/txt_translation_runtime.py:147`, `batch_translation_runtime.py:136`,
  `production_submission_adapter.py:37`, `epub_translation/runtime/adapter.py:104`).
- No UI commitment; no hidden production activation; one library (`character_memory_v2`).
- Classification: **EXPERIMENTAL / DEFAULT-OFF** (deferred).

### 4.11 Context / Scene Memory

- `quality_context_scene_v72: bool = False` default-off everywhere (same evidence set).
- Legacy `core/context/memory_engine.py` superseded; referenced only by
  `core/foundation/compatibility.py` (not reached by the reader path).
- Classification: **EXPERIMENTAL / DEFAULT-OFF** (deferred).

### 4.12 Literary Quality

- Production behavior is advisory QA only; no human-calibrated scoring, no reviewer
  workflow. S7 calibration artifacts remain methodologically closed (R1–R3) but
  `NOT AUTHORIZED`; H02 external annotation dependency; external evaluators + reference
  data still missing.
- Classification: **OBSERVATIONAL / DEFERRED** — a quality-program gap, not a runtime
  correctness defect.

### 4.13 QA / Validation

- Advisory guards in `BasicTranslationQA` + `runtime_qa`; `core/validator.py` and the
  Stage-15 engine are not imported in production; Korean/length/omission checks are
  duplicated. No blocking guard; no demonstrated correctness/stability risk from the
  duplication.
- Classification: **MAINTENANCE / CONSOLIDATION OPPORTUNITY**.

### 4.14 Runtime Architecture

- Canonical route intact and single:
  `UI/CLI → TranslationRuntime → RuntimeOrchestrator → TranslationEngine → ProviderManager
  → NvidiaTranslationProvider → NvidiaClient → LiteraryPromptBuilder`.
- Frozen production model `meta/llama-3.2-90b-vision-instruct` confirmed in
  `core/config.py:19`, `lts/txt_translation_runtime.py:83`,
  `core/epub_translation/runtime/adapter.py:56`.
- `core/translator.py` has no importers; `engine/` is reached only by it and
  `tools/legacy_pipeline_launchers/` (the `engine` string in
  `epub_translation/chunking.py:42` is a docstring reference, not an import).
  No hidden production route.
- Classification: **PASS**.

### 4.15 Security

- EPUB extraction guards unchanged (`_validate_zip_security`): entry-count/size caps,
  traversal/absolute/UNC/symlink/duplicate/executable/nested-archive/zip-bomb/encryption
  blocks. Security tests present in `tests/unit/adapters/test_epub_extraction_boundary.py`
  and `tests/integration/test_epub_extraction_e2e.py`.
- S11 repairs introduced no security change.
- Classification: **PASS**.

### 4.16 Testing Architecture / Test Debt

See §6. Classification: **PASS with pre-existing test debt** (no S11-caused failure).

### 4.17 Legacy / Orphan Surface

- `core/translator.py`: no importers → legacy.
- `engine/`: reached only by `core/translator.py` + `tools/legacy_pipeline_launchers/`.
- `core/validator.py`: no production importers.
- `core/context/memory_engine.py`: superseded; only `core/foundation/compatibility.py`.
- `core/translation_release`: the delivery pipeline (incl. `reader_structure/epub_packager.py`)
  is reached only through `core/adapters/rm8_delivery_adapter.py`, which itself is
  referenced only by `tests/unit/adapters/test_rm8_delivery_adapter.py`. **However**,
  `core/translation_release/reader_structure/models.py` is imported by the canonical
  `core/epub_translation/reader_chapter_map.py:19` — so `translation_release` is **not**
  fully orphan and must be split before any archive.
- Orphan top-level dirs (no production imports): `analysis/`, `engine/`, `integration/`,
  `runtime_api/`, `external_api/`, `web_ui/`, `web/`, `packaging/`, `compatibility/`,
  `platform_services/`, `performance/`, `benchmarks/`, `benchmark/`, `regression/`,
  `knowledge/`, `translated/`, `translation/`.
- Classification: **LEGACY / ARCHIVE CANDIDATE** (evidence-backed; REMOVE not authorized).

### 4.18 Repository Hygiene

- Root contains 5 canonical entry-point scripts (`launcher_translate.py`,
  `ntpe_production_translate.py`, `ntpe_translation_studio.py`,
  `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py`) — pre-existing canonical
  entry points, not S11-11 violations.
- Diagnostics live under `artifacts/`; one-shot tools under `tools/one_shots/`.
- Literary residuals and `memory/character_memory_lts.json` remain as pre-existing dirty
  state, not S11-11 defects.
- Classification: **PASS (no new noise)**.

## 5. Residual Gap Register (classification)

| Item | Classification | Basis |
|---|---|---|
| EPUB spine ordering | CLOSED | S11-03/04/10 |
| EPUB non-linear semantics | CLOSED | S11-06/07/10 |
| EPUB TOC fallback | CLOSED | S11-08/09/10 |
| EPUB original TOC structural fidelity (`toc_entries=()`) | LIMITATION / DEFERRED | by-design rebuild; product enhancement |
| EPUB fixed-layout rendering | LIMITATION / DEFERRED | detected + recorded only |
| Output absolute-path portability | LIMITATION / DEFERRED | truthful failure state, not corruption |
| Output stale `available` flag | MAINTENANCE DEBT (mitigated) | UI recomputes from filesystem |
| Glossary product integration | ACTIVE PRODUCT GAP / DEFERRED | no UI/contract/runtime wiring |
| Character Memory | EXPERIMENTAL / DEFERRED | default-off |
| Context / Scene Memory | EXPERIMENTAL / DEFERRED | default-off |
| Literary calibration | DEFERRED (quality-program) | S7 NOT AUTHORIZED; external data missing |
| QA guard duplication / `core/validator.py`, Stage-15 dead | MAINTENANCE / REFACTOR OPPORTUNITY | advisory only; no correctness risk shown |
| Legacy stack (`engine/`, `core/translator.py`, `core/context/`, orphan dirs) | LEGACY / ARCHIVE CANDIDATE | unreferenced; rollback proof required |
| `core/translation_release` delivery subsystem | ARCHIVE CANDIDATE (split first) | models live-used by canonical reader map |
| Launcher import-time `SystemExit` (~79 test files) | TEST INFRASTRUCTURE DEBT | collection architecture |
| Legacy root-module `ModuleNotFoundError` (90 collections) | TEST INFRASTRUCTURE DEBT | legacy collection |
| Frozen-worktree governance locks (`lcr_batch3/4`) | TEST INFRASTRUCTURE DEBT | global `git status` allowlist |
| Stale expectation tests (unit/contract 58 failures) | STALE TEST EXPECTATION | pre-existing |
| Shared Qt e2e session flaky access violation | TEST INFRASTRUCTURE DEBT | S11-10 §6; Qt/Python 3.14 race |
| UI provider path mocked in `tests/ui` | TEST COVERAGE GAP | contract is UI wiring by design |
| Pre-existing literary residuals / LTS memory | EXTERNAL DIRTY STATE (protected) | not S11 defects |

### 5.1 Test debt categories (A–F)

- A S11-caused: **none** (broad failures and the S11-10 e2e crash are not S11-caused).
- B pre-existing production/environment: reader_structure packager `chmod` tests,
  submission `NTPE_RUNTIME_PIPELINE` env test, `translation_runtime.test_adapter`
  `section_count` expectation.
- C legacy collection architecture: ~79 `launcher_*` import-time `SystemExit`; 90 legacy
  root-module `ModuleNotFoundError` collections.
- D frozen artifact / governance lock: `lcr_batch3`/`lcr_batch4` global-worktree allowlist
  tests (already violated by pre-existing dirty state).
- E stale test expectation: the 58 unit/contract failures (LCR/quality/stage suites).
- F uncovered capability / missing contract: UI provider path (mocked by design);
  shared Qt e2e session reliability.

## 6. S11-10 Test Placement Finding

S11-10 verification was placed at
`tests/integration/test_s11_10_epub_toc_fallback_reader_first.py` rather than `tests/e2e/`
because the shared Qt e2e session has a pre-existing, flaky Windows access violation in
`test_s11_04`'s background `TranslationRuntime` thread; adding any new e2e module aborts
the whole directory run (baseline `tests/e2e` 55 passed; a new unrelated e2e module
crashed in 1/2 runs). Classification: **TEST INFRASTRUCTURE DEBT** — an E2E-session
reliability issue, not an EPUB correctness failure, and not caused by S11-10. A dedicated
E2E-infrastructure workstream is warranted; it is not an S11 production blocker.

## 7. Blockers Analysis

| Category | Finding |
|---|---|
| Current production correctness blocker | **NONE** |
| Correctness-limitation (non-blocking) | Output portability; EPUB TOC structural fidelity; fixed-layout |
| Future feature / product gap | Glossary integration; optional memory default-on |
| Deferred quality program | S7 literary calibration (external data) |
| Maintenance / refactor debt | QA consolidation; legacy/orphan archive; dead code |
| Experimental | Character / Context-Scene memory |
| Test infrastructure debt | Launcher collection, legacy root modules, Qt e2e session, stale expectations |

Glossary incompleteness, literary calibration, experimental memory and legacy code are
**not** current runtime blockers.

## 8. S11 Program Decision

**Option A — S11 COMPLETE (recommendation).**

There is no unresolved production correctness blocker for the TXT/EPUB reader-first
product. Spine Ordering, Non-Linear Spine Semantics and TOC Fallback are CLOSED with
audit → repair → E2E evidence; resource mapping is intact; security is unchanged; the
canonical runtime is single and frozen. All remaining items are deferred features,
experimental capabilities, maintenance debt or test-infrastructure debt.

Per governance, this audit only recommends; it does **not** create an `s11-complete` tag.

### Recommended next boundary (evidence-ranked, not auto-inherited)

Open new, explicitly-scoped workstreams (each requires its own contract/decision):

1. **Glossary product integration** — needs a product-contract decision first
   (UI + Project binding + runtime injection); do not start from backend capability alone.
2. **E2E test infrastructure reliability** — make the Qt e2e session stable and decide the
   correct home for the S11-10 verification.
3. **Legacy / orphan archive program** — archive (not remove) with dependency proof;
   split `core/translation_release` (models are live).
4. **Output portability / stale-reference refresh** — only if product decides relocation
   support is required.
5. **QA guard consolidation** — remove dead duplicates without changing advisory semantics.
6. **S7 literary calibration** — blocked on external human evaluators + reference data.

## 9. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
Production Files Modified : NO
Tests Modified            : NO
```

## 10. Diff Hygiene

Only new audit artifacts under `artifacts/` are added. `core/`, `lts/`, `engine/`, `ui/`,
`cli/`, `tests/` unchanged. Pre-existing dirty state preserved. No scratch/root files or
generated sandboxes produced by this audit (source inspection only).

## 11. Acceptance

All §32 report sections covered; three EPUB chains marked CLOSED; S11-01 C1–C7 reconciled;
capability matrix produced; residual register classified with engineering decisions;
blockers separated from limitations/features/debt; program decision evidence-backed; no
implementation performed.
