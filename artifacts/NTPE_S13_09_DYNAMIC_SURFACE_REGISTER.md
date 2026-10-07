# NTPE S13-09 — Dynamic Surface Register (Batch A)

Companion to `artifacts/NTPE_S13_09_LEGACY_FRAMEWORK_BATCH_A_AUDIT.md`. Baseline HEAD `1dd6bf3`.

## 1. Dynamic Import Inventory

| Subsystem | File | Line | Pattern | Source of Module Name | Concrete Targets | Reachability |
|---|---|---|---|---|---|---|
| `integration/` | `extension_loader.py` | 4 | `importlib.import_module(module_name)` | `ExtensionManifest.entrypoint` (format `module:attribute`) | **Manifest-driven** — caller supplies `module:attribute` in extension manifest | **Manifest-driven only** — no hardcoded targets. Concrete module loaded only when extension manifest is processed. |

**No other dynamic imports** (`importlib.import_module`, `__import__`, `importlib.util.module_from_spec`, `pkgutil`, `__import__`) found in any of the seven subsystems.

## 2. Subprocess / Shell / File Invocation Inventory

| Subsystem | File | Pattern | Command/Target | Reachability |
|---|---|---|---|---|
| *(none)* | — | `subprocess.run`, `subprocess.Popen`, `os.system`, `os.popen` | — | **None** |

No `subprocess.run`, `subprocess.Popen`, `os.system`, `os.popen`, `subprocess.call` found in any of the seven subsystems.

## 3. Entry Point Inventory

| Subsystem | Entry Point Type | File | Description | Active? |
|---|---|---|---|---|
| `cli/` | `__main__.py` | `cli/__main__.py:1-3` | `from .main import main; raise SystemExit(main())` | **Exists but legacy** — only legacy quarantined tests depend on it |
| `cli/` | `if __name__ == "__main__"` | `cli/main.py:159` | `if __name__ == "__main__": raise SystemExit(main())` | **Exists but legacy** |
| All others | — | — | — | **None** |

**Canonical entry points** (unrelated to these seven subsystems):
- `ntpe_production_translate.py` — canonical production CLI
- `launcher_translate.py` — thin wrapper → `ntpe_production_translate.main`
- `ntpe_translation_studio.py` → `ui.translation_studio.app.run`
- `ntpe_literary_regression.py`, `ntpe_literary_evaluation.py` — tooling helpers

## 4. Subprocess / Shell / File-Based Invocation

| Subsystem | Invocation Type | Target | Reachability |
|---|---|---|---|
| *(none)* | `subprocess.run` / `Popen` / `os.system` | — | **None** |

No `subprocess.run`, `subprocess.Popen`, `os.system`, `os.popen`, `subprocess.call` found in any of the seven subsystems.

## 5. Dynamic Surface by Subsystem

### `compatibility/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Entry points**: None
- **Public API**: `__init__.py` exports `CompatibilityAuditRegistry`, `CompatibilityAuditRunner`, `build_compatibility_audit_manifest`, `load_compatibility_audit_manifest`, `build_compatibility_audit_reports`, `CompatibilityTarget`, `CompatibilityFinding`, `CompatibilityAuditResult`
- **Dynamic surface status**: **Static public API only** — no dynamic loading mechanism

### `cli/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Entry points**: `cli/__main__.py` (→ `main()`), `cli/main.py:159` (`if __name__ == "__main__"`)
- **Public API**: `__init__.py` exports `CLIContext`, `CLIResult`, `CLICommand`, `CommandRegistry`, `build_cli_manifest`, `attach_cli_manifest`, `main`, `run_cli`
- **Internal dynamic**: `cli/freeze/compatibility.py` imports from `cli.main` (static)

### `runtime_api/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Entry points**: None
- **Public API**: Extensive — `RuntimeApi`, `RuntimeSession`, `RuntimeJob`, `RuntimePipeline`, `RuntimeEvent`, `RuntimeResource`, `RuntimeMiddleware`, freeze validators, etc. (50+ exports)
- **Consumed by**: `external_api/` (which is used by `web_ui/` — separate product)

### `integration/`
- **Dynamic imports**: `integration/extension_loader.py:4` → `from importlib import import_module`
  - `ExtensionLoader.load_from_manifest(manifest)` → `module = import_module(module_name)` where `module_name` from `ExtensionManifest.entrypoint` (`module:attribute`)
  - **Manifest-driven** — concrete module names supplied by extension manifests at runtime
- **Public API**: Extensive — `IntegrationCore`, `IntegrationRegistry`, `EventBus`, `ServiceContainer`, `ExtensionLoader`, `ExtensionLoader`, `PluginIntegrationManager`, `BridgeManager`, `ExtensionManager`, freeze validators, etc.
- **Dynamic surface**: **Manifest-driven extension loader** — concrete module names come from extension manifests (caller-supplied), not hardcoded

### `workflow/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Public API**: Extensive — `WorkflowCore`, `WorkflowEngine`, `JobScheduler`, `PipelineOrchestrator`, `TaskQueue`, `WorkerRuntime`, `WorkflowPersistence`, freeze validators, etc.

### `platform_services/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Public API**: Extensive — `PlatformServiceRegistry`, `PlatformServiceManager`, `PlatformServiceHost`, `ServiceDiscovery`, `PlatformConfig`, `HealthMonitor`, `EventBus`, `EventBridge`, `LifecycleHooks`, `PolicyEngine`, `PolicyRegistry`, freeze validators, etc.

### `external_api/`
- **Dynamic imports**: None
- **Subprocess**: None
- **Public API**: Extensive — `RestApi`, `create_rest_api`, `RestSessionApi`, `RestJobApi`, `RestPipelineApi`, `RestEventApi`, `RestResourceApi`, `RestAuthContext`, `RestMiddlewareChain`, freeze validators, etc.
- **Consumed by**: `web_ui/rest_client.py`, `web_ui/web_app.py` (separate Next.js product surface)

## 3. Dynamic Surface Reachability Summary

| Dynamic Mechanism | Subsystem | Concrete Target | Reachable from Canonical? |
|---|---|---|---|
| Manifest-driven `import_module` | `integration/extension_loader.py` | Manifest-supplied | **No** — extension manifests not loaded by canonical path |
| `cli/` entry point | `cli/__main__.py` | `cli.main.main()` | **No** — canonical CLI is `ntpe_production_translate.py` |
| `external_api/` → `web_ui/` | Import chain | `web_ui/` (Next.js product) | **No** — `web_ui/` not on canonical path |

**No dynamic surface from any of the seven subsystems reaches the canonical production path.**

## 4. Subprocess / Shell Inventory

| Subsystem | `subprocess.run` | `subprocess.Popen` | `os.system` | `os.popen` | `subprocess.call` |
|---|---|---|---|---|---|
| `compatibility/` | 0 | 0 | 0 | 0 | 0 |
| `cli/` | 0 | 0 | 0 | 0 | 0 |
| `runtime_api/` | 0 | 0 | 0 | 0 | 0 |
| `integration/` | 0 | 0 | 0 | 0 | 0 |
| `workflow/` | 0 | 0 | 0 | 0 | 0 |
| `platform_services/` | 0 | 0 | 0 | 0 | 0 |
| `external_api/` | 0 | 0 | 0 | 0 | 0 |

**Total: 0 subprocess/shell invocations across all seven subsystems.**

## 5. Entry Point Classification

| Entry Point | Subsystem | Type | Active on Canonical Path? |
|---|---|---|---|
| `ntpe_production_translate.py` | Root | Canonical CLI | **Yes** |
| `launcher_translate.py` | Root | Wrapper → canonical | **Yes** |
| `ntpe_translation_studio.py` | Root | GUI launcher | **Yes** |
| `ntpe_literary_regression.py` | Root | Tooling | **Yes** (imported by canonical) |
| `ntpe_literary_evaluation.py` | Root | Tooling | **Yes** (imported by canonical) |
| `cli/__main__.py` | `cli/` | `raise SystemExit(main())` | **No** — legacy |
| `cli/main.py:159` | `cli/` | `if __name__ == "__main__"` | **No** — legacy |
| All others | — | — | — |

**Conclusion**: No legacy entry point from these seven subsystems reaches the canonical reader-facing path.

## 6. Dynamic Surface Summary

| Mechanism | Count | Subsystems | Canonical Reachability |
|---|---|---|---|
| `importlib.import_module` (manifest-driven) | 1 | `integration/` | No — manifest not loaded by canonical path |
| `subprocess`/`Popen`/`os.system` | 0 | — | — |
| Console scripts / module `-m` | 0 | — | — |
| Entry points (`__main__`, `if __name__`) | 1 | `cli/` | No — legacy |
| File-based invocation | 0 | — | — |

**Overall**: The dynamic surface of these seven subsystems is **minimal and isolated**. The only dynamic import is manifest-driven (extension loader), and it is not triggered by any canonical production path. The only executable entry point (`cli/`) is legacy and not on the canonical path.