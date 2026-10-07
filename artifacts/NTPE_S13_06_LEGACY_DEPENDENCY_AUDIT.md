# NTPE S13-06 — Legacy & Orphan Dependency Reconciliation Audit

Audit-only / no deletion. No production, test, import, runtime, EPUB/TXT/Glossary/Output/
Recovery or pytest-boundary change.

## 0. Baseline

```text
Repository    : D:\Python\NTPE
Branch        : main
Baseline HEAD : 79d1acd676282d93e54ee807dae296347adc3893
origin/main   : 79d1acd
Actual HEAD   : S13-06 audit commit (this commit; see final report / git log)
```

Pre-existing dirty state preserved. No reset / clean / restore --source / force-pull /
force-push / discard performed.

## 1. Method

For every candidate: reverse-map **caller → imports → exports → registry/factory →
CLI/UI → dynamic import**, distinguishing `CANONICAL PRODUCTION`, `ACTIVE SECONDARY`,
`LEGACY PRODUCTION`, `TEST-ONLY`, `NO ACTIVE CALLER`, `UNKNOWN`. A single grep is never
sufficient; historical dynamic-import governance evidence is cross-checked
(`archive/historical/audits/architecture_consolidation/batch5a_usage/`).

## 2. Audit A — Production dependency

Precise import scan from canonical roots (`core/`, `lts/`, `ui/`, `ntpe_production_translate.py`):

| Candidate | Direct production caller(s) | Indirect/registry/dynamic | Canonical route? |
|---|---|---|---|
| `core/translation_release/reader_structure/models.py` | `core/epub_translation/reader_chapter_map.py:19` | package `__init__`→`polish`→`core.translation_runtime.runtime_formatter`; `reader_structure/__init__`→`chapter_mapper`,`epub_packager` | **YES** (EPUB packaging) |
| `core/translation_release` (delivery subset) | none (only test-only `core/adapters/rm8_delivery_adapter.py:7-8`) | none found (no registry/config/manifest refs) | no |
| `engine/` (16 modules) | none (only orphan `core/translator.py:15`; standalone `tools/legacy_pipeline_launchers/*`) | none | no |
| `core/translator.py` | none | none (only archived/audit references) | no |
| `core/expansion/` (4 modules) | none (only dead `engine/pipeline/pipeline_v1.py:15`) | none | no |
| `core/context/` (7 modules) | none (only dead `engine/pipeline/pipeline_v1.py:12`) | **dynamic**: `core/foundation/compatibility.py:10,31` (`import_module("core.context")`) | no |
| `core/quality/` (33 modules) | none (only dead `engine/pipeline/*`, `core/expansion/expansion_planner.py:5`) | none | no |
| `core/foundation/compatibility.py` | none | dynamic-import holder (see `core/context`) | no |

Key evidence:
- The **only** live canonical dependency on `core.translation_release` is
  `core/epub_translation/reader_chapter_map.py:19` importing
  `ChapterBoundary, ReaderChapterMap` from `core.translation_release.reader_structure.models`.
  That module is reached by the canonical EPUB packager used by
  `ui/translation_studio/translation_worker.py:88-89` and `ui/translation_launcher/worker.py:109-110`.
- `core/adapters/rm8_delivery_adapter.py` (the only importer of the delivery subset) has
  **no production importer** — only `tests/unit/adapters/test_rm8_delivery_adapter.py`.
- Python semantics: `import core.translation_release.reader_structure.models` executes
  `core/translation_release/__init__.py` (→ `polish`) and
  `core/translation_release/reader_structure/__init__.py` (→ `models`, `chapter_mapper`,
  `epub_packager`). Those siblings are therefore on the canonical **import path** even
  though only `models` is logically used.

## 3. Audit B — Test dependency

| Candidate | Canonical tests | Legacy tests | Fixture/conftest | Collection |
|---|---|---|---|---|
| `core/translation_release.reader_structure.models` | `tests/contract/test_s4_epub_reader_chapter_map.py:33`; `tests/unit/translation_release/reader_structure/*` | — | — | collected |
| `core.translation_release` (whole) | `tests/unit/translation_release/*` | archived `archive/stage_tests/ntpe_te_v600_final_release_freeze_test.py` | — | collected |
| `core/quality` | — | `tests/unit/test_stage15_2..8*.py`; `tests/stage_15_*`; `tests/integration/test_stage15_2_quality_engine_completeness_integration.py`; note `tests/conftest.py:13` cites `core.quality.quality_context` as a **removed** module | — | partial (stage15_4/5 quarantined) |
| `core/context` | — | `tests/characterization/batch5a1_parity_support.py:7`; `tests/launcher_context_memory_test.py:4` | — | characterization collected; launcher test quarantined |
| `engine/` | — | **none** | — | n/a |
| `core/expansion/` | — | **none** | — | n/a |
| `compatibility/` (top-level) | — | `tests/rc_stage_02/*` (quarantined `rc_stage_*`) | — | quarantined |

No S13-03 quarantine is hiding an active **canonical** dependency. The quarantine only
masks legacy suites; it does not make their candidates production-safe.

## 4. Audit C — Runtime reachability

```text
TXT / ReaderProject / Recovery / Output / Translation Studio / Launcher / CLI
```

- `core.translation_release.reader_structure.models` → **reachable** (canonical EPUB packaging).
- `core.translation_release` delivery subset → **not reachable** by any reader-facing route
  (only the test-only `rm8_delivery_adapter`).
- `engine/`, `core/translator.py`, `core/expansion/`, `core/context/`, `core/quality/` →
  **not reachable** by any reader-facing route.

Strict distinction respected:
- "canonical path does not currently use it" = engine, translator, expansion, context, quality, delivery subset.
- "no production path can use it" = **not** claimed for any candidate (dynamic/tool/legacy-test
  references remain for several).

## 5. Audit D — `core/translation_release` split

See `artifacts/NTPE_S13_06_TRANSLATION_RELEASE_SPLIT_ANALYSIS.md`.

**Result: DEPENDENCY TO SPLIT.** Live canonical subset is small
(`reader_structure/models.py` + import-path siblings + `polish`); the delivery subset is
legacy/test-only. `core/translation_release` must **not** be classified as removable.

## 6. Audit E — Historical artifacts vs executable code

Top-level inspection (not name-based):

| Path | Tracked `.py` | Nature | Classification |
|---|---|---|---|
| `analysis/` | 0 | glossary JSON data | DATA/asset (not code) |
| `benchmarks/` | 0 | golden JSON fixtures | TEST DATA |
| `profiles/` | 0 | profile JSON | CONFIG DATA |
| `web/` | 0 | Next.js reader web app (TS/JS) | SEPARATE PRODUCT surface |
| `compatibility/` | 6 | audit registry, imported only by quarantined `tests/rc_stage_02/*` | LEGACY / TEST-ONLY |
| `engine/` | 16 | legacy pipeline engine | LEGACY |
| `archive/` | many | historical evidence/tests | HISTORICAL (out of scope) |

Names containing `stage`/`legacy`/`foundation`/`rm5` were **not** treated as removal
triggers anywhere in this audit.

## 7. Required classification

| Candidate | Production caller | Test caller | Runtime reachable | Classification | Recommended action |
|---|---|---|---|---|---|
| `core/translation_release/reader_structure/models.py` | CANONICAL (`reader_chapter_map.py:19`) | contract/unit | YES | **CANONICAL — KEEP** | preserve; relocate in future split |
| `core/translation_release/reader_structure/{__init__,chapter_mapper,epub_packager}.py` | import-path via canonical | unit | import-path | **DEPENDENCY TO SPLIT** | preserve until split |
| `core/translation_release/polish.py`, `__init__.py` | import-path via canonical | unit | import-path | **DEPENDENCY TO SPLIT** | preserve until split |
| `core/translation_release` delivery subset | none (test-only adapter) | unit translation_release | no | **DEPENDENCY TO SPLIT** | split/archive candidate later |
| `engine/` | none (orphan `core/translator.py`; tools scripts) | 0 | no | **LEGACY — ARCHIVE CANDIDATE** | resolve `core/translator.py`+tools first |
| `core/translator.py` | none | 0 (historical HIGH_RISK flag) | no | **DEFERRED** | do not remove (compat impact unproven) |
| `core/expansion/` | none (dead engine only) | 0 | no | **LEGACY — ARCHIVE CANDIDATE** | archive with engine cluster |
| `core/context/` | none (dead engine only) | characterization + legacy launcher | no | **DEFERRED** | test + dynamic refs unresolved |
| `core/quality/` | none (dead engine/expansion) | collected legacy stage15 | no | **LEGACY — ARCHIVE CANDIDATE** | blocked by test deps + missing submodules |
| `core/foundation/compatibility.py` | none | legacy foundation test | no | **LEGACY / TEST-ONLY** | keep (holds dynamic ref) |
| top-level `compatibility/` | none | quarantined rc_stage | no | **LEGACY / TEST-ONLY** | deferred |
| other top-level dirs (`cli`,`sdk`,`web_ui`,`platform_services`,`external_api`,`runtime_api`,`stable_release`,`release_candidate`,`packaging`,`benchmark`,`performance`,`workflow`,`translation`,`verification`,`integration`,`ntpe`,`regression`,`scripts`,`tools`) | not imported by canonical roots | mixed | unproven | **UNKNOWN / DEFERRED** | dedicated top-level audit required |

## 8. Archive safety gates

Required for any future removal:

```text
production caller = 0
test caller = 0
dynamic reference = 0
export/compatibility surface = none
canonical path dependency = none
```

**Archive-safe candidates (all gates met): NONE.**

- `engine/`: gate fails (non-production static callers `core/translator.py` (DEFERRED) and
  `tools/legacy_pipeline_launchers/*`).
- `core/expansion/`: reachable only via the blocked `engine/` cluster.
- `core/context/`: dynamic ref (`core/foundation/compatibility.py`) + test callers.
- `core/quality/`: collected legacy test callers.
- `core/translator.py`: historical HIGH_RISK flag → compatibility impact not proven `none`.

## 9. Existing contracts

No CLOSED capability is reopened or redefined. The only interaction with a closed
capability is the **live** `core.translation_release.reader_structure.models` dependency of
canonical EPUB packaging — explicitly preserved as CANONICAL — KEEP / DEPENDENCY TO SPLIT.

## 10. Result

```text
translation_release live dependency : BOUNDED (reader_structure.models, canonical EPUB)
Production-safe removals identified : none
Archive candidates (blocked)        : engine, core/expansion, core/quality
Deferred / unknown                  : core/translator.py, core/context, top-level dirs
```

**FINAL: PASS**

See `artifacts/NTPE_S13_06_ARCHIVE_CANDIDATE_REGISTER.md` and
`artifacts/NTPE_S13_06_TRANSLATION_RELEASE_SPLIT_ANALYSIS.md`.
