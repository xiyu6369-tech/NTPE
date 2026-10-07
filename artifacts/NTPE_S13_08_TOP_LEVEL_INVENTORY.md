# NTPE S13-08 — Top-Level Inventory & Dependency Audit

Audit-only / no deletion, no move, no import migration, no pytest-boundary change.

## 0. Baseline

```text
Repository    : D:\Python\NTPE
Branch        : main
Baseline HEAD : 02745cf10b52bf4c0a2e41d58aaf0e29e4199d22
origin/main   : 02745cf
Actual HEAD   : S13-08 audit commit (this commit; see final report / git log)
```

Pre-existing dirty state preserved. No reset / clean / restore --source / pull --rebase /
force-pull / force-push / discard performed.

## 1. Method

For every tracked top-level entry: static importers (production / test / tooling),
path-based and dynamic references (`importlib`, `__import__`, `subprocess`, manifests,
registries), executable entry points (`if __name__`, `__main__`, wrappers), reader-facing
reachability, and git last-touch (supporting evidence only). Name is never used as a
signal.

## 2. Root-level tracked files

| Path | Type | Classification |
|---|---|---|
| `ntpe_production_translate.py` | Python CLI entry | KEEP — CANONICAL |
| `launcher_translate.py` | Python entry (wrapper → `ntpe_production_translate.main`) | KEEP — CANONICAL |
| `ntpe_translation_studio.py` | Python GUI entry (→ `ui.translation_studio.app.run`) | KEEP — CANONICAL |
| `ntpe_literary_regression.py` | tooling (imported by canonical entry) | KEEP — ACTIVE TOOLING |
| `ntpe_literary_evaluation.py` | tooling (imported by canonical entry) | KEEP — ACTIVE TOOLING |
| `pyproject.toml`, `requirements.txt`, `README.md`, `VERSION.txt`, dotfiles | metadata | KEEP |

No `[project.scripts]` console-entry table exists in `pyproject.toml`; entry is via root
scripts only.

## 3. Top-level directory inventory

Legend: prod = imported by `core`/`lts`/`ui`/root entry; test = imported by `tests/`;
tool = referenced by `tools`/`scripts`/`core/enterprise` instrumentation; entry =
executable entry points present.

| Path | Purpose (evidence) | prod | test | tool | entry | Classification |
|---|---|---|---|---|---|---|
| `core/` | canonical runtime/libs | — | yes | yes | yes | KEEP — CANONICAL |
| `lts/` | canonical TXT runtime | yes (from core) | yes | yes | yes | KEEP — CANONICAL |
| `ui/` | canonical Translation Studio/Launcher | yes | yes | yes | yes | KEEP — CANONICAL |
| `config/` | config data JSON + `config_manager.py` (no importer) | 0 | 0 | tools read JSON | no | KEEP — SECONDARY (config data) |
| `manifests/` | freeze manifests read by `core/*/freeze.py` | yes | yes | yes | no | KEEP — CANONICAL (data) |
| `schemas/` | `schemas/knowledge` read by `core/knowledge_validation` | yes | yes | yes | no | KEEP — CANONICAL (data) |
| `memory/` | `memory/character_memory_lts.json` read/written by `lts` | yes | yes | yes | no | KEEP — CANONICAL (data) |
| `docs/` | documentation | 0 | 0 | 0 | no | KEEP — DOCUMENTATION |
| `tests/` | canonical test suite | n/a | canonical | yes | yes | KEEP — ACTIVE TEST INFRA |
| `benchmarks/` | golden fixtures read by `tools/knowledge_benchmark` | 0 | 0 (data) | yes | no | KEEP — ACTIVE BENCHMARK INFRA |
| `tools/` | dev/one-shot tooling (incl. `one_shots/`) | 0 | yes | self | yes (114) | KEEP — ACTIVE TOOLING |
| `scripts/` | root-hygiene dev scripts | 0 | 0 | self | yes (1) | KEEP — DEVELOPMENT TOOLING |
| `ntpe/` | public API facade (`quality`,`corpus`,`cli`) | 0 | **yes (collected `tests/unit/public_api`)** | 0 | no | KEEP — SECONDARY (public API) |
| `verification/` | verification harness; **collected** contract/integration tests import `verification.controlled_runtime.*` | 0 | **yes (collected)** | 0 | yes (20) | KEEP — ACTIVE TEST INFRA |
| `web/` | Next.js reader web app (separate product) | 0 | 0 | 0 | npm scripts | KEEP — SECONDARY (separate product) |
| `archive/` | historical tests/evidence | 0 | 0 | 0 | yes (308) | HISTORICAL ARTIFACT |
| `artifacts/` | audit outputs | 0 | 0 | 0 | yes (2) | AUDIT OUTPUT |
| `engine/` | legacy pipeline engine | via dead `core/translator.py` | 0 | `tools/legacy_pipeline_launchers` | no | LEGACY — ARCHIVE CANDIDATE (deferred, S13-06) |
| `cli/` | standalone CLI framework (`__main__` raises SystemExit) | 0 | yes (10/11 `launcher_*` → quarantined) | `core/enterprise` existence probe | yes | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `sdk/` | SDK + plugin registry/loader | 0 | yes (17/17 `launcher_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `integration/` | integration/extension framework | 0 | yes (19/19 `launcher_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `workflow/` | workflow/job framework (freeze manifests) | 0 | yes (10/10 `launcher_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `platform_services/` | service framework | 0 | yes (9/9 `launcher_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `external_api/` | REST API framework | 0 | yes (`beta_stage_12_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `runtime_api/` | runtime REST framework | 0 | yes (partial `launcher_*`) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `web_ui/` | server-rendered web UI framework | 0 | yes (`beta_stage_13_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `translation/` | `quality`/`consistency_audit` framework | 0 | yes (quarantined) | via `cli/commands/quality.py` | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `benchmark/` | benchmark framework | 0 | yes (7/7 `launcher_*` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `packaging/` | release packaging framework | 0 | yes (6/10 `launcher_*`) | 0 | yes | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `performance/` | perf stabilization framework | 0 | yes (`rc_stage_03` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `regression/` | regression harness | 0 | yes (`rc_stage_01` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `release_candidate/` | RC validation framework | 0 | yes (`rc_stage_05/06` → quarantined) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `stable_release/` | stable-release framework | 0 | yes (partial `launcher_*`) | 0 | no | LEGACY — ARCHIVE CANDIDATE (deferred) |
| `compatibility/` | compatibility-audit registry | 0 | yes (`rc_stage_02` → quarantined) | 0 | no | TEST-ONLY LEGACY (deferred) |
| `analysis/` | `*_glossary_auto.json` data | 0 | 0 | comment-only mention | no | HISTORICAL / DATA ARTIFACT |
| `profiles/` | `passion_profile.json` data | 0 | 0 | read only by dead `engine` | no | HISTORICAL / DATA ARTIFACT |
| `.agents/`, `.ai/`, `.codex/`, `.kilo/`, `.vscode/` | dev/agent config | 0 | 0 | 0 | no | DEVELOPMENT CONFIG |

## 4. Dynamic-reference findings (Audit C)

Dynamic resolution exists but resolves **caller-supplied** names:

```text
core/enterprise/deployment_*.py     -> importlib.import_module(BASELINE_MODULES)  (core.* only)
core/workflow/production_platform_freeze.py -> import_module(REQUIRED_MODULES)    (core.* only)
core/foundation/compatibility.py    -> import_module("core.context" etc.)         (legacy)
integration/extension_loader.py     -> import_module(manifest.entrypoint)         (manifest-driven)
sdk/plugin_loader.py                -> importlib.import_module(manifest.entrypoint) (manifest-driven)
tools/one_shots/ntpe_validate.py    -> importlib.import_module(module)            (tool list)
```

- No dynamic loader targets a top-level **legacy framework** directory (all concrete lists
  are `core.*`).
- `core/enterprise/deployment_foundation._package_inventory` performs an **existence
  probe** on `core,cl i,config,docs,tests` and `tools/one_shots/ntpe_validate.py` — a
  tooling reference to `cli/` and `config/` (non-functional).
- `tools/knowledge_benchmark/*` reads `benchmarks/golden`, `benchmarks/spec`,
  `benchmarks/results` by path → `benchmarks/` is an active tooling dependency.

## 5. Test-boundary findings (Audit D)

- `tests/conftest.py` (S13-03, unchanged; sha `7223032d`) quarantines only `tests/`
  subdirs and `launcher_*`/`integration/*_test.py` patterns; it does **not** touch any
  top-level candidate. Quarantine therefore does not hide a top-level dependency, nor does
  it prove removability.
- Collected canonical tests import `ntpe.quality`/`ntpe.corpus` (`tests/unit/public_api/*`)
  and `verification.controlled_runtime.*` (`tests/contract/...`,
  `tests/integration/controlled_runtime_execution_authorization_contract_test.py`) → both
  `ntpe/` and `verification/` are canonical test dependencies.
- The legacy frameworks (`cli`, `integration`, `workflow`, `sdk`, `platform_services`,
  `benchmark`, `web_ui`, `external_api`, `runtime_api`, `translation`, `performance`,
  `regression`, `release_candidate`, `compatibility`) are imported only by **quarantined**
  legacy suites (`beta_stage_*`, `rc_stage_*`, `launcher_*_test.py`).

## 6. Production reachability (Audit E)

No top-level legacy framework is reachable from any reader-facing route (`TXT`, `EPUB`,
`ReaderProject`, `Recovery`, `Output`, `Translation Studio`, `Launcher`, `CLI`,
`Glossary`). The only canonical-reachable assets are `core`, `lts`, `ui`, `config` (data),
`manifests`, `schemas`, `memory`, `ntpe` (public API), `verification` (test infra).

## 7. Verification

```text
collect-only   : 3954 collected, 0 errors
contract       : 338 passed
reader_project : 86 passed
e2e            : 55 passed
runtime        : 10 passed
compileall     : exit 0
```

All identical to the S13-07 baseline (no code/test/boundary change).

## 8. Result

```text
Top-level inventory      : complete (root files + 39 directories)
Archive-safe candidates  : NONE (no candidate satisfies G1..G6)
Deferred / unknown       : legacy framework set + compatibility + engine
```

See `artifacts/NTPE_S13_08_ENTRY_POINT_AUDIT.md` and
`artifacts/NTPE_S13_08_ARCHIVE_REGISTER.md`.
