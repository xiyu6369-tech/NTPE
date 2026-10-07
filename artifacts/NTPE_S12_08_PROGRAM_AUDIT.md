# NTPE S12-08 — Program-Level Capability, Quality & Residual Gap Reconciliation Audit

Audit / reconciliation only. No production, test, schema, runtime, provider or TXT change.

## 0. Baseline

```text
Baseline HEAD : 5ea85b4557453bb48e4c5920f6c9ea3c0adc8838
Actual HEAD   : 5ea85b4 (audit commit appended separately)
origin/main   : 5ea85b4
Branch        : main
```

Verified with `git status --short`, `git branch --show-current`, `git rev-parse HEAD`,
`git rev-parse origin/main`. No reset/clean/stash/restore. Pre-existing dirty state
preserved (see §17).

## 1. Method

Re-derived current truth from the repository at `5ea85b4` (source/import/reference
inspection + committed S12 audit/repair/E2E artifacts), not by copying S11-11. The S12
program added production code only in `core/reader_project/glossary.py`,
`ui/translation_studio/pages/project_page.py` (glossary panel + binding),
`lts/txt_translation_runtime.py` / `core/epub_translation/runtime/adapter.py` (canonical
glossary option binding) and the S12-06 validator repair in
`core/epub_translation/contract/validation.py`. All other capabilities re-confirmed by
direct checks.

## 2. S12 Closure Chain

```text
S12-01  Glossary Contract / Design        CLOSED  (f011e98)
S12-02  Glossary Backend / Project        CLOSED  (b178f39)
S12-03  Glossary Reader UX                CLOSED  (771bf08)
S12-04  Glossary Reader-first E2E         CLOSED  (e4ad350; EPUB block closed by S12-07)
S12-05  EPUB Chunk Offset Audit           CLOSED  (77fd7ae)
S12-06  EPUB Chunk Offset Repair          CLOSED  (83e34f0)
S12-07  Real EPUB Glossary E2E            CLOSED  (5ea85b4)
```

Evidence: commit chain above; `artifacts/NTPE_S12_0*` reports; S12-04/S12-06/S12-07 test
files passing at the S12-07 baseline.

## 3. Glossary Current State (reconciled)

S12-01 classified Glossary as `NOT IMPLEMENTED` (ACTIVE PRODUCT GAP). Current truth:

| Capability | State | Evidence |
|---|---|---|
| Import (TXT + JSON) | CLOSED | `ui/translation_studio/pages/project_page.py::_on_glossary_import`; S12-03 UI tests |
| Persistence | CLOSED | `ReaderProject.glossary`, `store.write_glossary_snapshot`; S12-02/S12-04 |
| Restart | CLOSED | S12-03 `test_h_restart_preserves_glossary`; S12-04/S12-07 |
| Replace | CLOSED | `manager.replace_glossary`; S12-03 test_e; S12-07 replace E2E |
| Detach | CLOSED | `manager.detach_glossary`; S12-03 test_g; S12-07 detach E2E |
| TXT terminology effect | CLOSED | `apply_glossary_to_options`; S12-04 TXT E2E |
| EPUB terminology effect | CLOSED | real adapter + `_apply_locked_dictionary`; S12-07 |
| EPUB packaging + read-back | CLOSED | S12-07 persisted artifact read-back |
| Recovery glossary-hash gate | CLOSED | `check_recovery_eligibility`; S12-02/S12-04 recovery tests |
| No-glossary (feature-off) | CLOSED | S12-07 contrast test |
| Corrupt glossary blocks launch | CLOSED | S12-03/S12-04/S12-07 |
| Determinism | CLOSED | S12-04/S12-07 determinism tests |

Glossary MVP classification: **CLOSED / PRODUCTION-READY (reader-first, TXT + EPUB)**.

### 3.1 MVP vs future enhancement (re-decided)

- **EPUB prompt parity** (`LiteraryPromptBuilder` glossary context in the EPUB orchestrator
  prompt) — S12-01 recorded this as a *bounded enhancement*; the MVP relies on canonical
  post-processing, which S12-07 verified end to end. No new evidence that prompt-stage
  injection is a *current product contract* requirement. Classification: **DEFERRED /
  future enhancement** (not a correctness gap).
- **CSV import** — S12-01 `DEFERRED`; no product requirement changed. Classification:
  **DEFERRED**.
- No re-opening of the MVP.

## 4. EPUB Offset Workstream (closure)

```text
S12-05 audit (canonical two-space contract) -> S12-06 validator repair
-> S12-07 real adapter E2E
```

- Canonical contract: `EpubTranslationChunk.body_*_offset` = chapter-body-relative;
  `extracted_*_offset` = absolute in `extracted_text`; invariant `body_range ==
  extracted_range`.
- Repair: `core/epub_translation/contract/validation.py::validate_epub_translation_chunk`
  replaced the invalid cross-space comparisons with the same-contract range invariant.
- Regression: `tests/integration/test_s12_06_epub_chunk_offset_repair.py` (real adapter
  path) + `tests/integration/test_s12_07_glossary_epub_real_adapter_e2e.py`.
- Classification: **CLOSED** (audit + repair + real-adapter regression). Not an active
  defect; do not re-open.

## 5. EPUB Capability

- **Correctness = PASS.** Fresh restart, spine ordering (S11-03/04), non-linear semantics
  (S11-06/07), TOC fallback (S11-09/10), chunk offset (S12-05/06/07), resource mapping,
  glossary terminology, packaging, persistence, recovery, fresh read-back all verified.
- **Production readiness = READER-FIRST USABLE** (S12-07 produced a real persisted EPUB
  with correct chapter identity, spine order, non-linear flag, nav and resource).
- **Limitations (feature/product, not correctness):**
  1. Original TOC structural fidelity: production passes `toc_entries=()`
     (`project_page.py`); the packager rebuilds one nav entry per chapter
     (`epub_packager.py:468-513`). (S11-08 known loss layer.)
  2. Fixed-layout: detected/recorded only; no layout-specific rendering.
  3. Glossary is bound in Translation Studio (ProjectPage), not in the
     `ui/translation_launcher` shell (`controller.py:46,205` `glossary_path=None`) —
     consistent with the S12-01 reader-first scope; a scope boundary, not a defect.
- **EPUB correctness gap vs feature limitation:** separated — correctness gap = NONE;
  limitations = the three items above.

## 6. TXT Capability

- Real path `lts/txt_translation_runtime.py` → canonical engine; `glossary_path` +
  `glossary_hash` on `TxtTranslationOptions` (`:123-124`); project glossary reaches
  prompt package + post-processing; resume/recovery; Open Result.
- Classification: **PRODUCTION READY**. Glossary integration introduced no TXT regression
  (S12-04 TXT E2E; S12-07 regression).

## 7. Project Persistence

- `ProjectStore` at `<NTPE_HOME>/projects/<id>/project.json`, atomic `os.replace`,
  schema v1, SHA-256 source identity.
- Glossary additive state is backward compatible: `ReaderProject.glossary: GlossaryRecord
  | None = None` (`models.py:310`) and `ReaderProject.from_dict` reads
  `data.get("glossary")` → `None` when absent (`models.py:334-343`). A legacy project.json
  without a `glossary` key loads successfully with `glossary=None`.
- Classification: **PASS**. No schema change required by S12.

## 8. Recovery

- `check_recovery_eligibility` deterministic gates (source identity, project identity,
  runtime artifact, glossary hash). Glossary-hash gate: same hash → eligible; different
  hash → `blocked_by="glossary"` (S12-02/S12-04 tests).
- Legacy artifact without a glossary hash: no glossary gate to violate → unaffected
  (backward compatible); glossary is only compared when the active project has a hash.
- Classification: **PRODUCTION READY**. No new Recovery feature added; contract unchanged.

## 9. Output / Artifact Portability

- `OutputRecord{output_dir, artifact_path, artifact_kind, available}` persisted by
  `project_page._persist_translation_result`.
- Absolute-path portability: real but a **portability limitation** — relocating
  `NTPE_HOME` yields a truthful "結果檔案不存在" failure state, not corruption.
- Stale `available`: the UI recomputes `output_exists` from the filesystem at render
  (`ui/translation_studio/project_view_model.py:69-74`) and gates controls on it
  (`:93-95`), so a stale persisted flag is not reader-facing corruption.
- Classification: **LIMITATION / DEFERRED** (product decision required); not an active
  correctness defect.

## 10. Translation Studio

- `ProjectPage` glossary panel, translation controls and result state remain real,
  observable, persistent and canonical (S12-03/S12-04/S12-07).
- Classification: **PASS**. No new fake control.

## 11. Launcher / CLI

- Two shells over canonical runtimes (`ui/translation_studio`, `ui/translation_launcher`);
  CLI `translate` plus internal commands. No hidden second translation route.
- Glossary binding uses canonical options only (`apply_glossary_to_options` →
  `dataclasses.replace`), and the runtime/provider layer has **no** glossary import
  (grep: no `glossary` in `core/runtime_orchestrator`, `core/translation_engine`,
  `provider`). No special glossary runtime.
- Classification: **PASS** (launcher shell glossary-off is a documented scope boundary).

## 12. Runtime Architecture

- Single canonical route: `UI/CLI → TranslationRuntime → RuntimeOrchestrator →
  TranslationEngine → ProviderManager → NvidiaTranslationProvider → NvidiaClient →
  LiteraryPromptBuilder`.
- Frozen model `meta/llama-3.2-90b-vision-instruct` re-confirmed at
  `core/config.py:19`, `lts/txt_translation_runtime.py:83`,
  `core/epub_translation/runtime/adapter.py:56`.
- Classification: **PASS**. S12 did not alter the route or model.

## 13. Character / Context Memory

- `quality_character_memory_v72` / `quality_context_scene_v72` default `False` in the TXT
  and EPUB option surfaces (`lts/txt_translation_runtime.py:148-149`,
  `core/epub_translation/runtime/adapter.py:105-106`). No hidden default-on activation;
  glossary does not enable memory (no memory import in the glossary path).
- Classification: **EXPERIMENTAL / DEFAULT-OFF** (deferred).

## 14. Literary Quality

- Production behavior is advisory QA only. S7 calibration remains `NOT AUTHORIZED`
  (`artifacts/NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md`); external evaluators + reference
  data missing. Glossary completion does not change this.
- Classification: **OBSERVATIONAL / DEFERRED** (quality-program gap).

## 15. QA / Validation

- Advisory guards in `BasicTranslationQA` + `runtime_qa`; `core/validator.py` and the
  Stage-15 engine remain without production importers; Korean/length/omission checks are
  duplicated. S12 glossary validation (`verify_snapshot_file`, hash gate) is additive and
  does not conflict with existing QA; import parsing is duplicated TXT/EPUB (known
  maintainability item).
- Classification: **MAINTENANCE / REFACTOR DEBT** (advisory only; no correctness risk
  demonstrated).

## 16. Security

- EPUB extraction ZIP guards unchanged (`_validate_zip_security`): entry-count/size caps,
  traversal/absolute/UNC/symlink/duplicate/executable/nested-archive/zip-bomb/encryption
  blocks. S12-06 validator repair changed only the offset comparison, not bounds/ownership
  checks. Glossary snapshot path is project-scoped and validated (`glossary_snapshot_path`
  rejects invalid hashes).
- Classification: **PASS**. No weakening.

## 17. Testing Architecture / Test Debt

- S12 added real-adapter regressions: `test_s12_06_epub_chunk_offset_repair.py` (real
  adapter path, offset negatives) and `test_s12_07_glossary_epub_real_adapter_e2e.py`
  (reader-first UI → real adapter → real packaging → persisted read-back). The real EPUB
  adapter is no longer an uncovered capability.
- Pre-existing debt unchanged and not S12-caused:
  - legacy `launcher_*` import-time `SystemExit` (~79 files);
  - legacy root-module collection errors (~90);
  - stale unit/contract expectations (~58);
  - frozen LCR/TIC fixture locks;
  - shared Qt e2e session Windows access violation (S12-07 worked around it by
    integration placement, same as S11-10).
- Classification: **PASS with pre-existing TEST INFRASTRUCTURE DEBT**.

## 18. Legacy / Archive Surface

- `core/translation_release/reader_structure/models.py` is imported by the canonical
  `core/epub_translation/reader_chapter_map.py:19` → **not fully orphan; split before any
  archive**.
- `core/translator.py`, `engine/`, `core/validator.py`,
  `core/context/memory_engine.py`, `tools/legacy_pipeline_launchers/`, and orphan
  top-level dirs remain unreferenced by the reader path.
- Classification: **LEGACY / ARCHIVE CANDIDATE** (`translation_release` = SPLIT first);
  **REMOVE NOT AUTHORIZED**.

## 19. Repository Hygiene

- No new root noise from S12; diagnostics under `artifacts/`.
- Naming drift (repository hygiene, non-automation): the S11-11 capability matrix file is
  named `NPTE_S11_11_CURRENT_CAPABILITY_MATRIX.md` (typo `NPTE`) though its own title and
  peer are `NTPE_...`; it also references `artifacts/NPTE_S11_11_PROGRAM_AUDIT.md`, but the
  actual file is `NTPE_S11_11_PROGRAM_AUDIT.md`. No code/automation references either name.
- S12 artifact naming is consistent (`NTPE_S12_0*`).
- Classification: **REPOSITORY HYGIENE** (do not rename in this audit).

## 20. Blockers Analysis

| Category | Finding |
|---|---|
| Current production correctness blocker (reader-first TXT/EPUB) | **NONE** |
| Correctness-limitation (non-blocking) | Output absolute-path portability; EPUB TOC structural fidelity; EPUB fixed-layout; launcher shell glossary-off |
| Product gap (deferred) | Glossary EPUB prompt parity; CSV import |
| Deferred quality program | S7 literary calibration (external data) |
| Experimental | Character / Context-Scene memory |
| Maintenance / refactor debt | QA guard consolidation; dead code (`core/validator.py`, Stage-15) |
| Legacy / archive candidate | `engine/`, `core/translator.py`, orphan dirs; `translation_release` (split first) |
| Test infrastructure debt | Launcher collection, legacy root modules, Qt e2e session, stale expectations |

Glossary incompleteness, literary calibration, experimental memory, portability and legacy
code are **not** current correctness blockers.

## 21. Next Workstream Ranking (evidence-ranked)

No correctness blocker exists; ranking is by reader-facing value / verification risk:

1. **Output portability / stale-artifact refresh** — the only reader-facing residual
   (relocation semantics + persisted `available`); needs a product decision, bounded.
2. **E2E test infrastructure reliability** — the shared Qt session forced integration
   placement in S11-10 and S12-07; stabilizing it improves future verification confidence.
3. **Glossary bounded enhancement** — EPUB prompt parity + CSV (now unblocked, deferred).
4. **QA guard consolidation** — remove dead duplicates without changing advisory semantics.
5. **Legacy / orphan archive program** — archive (not remove) with dependency proof; split
   `core/translation_release` first.
6. **S7 literary calibration** — blocked on external human evaluators + reference data.

## 22. S12 Program Decision

**COMPLETE (recommendation).**

There is no unresolved production correctness blocker for the reader-first TXT/EPUB
product. The Glossary MVP is implemented and reader-first verified for both TXT and EPUB
(with real adapter, real packaging, persisted artifact and fresh read-back); the EPUB
offset defect is audited, repaired and regression-locked; spine ordering, non-linear
semantics and TOC fallback remain CLOSED; security is unchanged; the canonical runtime is
single and frozen.

`COMPLETE ≠ everything is finished` — all remaining items fall into: future feature
(glossary prompt parity, CSV), quality debt (QA consolidation, literary calibration),
test-infrastructure debt (Qt e2e, legacy collection), experimental (memory), legacy
(archive candidates), deferred (output portability).

Per governance, this audit only recommends; it does **not** create an `s12-complete` tag.

## 23. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
Production Files Modified : NO
Tests Modified            : NO
```

## 24. Diff Hygiene

Only new audit artifacts under `artifacts/` are added. `core/`, `lts/`, `engine/`, `ui/`,
`cli/`, `tests/` unchanged. Pre-existing dirty state preserved. No scratch/root files or
generated sandboxes produced (source inspection only).

## 25. Acceptance

All required report sections covered; S12-01..S12-07 marked CLOSED; Glossary and EPUB
offset reconciled from their old classifications; capability matrix and residual register
produced; blockers separated from limitations/features/debt; program decision
evidence-backed; no implementation performed.
