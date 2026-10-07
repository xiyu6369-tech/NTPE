# NTPE S13-09 — Legacy Framework Entry-Point & Dynamic-Surface Audit (Batch A)

**Audit-only / No implementation / No deletion**

Audit of seven legacy framework subsystems per S13-08 recommendations.

## 0. Baseline

```text
Repository    : D:\Python\NTPE
Branch        : main
Baseline HEAD : 1dd6bf30a471c6b0833c776564ef3ac8303fc811
origin/main   : 1dd6bf3
```

Pre-existing dirty state preserved. No code modifications.

## 1. Subsystem Summaries

### 1.1 `compatibility/`

| Aspect | Finding |
|---|---|
| Production callers | **0** (no canonical production imports) |
| Test callers | 4 files, all `tests/rc_stage_02/*` (quarantined by `tests/conftest.py` `rc_stage_*`) |
| Entry points | **None** (no `__main__.py`, no `if __name__ == "__main__"`, no console scripts) |
| Dynamic imports | **None** (`importlib`, `__import__`, `module_from_spec`, `pkgutil` not used) |
| Subprocess/shell | **None** |
| Dynamic surface | Public API exports via `__init__.py`: `CompatibilityAuditRegistry`, `CompatibilityAuditRunner`, `build_compatibility_audit_manifest`, etc. |
| Production reachability | **Unreachable** from all reader-facing routes (TXT, EPUB, ReaderProject, Recovery, Output, Translation Studio, Launcher, CLI, Glossary) |
| Test boundary | All importers in `tests/rc_stage_02/*` → quarantined by `tests/conftest.py` `rc_stage_*` pattern |

**Classification**: **TEST-ONLY LEGACY** — Only dependency is quarantined legacy test suite. No production, tooling, or active entry-point dependency.

---

### 1.2 `cli/`

| Aspect | Finding |
|---|---|
| Production callers | **0** |
| Test callers | 11 files in `tests/beta_stage_06_*` (all quarantined by `tests/conftest.py` `beta_stage_*` and `launcher_*_test.py` patterns) |
| Entry points | **Yes**: `cli/__main__.py` → `raise SystemExit(main())`; `cli/main.py:159` `if __name__ == "__main__": raise SystemExit(main())` |
| Dynamic imports | **None** |
| Subprocess/shell | **None** |
| Dynamic surface | Exports via `__init__.py`: `CLIContext`, `CLIResult`, `CLICommand`, `CommandRegistry`, `build_cli_manifest`, `attach_cli_manifest`, `main`, `run_cli`. Internal `cli/freeze/compatibility.py` imports from `cli.main`. |
| Production reachability | **Unreachable** from reader-facing routes. Canonical CLI is `ntpe_production_translate.py`. |
| Test boundary | All test importers in `tests/beta_stage_06_*` → quarantined by `tests/conftest.py` `beta_stage_*` and `launcher_*_test.py` patterns. |
| Tooling reference | `core/enterprise/deployment_foundation.py` `_package_inventory()` probes for `cli/` directory existence (existence probe only). |

**Classification**: **LEGACY** — Entry point exists (`__main__.py`, `if __name__ == "__main__"`), but only legacy quarantined tests depend on it. Canonical CLI entry is `ntpe_production_translate.py`.

---

### 1.3 `runtime_api/`

| Aspect | Finding |
|---|---|
| Production callers | **0** from canonical reader-facing path. Indirectly used by `external_api/` which is used by `web_ui/` (separate product). |
| Test callers | 20+ files in `tests/beta_stage_11_*`, `tests/beta_stage_12_*` (all quarantined by `tests/conftest.py` `beta_stage_*`) |
| Entry points | **None** |
| Dynamic imports | **None** |
| Subprocess/shell | **None** |
| Dynamic surface | Extensive public API via `__init__.py` (`RuntimeApi`, `RuntimeSession`, `RuntimeJob`, `RuntimePipeline`, `RuntimeEvent`, `RuntimeResource`, `RuntimeMiddleware`, freeze validators, etc.) |
| Production reachability | **Unreachable** from canonical reader-facing routes. Used by `external_api/` → `web_ui/` which is a separate product surface (Next.js app). Not on canonical TXT/EPUB/ReaderProject/Recovery/Output paths. |
| Test boundary | All test importers in `tests/beta_stage_11_*`, `tests/beta_stage_12_*` → quarantined by `beta_stage_*` pattern. |

**Classification**: **LEGACY** — No canonical production dependency. Used by `external_api/` which is only used by `web_ui/` (separate product surface, Next.js app). All tests quarantined.

---

### 1.4 `integration/`

| Aspect | Finding |
|---|---|
| Production callers | **0** |
| Test callers | 20+ files in `tests/beta_stage_08_*`, `tests/beta_stage_09_*`, `tests/beta_stage_10_0` (all quarantined by `tests/conftest.py` `beta_stage_*` pattern) |
| Entry points | **None** |
| Dynamic imports | **Yes**: `integration/extension_loader.py:4` → `from importlib import import_module`. `ExtensionLoader.load_from_manifest()` uses `import_module(module_name)` where `module_name` comes from `ExtensionManifest.entrypoint` (format `module:attribute`). This is a **manifest-driven dynamic loader** — concrete module names are provided by extension manifests, not hardcoded. |
| Subprocess/shell | **None** |
| Dynamic surface | Extensive public API via `__init__.py`: `IntegrationCore`, `IntegrationRegistry`, `EventBus`, `ServiceContainer`, `ExtensionLoader`, `PluginIntegrationManager`, `BridgeManager`, `ExtensionLoader`, freeze validators, etc. |
| Production reachability | **Unreachable** from canonical reader-facing routes. |
| Test boundary | All test importers in `tests/beta_stage_08_*`, `tests/beta_stage_09_*`, `tests/beta_stage_10_0` → quarantined by `tests/conftest.py` `beta_stage_*` pattern. |

**Classification**: **LEGACY** — Contains a **manifest-driven dynamic loader** (`extension_loader.py`), but concrete module names come from extension manifests (not hardcoded). No production callers; all test dependencies quarantined.

---

### 1.5 `workflow/`

| Aspect | Finding |
|---|---|
| Production callers | **0** |
| Test callers | 10 files in `tests/beta_stage_09_*`, `tests/beta_stage_10_0` (all quarantined by `beta_stage_*` pattern) |
| Entry points | **None** |
| Dynamic imports | **None** |
| Subprocess/shell | **None** |
| Dynamic surface | Extensive public API via `__init__.py`: `WorkflowCore`, `WorkflowEngine`, `JobScheduler`, `PipelineOrchestrator`, `TaskQueue`, `WorkerRuntime`, `WorkflowPersistence`, freeze validators, etc. |
| Production reachability | **Unreachable** from canonical reader-facing routes. |
| Test boundary | All test importers in `tests/beta_stage_09_*`, `tests/beta_stage_10_0` → quarantined by `beta_stage_*` pattern. |

**Classification**: **LEGACY** — No production callers, no dynamic imports, no entry points. All test dependencies quarantined.

---

### 1.6 `platform_services/`

| Aspect | Finding |
|---|---|
| Production callers | **0** |
| Test callers | 9 files in `tests/beta_stage_10_*` (quarantined by `beta_stage_*` pattern) |
| Entry points | **None** |
| Dynamic imports | **None** |
| Subprocess/shell | **None** |
| Dynamic surface | Extensive public API via `__init__.py`: `PlatformServiceRegistry`, `PlatformServiceManager`, `PlatformServiceHost`, `ServiceDiscovery`, `PlatformConfig`, `HealthMonitor`, `Metrics`, `EventBus`, `EventBridge`, `LifecycleHooks`, `PolicyEngine`, `PolicyRegistry`, freeze validators, etc. |
| Production reachability | **Unreachable** from canonical reader-facing routes. |
| Test boundary | All test importers in `tests/beta_stage_10_*` → quarantined by `beta_stage_*` pattern. |

**Classification**: **LEGACY** — No production callers, no dynamic imports, no entry points. All test dependencies quarantined.

---

### 1.7 `external_api/`

| Aspect | Finding |
|---|---|
| Production callers | **0** from canonical reader-facing path. Used by `web_ui/` (separate Next.js product). `web_ui/rest_client.py` and `web_ui/web_app.py` import `external_api`. |
| Test callers | 16+ files in `tests/beta_stage_12_*` (quarantined by `beta_stage_*` pattern) |
| Entry points | **None** |
| Dynamic imports | **None** |
| Subprocess/shell | **None** |
| Dynamic surface | Extensive public API via `__init__.py`: `RestApi`, `create_rest_api`, `RestSessionApi`, `RestJobApi`, `RestPipelineApi`, `RestEventApi`, `RestResourceApi`, `RestAuthContext`, `RestMiddlewareChain`, freeze validators, etc. |
| Production reachability | **Unreachable** from canonical reader-facing routes. Used by `web_ui/` (separate Next.js product surface) which is not on the canonical TXT/EPUB/ReaderProject/Recovery/Output path. |
| Test boundary | All test importers in `tests/beta_stage_12_*` → quarantined by `beta_stage_*` pattern. |

**Classification**: **LEGACY** — No canonical production dependency. Used by `web_ui/` (separate Next.js product surface). All test dependencies quarantined.

---

## 2. Cross-Cutting Findings

### 2.1 No Production Callers
**None** of the seven subsystems have any direct or indirect caller in the canonical production path (`core/`, `lts/`, `ui/`, `ntpe_production_translate.py`, `launcher_translate.py`, `ntpe_translation_studio.py`, `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py`).

### 2.2 Test Dependencies Are All Quarantined
All test dependencies for all seven subsystems reside in test directories that are **quarantined** by `tests/conftest.py`:
- `compatibility/` → `tests/rc_stage_02/*` (quarantined by `rc_stage_*`)
- `cli/` → `tests/beta_stage_06_*` (quarantined by `beta_stage_*` and `launcher_*_test.py`)
- `runtime_api/` → `tests/beta_stage_11_*`, `beta_stage_12_*`
- `integration/` → `tests/beta_stage_08_*`, `beta_stage_09_*`, `beta_stage_10_0`
- `workflow/` → `tests/beta_stage_09_*`, `beta_stage_10_0`
- `platform_services/` → `tests/beta_stage_10_*`
- `external_api/` → `tests/beta_stage_12_*`

All these test directories are matched by `tests/conftest.py` `collect_ignore_glob` patterns (`beta_stage_*`, `rc_stage_*`, `launcher_*_test.py`).

### 2.3 No Active Entry Points (except `cli/`)
Only `cli/` has an executable entry point (`cli/__main__.py` → `raise SystemExit(main())`). All other six subsystems have **zero** entry points (`__main__.py`, `if __name__ == "__main__"`, console scripts, module `-m` invocation).

### 2.4 Dynamic Imports
Only **one** dynamic import found across all seven subsystems:
- `integration/extension_loader.py:4` → `from importlib import import_module`
  - Used by `ExtensionLoader.load_from_manifest()` where module name comes from `ExtensionManifest.entrypoint` (format `module:attribute`) — **manifest-driven**, not hardcoded.

No `subprocess`, `Popen`, `os.system`, `pkgutil`, `module_from_spec`, `__import__` elsewhere.

### 2.4 `web_ui/` and `external_api/` Relationship
`external_api/` is imported by `web_ui/rest_client.py` and `web_ui/web_app.py`. `web_ui/` is a **separate Next.js product surface** (has `web/reader/app/package.json`). `web_ui/` is **not imported** by any canonical production code. Therefore the `external_api/` → `web_ui/` chain is a **separate product surface**, not on the canonical reader-facing path.

### 2.5 `cli/` Entry Point vs Canonical CLI
`cli/` has a real entry point (`cli/__main__.py` → `raise SystemExit(main())`). However:
- Canonical CLI entry is `ntpe_production_translate.py` (used by `launcher_translate.py` and production)
- `cli/` is **not** imported by any canonical entry script
- Only legacy quarantined tests depend on `cli/`
- `core/enterprise/deployment_foundation.py` does an existence probe for `cli/` directory (non-functional probe)

### 2.5 Dynamic Surface Summary

| Subsystem | Dynamic Import | Source | Concrete Target |
|---|---|---|---|
| `integration/extension_loader.py` | `importlib.import_module(module_name)` | `ExtensionManifest.entrypoint` (manifest-driven) | Caller-supplied via manifest |
| All others | None | — | — |

No hardcoded dynamic imports. The only dynamic import is **manifest-driven** (extension manifest supplies the module name).

---

## 3. Classification Summary

| Subsystem | Classification | Key Evidence |
|---|---|---|
| `compatibility/` | **TEST-ONLY LEGACY** | Only quarantined `rc_stage_02` test deps; no production, no entry, no dynamic |
| `cli/` | **LEGACY** | Entry point exists (`__main__.py`), but only quarantined test deps; canonical CLI is `ntpe_production_translate.py` |
| `runtime_api/` | **LEGACY** | Used by `external_api`→`web_ui` (separate product); all tests quarantined |
| `integration/` | **LEGACY** | Manifest-driven dynamic loader; all tests quarantined |
| `workflow/` | **LEGACY** | No production, no dynamic, no entry; all tests quarantined |
| `platform_services/` | **LEGACY** | No production, no dynamic, no entry; all tests quarantined |
| `external_api/` | **LEGACY** | Used by `web_ui` (separate product); all tests quarantined |

---

## 3. Verification

```text
pytest --collect-only         : 3954 collected, 0 errors
pytest tests/contract         : 338 passed
pytest tests/reader_project   : 86 passed
pytest tests/e2e              : 55 passed
pytest tests/runtime          : 10 passed
python -m compileall core lts ui : exit 0
```

All canonical baselines preserved. No code modified.