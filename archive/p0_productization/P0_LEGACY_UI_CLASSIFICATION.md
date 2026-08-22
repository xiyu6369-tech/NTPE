# P0 Legacy UI Classification Report

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## UI Surface Inventory

| Directory | Type | Classification | Rationale |
|-----------|------|----------------|-----------|
| `ui/translation_launcher/` | Desktop GUI (Tkinter) | **QUARANTINED** | Start Translation = disabled (shows info dialog) |
| `web_ui/` | Web UI (framework-neutral) | **LEGACY_LIFECYCLE_FACADE** | Only consumes REST API, no direct runtime calls |
| `runtime_api/` | REST API facade | **LEGACY** | In-memory job/pipeline state, no TranslationRuntime integration |

---

## Detailed Classification

### 1. ui/translation_launcher/ — Desktop GUI

**Files**:
- `app.py` — Main Tkinter application
- `controller.py` — LauncherController (validation, preview, inspect)
- `state.py` — Window model, config
- `widgets.py` — UI helpers

**Key Evidence** (`app.py:71, 140-141`):
```python
self.start_button = ttk.Button(controls, text="Start Translation", command=self._start, state="disabled")
# ...
def _start(self) -> None:
    messagebox.showinfo("NTPE Stage 1", self.window_model.start_disabled_reason)
```

**Behavior**:
- Start Translation button **permanently disabled**
- Click shows info dialog: "Start Translation is not available in NTPE Stage 1"
- Validate/Preview/Inspect work (read-only operations)
- Dry-run only (`dry_run=True` hardcoded in `_config()` line 96)

**Classification**: **QUARANTINED** — Explicitly disabled, not a product path

---

### 2. web_ui/ — Web UI (Framework-Neutral)

**Files** (13 pages + shell + models):
- `web_app.py` — Application facade
- `job_page.py` — Job list/actions
- `pipeline_page.py` — Pipeline list/actions
- `session_page.py`, `event_page.py`, `resource_page.py`, `dashboard.py`
- `rest_client.py` — REST client wrapper
- `ui_shell.py` — Routing/rendering

**Key Evidence** (`job_page.py:29-31`, `pipeline_page.py:32-34`):
```python
# Job actions
JobAction("start", "Start", "POST", "/v1/jobs/{job_id}/start"),
JobAction("resume", "Resume", "POST", "/v1/jobs/{job_id}/resume"),
# Pipeline actions
PipelineAction("start", "Start", "POST", "/v1/pipelines/{pipeline_id}/start"),
PipelineAction("resume", "Resume", "POST", "/v1/pipelines/{pipeline_id}/resume"),
```

**Architecture**:
- `WebUiApp` → `WebUiRestClient` → **External REST API** (`external_api.RestApi`)
- **No direct import** of `TranslationRuntime`, `lts`, `core.translation_runtime`
- Pure REST consumer — additive facade only

**Lifecycle Methods** (via REST):
- `Job.start()` → `POST /v1/jobs/{id}/start`
- `Job.resume()` → `POST /v1/jobs/{id}/resume`
- `Pipeline.start()` → `POST /v1/pipelines/{id}/start`
- `Pipeline.resume()` → `POST /v1/pipelines/{id}/resume`

**Do these call TranslationRuntime?**
- **NO** — They call REST endpoints
- REST endpoints (`runtime_api/job_api.py`, `runtime_api/pipeline_api.py`) manipulate **in-memory state only**
- `RuntimeJob.transition()` / `RuntimePipeline.transition()` — state machine only
- No provider calls, no translation execution

**Classification**: **LEGACY_LIFECYCLE_FACADE** — Modifies in-memory state via REST, no actual translation execution

---

### 3. runtime_api/ — REST API Facade

**Files** (20+ modules):
- `job_api.py` — Job CRUD + lifecycle
- `pipeline_api.py` — Pipeline CRUD + lifecycle
- `session_api.py`, `resource_api.py`, `event_api.py`, `middleware_api.py`
- `runtime_job.py`, `runtime_pipeline.py`, `runtime_session.py` — In-memory models

**Key Evidence** (`job_api.py:120-127`):
```python
def _handle_start(self, request, context):
    return self.transition(job_id, RuntimeJobState.STARTED, metadata=request.payload.get("metadata") or {}).to_dict()

def _handle_resume(self, request, context):
    return self.transition(job_id, RuntimeJobState.RESUMED, metadata=request.payload.get("metadata") or {}).to_dict()
```

**RuntimeJob.transition()** (`runtime_job.py`):
```python
def transition(self, state, *, metadata=None, result=None):
    return RuntimeJob(
        job_id=self.job_id,
        session_id=self.session_id,
        state=state,
        metadata={**self.metadata, **(metadata or {})},
        result=result or self.result,
        updated_at=now_iso(),
    )
```

**No TranslationRuntime integration**:
- No import of `core.translation_runtime.TranslationRuntime`
- No import of `lts.txt_translation_runtime`
- No `translate_txt()`, `translate_batch()` calls
- Pure in-memory state machine

**Classification**: **LEGACY** — Additive API layer, no production translation path

---

## Classification Summary

| Surface | Classification | Translation Execution? | Product Path? |
|---------|----------------|------------------------|---------------|
| `ui/translation_launcher/` | QUARANTINED | NO (button disabled) | NO |
| `web_ui/` | LEGACY_LIFECYCLE_FACADE | NO (REST only) | NO |
| `runtime_api/` | LEGACY | NO (in-memory state) | NO |

---

## Official Product Path

**Only official translation entry**: `launcher_translate.py` → `ntpe_production_translate.py` → `TranslationRuntime` → `lts/txt_translation_runtime`

**No UI surface currently executes translation**. All UI surfaces are read-only or lifecycle facades.