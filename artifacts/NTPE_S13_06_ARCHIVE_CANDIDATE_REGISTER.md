# NTPE S13-06 — Archive Candidate Register

Companion to `artifacts/NTPE_S13_06_LEGACY_DEPENDENCY_AUDIT.md`. Baseline HEAD `79d1acd`.
Audit-only; nothing removed.

## Archive safety gates

A candidate may be considered for removal in a **future** task only if **all** hold:

```text
G1 production caller            = 0
G2 test caller                  = 0
G3 dynamic reference            = 0
G4 export/compatibility surface = none
G5 canonical path dependency    = none
```

Any unknown → `UNKNOWN / DEFERRED`; removal is not authorized by this audit.

## Register

| # | Candidate | G1 prod | G2 test | G3 dynamic | G4 export | G5 canonical | Classification | Recommended action |
|---|---|---|---|---|---|---|---|---|
| 1 | `core/translation_release/reader_structure/models.py` | **NO (live)** | no | no | package-`__init__` chain | **YES** | CANONICAL — KEEP | preserve; relocate in future split |
| 2 | `core/translation_release/reader_structure/{chapter_mapper,epub_packager}.py` | import-path only | no | no | `reader_structure/__init__` | import-path | DEPENDENCY TO SPLIT | preserve until split |
| 3 | `core/translation_release/polish.py` (+`__init__.py`) | import-path only | no | no | package `__init__` | import-path | DEPENDENCY TO SPLIT | preserve until split |
| 4 | `core/translation_release` delivery subset (`models`,`metadata`,`package`,`validator`,`delivery_pipeline`,`exporters/*`,`release_contract`,`release_manifest`,`release_validation`,`te_v6_release`) | none | unit translation_release | none found | package-internal | none | DEPENDENCY TO SPLIT | split/archive in a future task |
| 5 | `engine/` (16 modules) | none | **0** | 0 | `engine/__init__.py` empty | none | LEGACY — ARCHIVE CANDIDATE | blocked: depends on #6 + tools scripts |
| 6 | `core/translator.py` | none | 0 (historical HIGH_RISK) | 0 | unknown | none | DEFERRED | do not remove; compat impact unproven |
| 7 | `core/expansion/` (4 modules) | none (dead engine) | **0** | 0 | `__init__` exports ExpansionPlanner | none | LEGACY — ARCHIVE CANDIDATE | blocked by #5 |
| 8 | `core/context/` (7 modules) | none (dead engine) | characterization + legacy launcher | **YES** (`core/foundation/compatibility.py`) | `__init__` exports ContextBuilder | none | DEFERRED | resolve test + dynamic refs first |
| 9 | `core/quality/` (33 modules) | none (dead engine/expansion) | **collected stage15** | 0 | package re-exports (several `None`) | none | LEGACY — ARCHIVE CANDIDATE | blocked by test deps + missing submodules |
| 10 | `core/foundation/compatibility.py` | none | legacy foundation test | holder | dict API | none | LEGACY / TEST-ONLY | keep (holds #8 dynamic ref) |
| 11 | top-level `compatibility/` | none | quarantined `rc_stage_02` | 0 | package API | none | LEGACY / TEST-ONLY | deferred |
| 12 | top-level dirs `cli`,`sdk`,`web_ui`,`platform_services`,`external_api`,`runtime_api`,`stable_release`,`release_candidate`,`packaging`,`benchmark`,`performance`,`workflow`,`translation`,`verification`,`integration`,`ntpe`,`regression`,`scripts`,`tools` | not imported by canonical roots | mixed | unproven | unproven | unproven | **UNKNOWN / DEFERRED** | dedicated top-level audit required |
| 13 | `analysis/`,`benchmarks/`,`profiles/`,`web/` | n/a | n/a | n/a | n/a | no | DATA / SEPARATE PRODUCT | not code; out of removal scope |

## Archive-safe now

```text
NONE — no candidate satisfies all of G1..G5 in this audit.
```

The nearest candidates (`engine/`, `core/expansion/`) fail because they are reached by the
deferred `core/translator.py` and standalone `tools/legacy_pipeline_launchers/*` (static
non-production callers), so removal is not safe in isolation.

## Deferred / unknown detail

- **#6 `core/translator.py`** — 0 current importers, but the historical
  `BATCH5A_DYNAMIC_USAGE_AUDIT` governance evidence explicitly lists it in a HIGH_RISK set
  that must **not** be classified `SAFE_DELETE` (asserted by the quarantined
  `tests/integration/architecture_consolidation_batch5a_dynamic_usage_audit_test.py:54`).
  Compatibility impact is therefore not proven `none` → DEFERRED.
- **#8 `core/context/`** — a dynamic reference exists:
  `core/foundation/compatibility.py:8-17,29-52` maps `"context_pipeline": "core.context"`
  and calls `import_module(module_name)` (in a try/except). The holder is imported only by
  a legacy foundation test, but the dynamic reference still violates G3 → DEFERRED.
- **#9 `core/quality/`** — `core/quality/quality_context.py` and `quality_result.py` are
  absent; `core/quality/__init__.py:50-82` swallows the ImportError, so
  `TranslationQualityEngine` and friends are always `None`. Collected legacy stage15 unit
  tests import the package → G2 fails.
- **#12 top-level dirs** — none is imported by `core/`, `lts/`, `ui/` or
  `ntpe_production_translate.py`. That alone is **not** deletion proof: several are
  standalone entry-point subsystems (CLI, SDK, web UI, release tooling, benchmarks). Their
  entry-point activity was not audited here → UNKNOWN / DEFERRED.

## Non-regression note

This register does not reopen or alter any CLOSED contract. `core/translation_release`
remains intact; candidate #1 is explicitly recorded as a live canonical dependency.
