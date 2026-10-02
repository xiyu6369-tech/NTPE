# NTPE S9-01 — Project Persistence Audit & Design

**Task**: `NTPE-S9-01`
**Date**: 2026-10-01
**Executor**: Kilo (Automated)
**Status**: `S9_01_AUDIT_AND_DESIGN_COMPLETE`
**Scope**: Audit + design only. No production code modified. No commit / push / tag.

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline / Actual HEAD | `53138c6` (`chore(repo): preserve final cleanup closure evidence`) |
| Branch | `main` |
| Git Commit / Push / Tag | NO |
| Production code modified in S9-01 | NO |

### 1.1 Pre-existing worktree state (not created by S9-01)

The working tree carries the **uncommitted S8-01 → S8-06 deliverables** plus legacy drift:

```
 M core/epub_translation/runtime/adapter.py
 M core/launcher_product/model_catalog.py
 M lts/txt_translation_runtime.py
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md          <-- literary residual currently DELETED
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
 M tests/ui/test_translation_launch*.py
 M ui/translation_launcher/{app,state,worker}.py
 M ui/translation_studio/{main_window.py,pages/home_page.py,pages/project_page.py,resources/translations.py,translation_worker.py}
 ?? artifacts/NTPE_S8_0{1..6}_*.md
 ?? tests/ui/test_epub_translation_launch.py
 ?? tests/ui/test_s8_0{2,3,4}_*.py
```

**Finding (pre-existing, not caused by S9-01):** `tests/literary/outputs/PS-03/README.md` is
deleted from the worktree. S9 governance (§22) requires the four literary residuals to be
preserved. S9-01 records this anomaly and does **not** restore, rewrite, or commit it without
owner approval. The other three residuals still exist on disk.

**Conclusion:** the S9 baseline is HEAD `53138c6` + uncommitted S8 UI work. Any S9
implementation must first freeze/reconcile this worktree state (separate governance step),
otherwise S9 changes will be commingled with S8 deliverables.

---

## 2. Audit — Existing State

### 2.1 Project state

| Surface | Location | Nature | Persistence | Source identity | Checkpoint link |
|---------|----------|--------|-------------|-----------------|-----------------|
| Studio UI | `ui/translation_studio/pages/project_page.py:169` `self._projects` | in-memory `list[dict]` | **none** | none (only `source` string) | none |
| Studio "New/Open Project" | `project_page.py:266,448` / `home_page.py:77,387` | explicitly disabled, no-op | none | — | — |
| CLI project package | `cli/commands/project_model.py:9,17` | directory + `ntpe_project.json` (v `1.0-beta-stage-06.2`) | yes (repo-relative) | none | none |
| Engine pipeline project | `engine/pipeline/project_manager.py:9` | profile + normalized files | partial | none | none |
| Book profile | `core/project_profile.py` | JSON profile validation | yes | none | none |

**Finding P1:** there is **no** persistent, source-identity-aware, checkpoint-linked
reader Project entity. The UI "projects" evaporate on app close. The CLI project package is a
directory scaffold, unrelated to the Studio and to runtime checkpoints.

### 2.2 Session state

| Surface | Location | Storage | Lifetime |
|---------|----------|---------|----------|
| Session checkpoint | `core/translation_session/session_checkpoint.py:23` | `<root>/.ntpe_sessions/<session_id>/session_checkpoint.json` | file-backed |
| Runtime session | `core/runtime_session` (via `RuntimeOrchestrator`) | in-memory session manager | job lifetime |
| Session API | `runtime_api/session_api.py`, `core/translation_session` | manager | job lifetime |

**Finding S1:** runtime `session_id` is created fresh per translation run
(`lts/txt_translation_runtime.py:702`, `core/epub_translation/runtime/adapter.py:328`) and is
**not** a stable resume handle. It must never be used as the Project identity.

### 2.3 Checkpoint / resume state

| Substrate | Location | Key/format | Used by |
|-----------|----------|-----------|---------|
| TXT resume state | `lts/txt_translation_runtime.py:349` `get_resume_state_path` → `<out>/<stem>_resume_state.json` | `{version, chunks:{chunk_key:{status,source_hash,output_path,updated_at}}, events}` | **TXT runtime (authoritative resume)** |
| EPUB resume state | `core/epub_translation/runtime/adapter.py:314` → `<out>/<stem>_epub_resume_state.json` | `chunks:{ "chapter_id:seq": {status,source_hash,...} }` | **EPUB runtime (authoritative resume)** |
| Runtime recovery checkpoints | `core/translation_runtime/runtime_recovery.py:12` | `.ntpe_runtime_checkpoints/<scope>_<name>_<hash>.json` | `TranslationRuntime.checkpoint*`, `recovery_summary()` |
| Production checkpoint store | `core/production_runtime/checkpoint.py:42` | `.ntpe_runtime_checkpoints/<session>.json` | beta runtime |
| Workflow checkpoint | `workflow/checkpoint_manager.py` | in-memory only | workflow tests |
| Canary checkpoint | `core/controlled_multi_chunk_translation_canary/checkpoint.py` | canary | canary only |

**Finding C1 (critical):** **actual** TXT/EPUB resume does **not** use
`core/translation_runtime/runtime_recovery.py`. It uses per-output-directory
`*_resume_state.json` files. The `RuntimeCheckpointKey`/`RuntimeCheckpointStore` layer is a
parallel, largely unused-by-production resume surface.

**Finding C2 (idempotency):** resume entries carry `source_hash` (sha256[:16] of the
chunk/segment). A cached chunk is reused only when `status ∈ {success, pass_with_warning}`
**and** `source_hash` matches **and** the chunk output file exists and is non-empty
(`lts/txt_translation_runtime.py:754-760`, `core/epub_translation/runtime/adapter.py:397-406`).
Idempotency on restart is therefore already present at the runtime level.

**Finding C3 (atomicity gap):** `save_json` / `save_text`
(`core/translation_engine/utils.py:17,24`) perform a direct non-atomic `Path.write_text`.
A crash mid-write can leave a truncated `*_resume_state.json`. The runtime route is frozen
(production route immutable), so S9 must **not** modify it; atomicity must be provided by the
S9 Project writer for **Project** state, and corruption of runtime resume files must be
**detected** (treated as `unrecoverable` / re-derivable), not silently trusted.

**Finding C4 (consistency):** resume files store the source identity only at segment
granularity (`source_hash`). There is no book-level source identity embedded in
`*_resume_state.json`, so a *whole-book* source swap is not detectable from the resume file
alone. Source-level consistency must come from the S9 Project record.

### 2.4 Output state

| Format | Final artifact | Aux files | Location owner |
|--------|----------------|-----------|----------------|
| TXT | `<output_dir>/<stem>_zh.txt` (`lts/txt_translation_runtime.py:1065`) | `<stem>_chunk_%06d_zh.txt`, `<stem>_resume_state.json`, `<stem>_live_progress.json` | `options.output_dir` (UI uses `Path("output")/<stem>`, **repo/CWD-relative**) `project_page.py:483` |
| EPUB | `<src.parent>/output/epub_translation/<identifier>/<stem>_zh.epub` (`translation_worker.py:125-135`) | `<stem>_epub_resume_state.json`, `<stem>_live_progress.json` | canonical EPUB runtime, **source-adjacent** |

**Finding O1:** the UI's TXT output path is CWD-relative (`Path("output") / stem`), so it
depends on where the app was launched. This violates §19 ("must not assume the user runs NTPE
from the repository root"). S9 must resolve output to an absolute, stable location — but
without changing the frozen runtime, i.e. by passing an **absolute** `output_dir` from the
Project layer.

**Finding O2:** the final artifact path is only known from the runtime result
(`result["output"]`). The UI must persist the runtime-returned artifact path, never guess it
(§14).

### 2.5 Source identity

| Provider | Location | Fields |
|----------|----------|--------|
| TXT | `core/adapters/canonical_book_intake_adapter.py:29` `SourceIdentity` | `source_path, source_hash(sha256[:16]), file_size, modified_time` |
| EPUB | `core/adapters/epub_extraction_boundary.py:73` `EpubExtractionResult` | `original_hash(sha256 full), extracted_hash, metadata.identifier` |

**Finding I1:** a canonical source identity already exists for both formats and must be
reused verbatim (§5, §18). `SourceIdentity` is produced by
`CanonicalBookIntakeAdapter.process_path` (TXT) and by `EpubExtractionBoundary.extract`
(EPUB). No new hashing scheme is required.

### 2.6 Reader-facing state exposure today

`project_page.py` writes raw runtime strings directly into the table
(`_on_translation_finished` lines 710-812): `Session ID：{session_id}`, `成功區塊：…`,
`chunk_total`, `Runtime…` error text. `home_page.py` statuses are `已匯入` / `部分匯入`.
There is no reader-facing enum and no mapping layer (§8, §10, §15).

---

## 3. Gap Analysis vs S9 Requirements

| S9 req | Requirement | Current | Gap |
|--------|-------------|---------|-----|
| §3 Project model | persistent unit w/ identity, metadata, state, progress, refs | none | **build** |
| §4 persistence boundary | Project separate from runtime, linked | none | **build link** |
| §5 source identity | detect source change, no silent reuse | identity exists; no project record | **build** |
| §6 checkpoint contract | idempotent/atomic/consistent/recoverable | idempotent yes; atomic no; book-consistency no | **Project-layer** |
| §7 schema versioning | `project_schema_version`, migrate/unsupported | none | **build** |
| §8 reader state model | 8 reader states, no raw tech | none | **build mapper** |
| §9 library UI | cards, resume/preview/open/folder | table with raw status | **build** |
| §10 hidden internals | hide provider/model/chunk/key/session | leaks session/chunk | **build** |
| §11 lifecycle | create..delete (confirmed) | none | **build** |
| §12 TXT/EPUB shared model | one model | none | **build** |
| §13 resume UX | first-class, real resume | button only, no persistence | **build** |
| §14 completion UX | open artifact/folder from runtime ref | message box only | **build** |
| §15 recovery UX | reader-language recovery | raw errors | **build mapper** |
| §18 backward compat | integrate, not replace | — | **constrain** |
| §19 storage | OS-appropriate, restart-findable | CWD-relative | **decide+build** |
| §20 security | normalize paths, no exec/untrusted load | partial | **constrain** |

---

## 4. Project Persistence Contract (Design)

### 4.1 Storage location (§19)

**Decision:** a per-user NTPE data root, resolved by a new pure helper:

```text
NTPE_HOME (env override, absolute)  ->  used verbatim
Windows  local app data            ->  %LOCALAPPDATA%\NTPE
macOS / Linux                      ->  ~/.local/share/NTPE (XDG_DATA_HOME honored)
fallback                           ->  ~/.ntpe
```

Per-project layout:

```text
<NTPE_HOME>/projects/<project_id>/
    project.json          # schema-versioned reader Project record (source of truth)
```

Rationale: not in repo, not CWD-dependent, backup-friendly (one folder), restart-findable,
future-migration-friendly. `NTPE_HOME` makes tests hermetic (tmp dir) and keeps
provider/network/real-translation at zero.

**Non-decision (must not do):** do **not** copy runtime artifacts into the project folder.
Output and resume files remain owned by the frozen runtime; the Project stores **absolute
references** to them.

### 4.2 Project schema v1 (`project.json`)

```jsonc
{
  "project_schema_version": 1,
  "project_id": "<uuid4 hex>",
  "created_at": "<iso8601>",
  "updated_at": "<iso8601>",
  "last_activity_at": "<iso8601>",

  "source": {
    "path": "<absolute normalized path>",     // pathlib.Path.resolve()
    "format": "txt | epub",
    "identity_kind": "txt_sha256_16 | epub_sha256",
    "hash": "<canonical hash>",
    "file_size": 123456,
    "modified_time": 1690000000.0,
    "title": "<display title>",
    "language": "ko",
    "encoding": "utf-8 | null"
  },

  "target": {
    "target_language": "zh-TW",
    "quality_profile": "literary"
  },

  "book": {
    "format": "txt | epub",
    "title": "<display>",
    "author": null,
    "identifier": null,          // EPUB dc:identifier
    "chapter_count": null,       // EPUB
    "total_units": 120           // chunks; progress denominator
  },

  "state": {
    "reader_status": "<reader_enum>",   // derived, never raw runtime status
    "completed_units": 47,
    "total_units": 120,
    "current_unit": 48,
    "last_error": null
  },

  "execution": {
    "pipeline_mode": "runtime | epub",
    "session_id": null,                 // LAST session (diagnostic only)
    "resume_state_path": "<abs>|null",  // runtime-authored resume file
    "checkpoint_ref": null              // {"scope","name"} when runtime_recovery used
  },

  "output": {
    "output_dir": "<abs>|null",
    "artifact_path": "<abs>|null",       // runtime-returned, never guessed
    "artifact_kind": "txt | epub | null",
    "available": false
  }
}
```

### 4.3 Reader-facing state model (§8) and derivation

```text
not_started  未開始          no resume_state, no artifact
translating  翻譯中          runtime running (live flag / in-process)
resumable    可繼續          resume_state present, 0 < completed < total, source OK
completed    已完成          artifact exists AND artifact matches success
incomplete   翻譯不完整       artifact exists but failed/failed-chunks > 0
failed       翻譯失敗          last run failed, no usable artifact
source_changed 來源已變更     current source identity != stored identity
unrecoverable 專案無法恢復    resume_state corrupt/unreadable, or refs missing
```

Derivation inputs are only: stored Project record, presence + parseability of the runtime
`*_resume_state.json`, presence of the artifact, and a fresh source-identity comparison.
Runtime internal statuses are translated, never displayed.

### 4.4 Source identity contract (§5)

1. On `create`, store canonical identity from `SourceIdentity` (TXT) or
   `EpubExtractionResult.original_hash` (EPUB).
2. On `load`/`validate`, cheap-check `file_size` + `modified_time`; if either differs,
   recompute the canonical hash. If the hash differs → `source_changed`.
3. Never silently apply an old checkpoint to a changed source. UI shows `來源檔案已變更`
   with a `查看` action; resume is blocked until the user confirms a new project.

### 4.5 Checkpoint contract mapping (§6)

| Property | Mechanism | Owner |
|----------|-----------|-------|
| Idempotency | runtime `source_hash` + `status` + output-exists reuse | runtime (existing) |
| Atomicity | S9 Project writer uses temp-file + `os.replace` for `project.json`; runtime resume atomicity is a **known frozen gap**, detected not fixed | S9 for Project only |
| Consistency | Project stores book-level source identity; resume entries checked against it | S9 derives, runtime enforces per-segment |
| Recoverability | derive `reader_status` from record + resume file + artifact; corrupt → `unrecoverable` | S9 |

**Explicit prohibition:** no second checkpoint/translation engine. S9 reads and references the
existing `*_resume_state.json`; it never rewrites chunk state and never invents chunk keys.

### 4.6 Project lifecycle (§11)

```text
create(source, intake_meta) -> Project            # uuid + identity + schema
load(project_id|path) -> Project                  # validate schema_version
save(project) -> path                             # atomic write
update(project, **fields) -> Project              # touch updated_at
list_projects() -> [Project]                      # scan NTPE_HOME/projects/*
resume(project) -> runtime options                # validate source+project, then launch
complete(project, artifact) -> Project            # persist runtime artifact path
fail(project, error) -> Project                    # reader-safe last_error
recover(project) -> Project                       # re-derive reader_status
delete(project_id, confirm=True) -> bool          # explicit + confirmed
```

`delete` requires an explicit confirmation value; it removes exactly one project directory and
never touches sources, outputs, other projects, or runtime checkpoints. Startup/load **never**
auto-deletes.

### 4.7 Schema versioning (§7)

- `project_schema_version` is required and validated on load.
- `== current` → load.
- `< current` → migrate via an ordered migration table, or refuse as `unsupported`.
- `> current` → refuse with `project cannot be restored (newer schema)`.
- Missing/invalid → `unrecoverable`; never crash the library.

### 4.8 TXT/EPUB shared model (§12)

One `Project` dataclass and one `project.json` schema. Format differences are confined to:

| Concern | TXT | EPUB |
|---------|-----|------|
| identity | `txt_sha256_16` | `epub_sha256` (+ identifier) |
| progress unit | chunk | chunk (`chapter_id:seq`) |
| output kind | `.txt` | `.epub` |
| preview | plain text | chapter map |
| pipeline_mode | `runtime` | `epub` |

No divergent persistence architecture.

### 4.9 Security / integrity (§20)

- All paths normalized with `Path.resolve()` before store/compare.
- Project load reads **only** JSON via `json.loads`; never `eval`, never import, never execute
  anything from the project or source path.
- Untrusted `project.json` is schema-validated; unknown fields ignored, invalid fields →
  `unrecoverable` (project downgraded, library still loads).
- Partial writes prevented by atomic replace for Project state.
- A missing source is reported, never auto-relinked by name.

---

## 5. Reader-First UI Design (S9-03..S9-06 outline)

- `我的小說` library: one card per Project (title, `EPUB · 韓 → 繁中`, `已完成 47/120 章`,
  progress bar, reader status, last activity, primary action).
- Actions by status: `繼續翻譯` / `預覽`; `開啟成品` / `開啟資料夾`; `查看問題`;
  `來源檔案已變更` + `查看`.
- Hidden by default: provider, model technical ID, chunk size, checkpoint key, session ID,
  retry counters, runtime architecture (§10).
- Auto-restore: `MainWindow` loads `list_projects()` on startup; import creates a Project
  instead of an in-memory row.

---

## 6. Task Sequence & Explicit Path Allowlists (§16, governance §22)

> Governance constraint: each task defines an **explicit path allowlist**; no file is chosen
> merely because it is modified. All tasks: Provider = 0, Network = 0, Real Translation = 0;
> no unapproved commit/push/tag.

### S9-02 — Persistent Book Project (create/load/save/update)
Allowlist:
```
core/reader_project/__init__.py
core/reader_project/models.py          # Project dataclass + schema v1 + reader enum
core/reader_project/identity.py        # source identity adapter (reuse existing hashes)
core/reader_project/store.py           # NTPE_HOME resolution + atomic JSON store
core/reader_project/manager.py         # create/load/save/update/list/delete
tests/reader_project/test_project_store.py
tests/reader_project/test_project_identity.py
```
No runtime, no UI, no EPUB packaging changes.

### S9-03 — Resume / Interrupted State UX
Allowlist:
```
core/reader_project/state.py           # derive reader_status from resume_state + artifact
core/reader_project/manager.py         # resume()/recover() (additive)
ui/translation_studio/pages/project_page.py
ui/translation_studio/resources/translations.py
tests/reader_project/test_resume_state.py
tests/ui/test_s9_03_resume_ux.py
```
Resume must call the existing runtime resume path (pass absolute `output_dir`), never create a
fresh translation job.

### S9-04 — Reader Progress Dashboard
Allowlist:
```
ui/translation_studio/pages/project_page.py
ui/translation_studio/main_window.py
ui/translation_studio/resources/translations.py
tests/ui/test_s9_04_reader_dashboard.py
```

### S9-05 — Completion & Output UX
Allowlist:
```
core/reader_project/manager.py         # complete() persists runtime artifact path
ui/translation_studio/pages/project_page.py
ui/translation_studio/resources/translations.py
tests/ui/test_s9_05_completion_ux.py
```

### S9-06 — Recovery & Source Integrity
Allowlist:
```
core/reader_project/state.py
core/reader_project/manager.py
core/reader_project/migrations.py      # schema migration/unsupported handling
ui/translation_studio/pages/project_page.py
tests/reader_project/test_recovery_source_integrity.py
```

### S9-07 — Reader-First E2E Acceptance
Allowlist:
```
tests/acceptance/test_s9_reader_first_e2e_txt.py
tests/acceptance/test_s9_reader_first_e2e_epub.py
tests/acceptance/fixtures/            # fake runtime / deterministic checkpoint fixtures
artifacts/NTPE_S9_07_READER_FIRST_E2E_ACCEPTANCE_REPORT.md
```

**Frozen (must not modify):** `lts/txt_translation_runtime.py`,
`core/epub_translation/**`, `core/translation_runtime/**`,
`core/runtime_orchestrator/**`, `core/translation_engine/**`, `core/adapters/**`
(read-only reuse), and the four literary residuals.

**Note:** `ui/translation_studio/**` is currently dirty from S8. S9 UI tasks must build on
the S8 worktree state; the S8 worktree should be committed/frozen before S9 UI edits to keep
scopes atomic.

---

## 7. Validation Boundary (§17)

- Automated tests: Provider = 0, Network = 0, Real Translation = 0.
- S9-07 uses a **fake runtime / deterministic checkpoint fixtures** in `NTPE_HOME` tmp dirs.
- No NVIDIA call is made to validate persistence.
- A separate production smoke test (real provider resume) is out of scope for S9 automated
  acceptance.

---

## 8. Backward Compatibility (§18)

- Existing TXT/EPUB runtime, resume state, checkpoint, and output are unchanged.
- S9 adds a Project layer that **references** them.
- S9 passes an absolute `output_dir` to the existing TXT runtime; EPUB output stays
  source-adjacent and is referenced, not relocated.
- No runtime file is rewritten by S9.

---

## 9. Risks & Open Decisions

| # | Item | Status |
|---|------|--------|
| R1 | S8 UI worktree is uncommitted; S9 UI scope may commingle with it | needs owner freeze/commit decision before S9 UI |
| R2 | `PS-03/README.md` literary residual deleted in worktree | needs owner confirmation; S9-01 does not touch it |
| R3 | Runtime resume writes are non-atomic (frozen route) | S9 detects corruption → `unrecoverable`; no fix |
| R4 | TXT UI output is CWD-relative today | S9 passes absolute `output_dir` from Project |
| R5 | `NTPE_HOME` location choice | proposed `%LOCALAPPDATA%\NTPE` / `~/.local/share/NTPE` |
| R6 | Schema migration framework scope | minimal ordered migration table in S9-06 |

---

## 10. S9-01 Conclusion

- The runtime already provides **idempotent, source-hash-guarded resume** for TXT and EPUB.
- What is missing is exactly the **reader-facing persistent Project**: identity, schema
  version, reader state model, lifecycle, storage location, and UI.
- S9 will **integrate** the existing canonical runtime/checkpoint/output, add a
  `core/reader_project` persistence layer and reader-first UI, and must not build a second
  checkpoint engine or rewrite any frozen runtime.

**Status:** `S9_01_AUDIT_AND_DESIGN_COMPLETE` — ready for S9-02 (no code written in S9-01).
