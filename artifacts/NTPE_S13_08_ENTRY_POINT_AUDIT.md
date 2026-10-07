# NTPE S13-08 — Entry-Point Audit

Companion to `artifacts/NTPE_S13_08_TOP_LEVEL_INVENTORY.md`. Baseline HEAD `02745cf`.
Audit-only; no entry point modified.

## 1. Method

Enumerate executable entry points by scanning for `if __name__ == "__main__"`,
`__main__.py`, argparse `main()` members, root script wrappers, and console-script tables
(`pyproject.toml` has none). For each: entry → imported module → runtime path → production
relevance.

## 2. Canonical entry points (reader-facing production)

| Entry | Path | Reaches | Evidence |
|---|---|---|---|
| Production CLI | `ntpe_production_translate.py` | `core.*` + `lts.*` + `ntpe_literary_*` | imports `core.translation_runtime`, `lts.txt_translation_runtime`, adapters |
| CLI wrapper | `launcher_translate.py` | `ntpe_production_translate.main` | `from ntpe_production_translate import main` |
| GUI | `ntpe_translation_studio.py` | `ui.translation_studio.app.run` | `from ui.translation_studio.app import run` |
| GUI (launcher) | `ui/translation_launcher/*` | canonical EPUB packaging + `lts` runtime | `ui/translation_launcher/worker.py:109-164` |
| GUI (studio) | `ui/translation_studio/*` | canonical EPUB/TXT runtime | `ui/translation_studio/translation_worker.py:88-143` |

## 3. Secondary supported entry points

| Entry | Path | Purpose | Evidence |
|---|---|---|---|
| Public API facade | `ntpe/quality`, `ntpe/corpus`, `ntpe/cli` | programmatic quality/corpus API | collected tests `tests/unit/public_api/*` import `ntpe.quality`/`ntpe.corpus` |
| SDK | `sdk/client.py`, `sdk/translation.py` | programmatic SDK; uses `TranslationOrchestrator` | imported by `tests/*` (all `launcher_*`, quarantined) |
| Web reader app | `web/reader/app` | separate Next.js product surface | `package.json`/`next.config.js`; no Python reference |
| Literary tooling | `ntpe_literary_regression.py`, `ntpe_literary_evaluation.py` | regression/eval helpers | imported by canonical `ntpe_production_translate.py` |

## 4. Development / maintenance tooling entry points

| Entry | Path | Purpose |
|---|---|---|
| One-shot/maintenance tools | `tools/**` (114 `__main__`) | diagnostics, generation, migrations |
| Scratch/allowed one-shots | `tools/one_shots/**` | sanctioned scratch location |
| Root-hygiene scripts | `scripts/{classify_root_files,list_root_py,rm_4_2a_execute}.py` | dev scripts |
| Knowledge benchmark CLI | `tools/knowledge_benchmark/*` | reads `benchmarks/golden` |
| Validation tool | `tools/one_shots/ntpe_validate.py` | `importlib.import_module` module checks |

## 5. Verification entry points

| Entry | Path | Purpose | Evidence |
|---|---|---|---|
| Verification harness | `verification/_bootstrap.py`, `verification/conftest.py`, `verification/**` (20 `__main__`) | acceptance/freeze helpers | **collected** tests import `verification.controlled_runtime.*` |

`verification/` is loaded by collected contract/integration tests
(`tests/contract/controlled_multi_chunk_translation_canary/test_artifact_root_contract.py`,
`tests/integration/controlled_runtime_execution_authorization_contract_test.py`) → active
test infrastructure, not an orphan.

## 6. Legacy launchers / historical entry points

| Entry | Path | Status | Evidence |
|---|---|---|---|
| Standalone CLI framework | `cli/__main__.py` (`raise SystemExit(main())` at import) | LEGACY | only quarantined `tests/beta_stage_06_*` import `cli.*` |
| Legacy pipeline launchers | `tools/legacy_pipeline_launchers/*` | LEGACY | import dead `engine.*` |
| Packaging/maintenance entries | `packaging/**` (1 `__main__`) | LEGACY | tests are `launcher_*` (quarantined) |
| Archived entries | `archive/**` (308 `__main__`) | HISTORICAL | out of scope |
| Beta/RC launcher wrappers | `tests/beta_stage_*`, `tests/rc_stage_*` | QUARANTINED | `tests/conftest.py` |

## 7. Orphan entry points

No entry point is proven orphan (zero reasonable caller). The nearest candidate,
`cli/__main__.py`, has quarantined legacy callers and a `core/enterprise` existence probe,
so it is **LEGACY — ARCHIVE CANDIDATE (deferred)**, not orphan.

## 8. Entry-point → reachability summary

```text
CANONICAL   : ntpe_production_translate.py, launcher_translate.py, ntpe_translation_studio.py,
              ui/translation_studio, ui/translation_launcher
SECONDARY   : ntpe/ (public API), sdk/, web/ (separate product), ntpe_literary_*
TOOLING     : tools/, scripts/, tools/one_shots/, tools/knowledge_benchmark/
TEST INFRA  : tests/, verification/
LEGACY      : cli/, tools/legacy_pipeline_launchers/, packaging/ (entry only), archive/
ORPHAN      : none proven
```

No legacy entry point is on, or reachable from, a reader-facing runtime path.
