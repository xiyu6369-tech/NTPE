# NTPE S12-08 — Residual Gap Register

Companion to `artifacts/NTPE_S12_08_PROGRAM_AUDIT.md`. Baseline HEAD `5ea85b4`,
branch `main`.

Classification vocabulary (only): CLOSED · ACTIVE CORRECTNESS GAP · ACTIVE PRODUCT GAP ·
QUALITY DEBT · TEST INFRASTRUCTURE DEBT · MAINTENANCE / REFACTOR · DEFERRED ·
EXPERIMENTAL · LEGACY / ARCHIVE CANDIDATE.

| # | Item | Classification | Basis / Evidence |
|---|---|---|---|
| R1 | Glossary contract / design (S12-01) | CLOSED | `artifacts/NTPE_S12_01_*`; option binding design |
| R2 | Glossary backend / project integration (S12-02) | CLOSED | `core/reader_project/glossary.py`; `manager.attach/replace/detach/resolve_glossary` |
| R3 | Glossary reader UX (S12-03) | CLOSED | `project_page.py::_on_glossary_import/_on_glossary_detach`; 20 UI tests |
| R4 | Glossary reader-first E2E (S12-04) | CLOSED | `tests/integration/test_s12_04_*`; EPUB block closed by S12-07 |
| R5 | EPUB chunk offset contract audit (S12-05) | CLOSED | `artifacts/NTPE_S12_05_*` |
| R6 | EPUB chunk offset repair (S12-06) | CLOSED | `validation.py::validate_epub_translation_chunk`; `test_s12_06_*` |
| R7 | EPUB real-adapter glossary E2E (S12-07) | CLOSED | `test_s12_07_*`; persisted EPUB read-back |
| R8 | EPUB spine ordering | CLOSED | S11-03/04/10 |
| R9 | EPUB non-linear semantics | CLOSED | S11-06/07/10 |
| R10 | EPUB TOC fallback | CLOSED | S11-08/09/10 |
| R11 | EPUB extraction offsets (body/marker) | CLOSED | S10-02; S12-05/06/07 |
| R12 | EPUB original TOC structural fidelity (`toc_entries=()`) | DEFERRED | production rebuilds one nav entry/chapter (`epub_packager.py:468-513`); product enhancement |
| R13 | EPUB fixed-layout rendering | DEFERRED | detected/recorded only |
| R14 | Glossary EPUB prompt parity | DEFERRED | S12-01 bounded enhancement; MVP post-processing verified (S12-07) |
| R15 | Glossary CSV import | DEFERRED | S12-01 `DEFERRED`; no requirement change |
| R16 | Glossary not bound in `translation_launcher` shell | DEFERRED | `ui/translation_launcher/controller.py:46,205` `glossary_path=None`; S12-01 reader-first scope |
| R17 | TXT reader-first path | CLOSED | `lts/txt_translation_runtime.py`; glossary `:123-124`; S12-04/S12-07 |
| R18 | Project persistence schema v1 / backward compat | CLOSED | `ReaderProject.glossary=None` default; `from_dict` tolerates missing key (`models.py:310,334-343`) |
| R19 | Recovery (source/project/artifact/glossary-hash gates) | CLOSED | `check_recovery_eligibility`; S12-02/04 recovery tests |
| R20 | Output absolute-path portability | DEFERRED | truthful failure state on relocation; product decision required |
| R21 | Output stale `available` flag | QUALITY DEBT | UI recomputes `output_exists` from filesystem (`project_view_model.py:69-95`); not reader corruption |
| R22 | Translation Studio controls/state | CLOSED | S12-03/S12-07; no fake control |
| R23 | Launcher / CLI single canonical route | CLOSED | no second translation route; glossary uses canonical options only |
| R24 | Runtime architecture / frozen model | CLOSED | `meta/llama-3.2-90b-vision-instruct` (`config.py:19`, `txt_translation_runtime.py:83`, `adapter.py:56`) |
| R25 | Character Memory default-off | EXPERIMENTAL | `quality_character_memory_v72=False` (`txt_translation_runtime.py:148`, `adapter.py:105`) |
| R26 | Context / Scene Memory default-off | EXPERIMENTAL | `quality_context_scene_v72=False` (`txt_translation_runtime.py:149`, `adapter.py:106`) |
| R27 | S7 literary quality calibration | DEFERRED | `NTPE_S7_14_CALIBRATION_BLOCKER_STATUS.md` (`NOT AUTHORIZED`); external evaluators/data missing |
| R28 | QA guard duplication; dead `core/validator.py` / Stage-15 engine | MAINTENANCE / REFACTOR | no production importers; advisory only |
| R29 | S12 glossary import parsing duplicated TXT/EPUB | MAINTENANCE / REFACTOR | known maintainability item; no correctness risk |
| R30 | Security (ZIP guards, path normalization, snapshot path validation) | CLOSED | unchanged; S12-06 repair touched only offset comparison |
| R31 | Legacy test collection: `launcher_*` import-time `SystemExit` (~79) | TEST INFRASTRUCTURE DEBT | pre-existing; not S12-caused |
| R32 | Legacy root-module collection errors (~90) | TEST INFRASTRUCTURE DEBT | pre-existing |
| R33 | Stale unit/contract expectations (~58) | TEST INFRASTRUCTURE DEBT | pre-existing (LCR/quality/stage suites) |
| R34 | Frozen LCR/TIC fixture worktree locks (`lcr_batch3/4`) | TEST INFRASTRUCTURE DEBT | global `git status` allowlist; already violated by residual dirty state |
| R35 | Shared Qt e2e session Windows access violation | TEST INFRASTRUCTURE DEBT | S11-10 §6; S12-07 worked around via integration placement |
| R36 | UI provider path mocked in `tests/ui` | TEST INFRASTRUCTURE DEBT | UI wiring by design; real path covered by S12-07 integration |
| R37 | Real EPUB adapter previously uncovered | CLOSED | now directly covered by S12-06/S12-07 |
| R38 | Legacy stack: `engine/`, `core/translator.py`, orphan top-level dirs | LEGACY / ARCHIVE CANDIDATE | unreferenced by reader path; REMOVE not authorized |
| R39 | `core/translation_release` delivery subsystem | LEGACY / ARCHIVE CANDIDATE | SPLIT first: `reader_structure/models.py` imported by canonical `reader_chapter_map.py:19` |
| R40 | `core/context/memory_engine.py` superseded | LEGACY / ARCHIVE CANDIDATE | referenced only by `core/foundation/compatibility.py` |
| R41 | Pre-existing residuals (`memory/character_memory_lts.json`, four literary outputs) | EXTERNAL DIRTY STATE (protected) | not S12 defects; must remain untouched |
| R42 | S11-11 capability matrix filename typo `NPTE_` + broken internal ref | MAINTENANCE / REFACTOR | filename `NPTE_S11_11_CURRENT_CAPABILITY_MATRIX.md`; content refs `NPTE_S11_11_PROGRAM_AUDIT.md` (actual `NTPE_...`); no code/automation reference; do not rename here |

## Summary by class

```text
CLOSED                         : R1-R11, R17-R19, R22-R24, R30, R37
DEFERRED                       : R12-R16, R20, R27
QUALITY DEBT                   : R21
MAINTENANCE / REFACTOR         : R28, R29, R42
TEST INFRASTRUCTURE DEBT       : R31-R36
EXPERIMENTAL                   : R25, R26
LEGACY / ARCHIVE CANDIDATE     : R38-R40
EXTERNAL DIRTY STATE (protected): R41

ACTIVE CORRECTNESS GAP         : NONE
ACTIVE PRODUCT GAP             : NONE
```

No item is classified with vague wording. The only reader-facing residual is R20/R21
(output portability / stale flag), which is a deferred limitation, not a correctness gap.
