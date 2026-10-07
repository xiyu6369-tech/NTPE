# NTPE S13-01 — Output Portability & Stale Artifact Reconciliation Audit

Audit / decision-support only. No production, test, schema, runtime or pipeline change.

## 0. Baseline

```text
Baseline HEAD : a970133c36620ee4f9e1983f842289548628cf3a
Actual HEAD   : a970133 (audit commit appended separately)
origin/main   : a970133
Branch        : main
Working Tree Before : pre-existing dirty state only (5 tracked residuals + 4 untracked S11 artifacts)
```

`git status --short` before and after this audit is identical (see §9). No reset/clean/
force-pull/force-push/discard performed.

## 1. Scope

Reconcile the two S12-08 Output residuals (`absolute-path portability`, `stale
available`) by direct source + test inspection:

```text
ReaderProject -> translation launch -> output path construction -> output persistence
-> project/runtime artifact references -> fresh process/project reload
-> result rendering / output availability
```

## 2. Canonical output flow (evidence)

### 2.1 Path construction (runtime-owned, per format)

- EPUB: output dir is **source-adjacent and identifier-segmented** —
  `epub_output_dir(source.parent, identifier)` = `<source.parent>/output/epub_translation/<safe id>`
  (`core/epub_translation/output_layout.py:32`); artifact
  `<output_dir>/<source_stem>_zh.epub` (`ui/translation_studio/translation_worker.py:130-135`).
- TXT: output dir is **project-owned under NTPE_HOME** —
  `<NTPE_HOME>/output/<project_id>` for persisted projects
  (`ui/translation_studio/pages/project_page.py:873-889`); otherwise the legacy
  `output/<stem>` relative path for non-persisted rows.

The result dict carries the runtime's real `output` / `output_dir`
(`translation_worker.py:149-153`); the UI never guesses the path.

### 2.2 Persistence

`_persist_translation_result` (`project_page.py:1031-1060`) writes, only when a non-empty
`output` is returned:

```text
project.output.artifact_path = str(output)                  # ABSOLUTE string
project.output.output_dir    = str(result["output_dir"])    # ABSOLUTE string
project.output.artifact_kind = project.source.format
project.output.available     = Path(output).is_file()       # derived-at-persist-time
project.execution.resume_state_path = <absolute resume json>
```

persisted atomically via `ReaderProjectManager.update(...) -> store.write(...)`
(`manager.py:158-184`); `OutputRecord` is a schema-v1 dataclass
(`core/reader_project/models.py:217-242`). Confirmed by
`tests/reader_project/test_project_store.py::test_output_reference_is_persisted_not_guessed`
(absolute `artifact_path` survives reload).

### 2.3 Path categories

| Path | Category |
|---|---|
| `output.artifact_path` | ABSOLUTE persisted reference |
| `output.output_dir` | ABSOLUTE persisted reference |
| `execution.resume_state_path` | ABSOLUTE persisted reference |
| source EPUB/TXT `source.path` | ABSOLUTE persisted reference (`SourceRecord`) |
| EPUB output dir | deterministically derivable from `source.parent` + identifier (not stored as relative) |
| TXT output dir | deterministically derivable from `source.parent` or `project_id` |
| live progress / session id | runtime-local transient (not a Project reference) |

No project-relative path is stored; no CWD-relative path is used for persisted projects
(deliberate, S9-05: "Output stays Project-owned … No CWD-relative path is reintroduced").

### 2.4 Relocation behavior

- Same filesystem location: all references valid; per-project isolation holds
  (`test_s9_05_completion_output.py::test_outputs_are_never_cross_wired`,
  `test_same_filename_distinct_projects_open_their_own_output`).
- Move the source file (TXT/EPUB): persisted absolute `source.path` breaks → truthful
  source-missing handling (`project_view_model.py:61-65`).
- Relocate `NTPE_HOME`: `project.json` moves with the store, but the persisted
  `artifact_path` / `output_dir` / `resume_state_path` still point at the **old absolute
  paths** → `Path(artifact).is_file()` becomes False → truthful `結果檔案不存在` state.
  For TXT, `_txt_output_dir` reuses the persisted absolute `output.output_dir`, so a later
  run would (re)create/write the old absolute output tree rather than the new home.
- There is **no** project-identity-based relocation/recompute of output paths, and no test
  asserts relocation (searched `tests/` for relocation/re-home; none found).

### 2.5 Hidden second pipeline

**ABSENT (confirmed).**
- Single canonical packager: `pack_epub_resource_aware` +
  `build_epub_reader_chapter_map_with_metadata` + `epub_output_dir`. The
  `ui/translation_launcher/worker.py:142-167` call site reuses the **same** canonical
  functions (shell duplication of the *result-dict assembly*, not a second pipeline).
- Single reader-facing output persistence: only
  `project_page._persist_translation_result`. The launcher has **no** `ReaderProject` /
  `ReaderProjectManager` / `OutputRecord` reference (grep: none).
- Single output model: `OutputRecord` (schema v1). No second output store.

## 3. Stale `available` state — lifecycle

```text
persist:  project.output.available = Path(output).is_file()      (write-time snapshot)
derive:   artifact_available = output.available AND artifact_path AND Path(...).is_file()
          (core/reader_project/state.py:71-75)
render:   output_exists = bool(artifact) and Path(artifact).is_file()
          (ui/translation_studio/project_view_model.py:69-74)
action:   _on_open_result re-checks Path(artifact).is_file() before opening
          (project_page.py:645-654)
```

- `available` is a **persisted derived snapshot**, not authoritative truth. It is
  **always** re-gated by a live `is_file()` check at derivation, render and action time.
- Artifact deleted after completion: `derive_reader_status` requires `available AND
  is_file()` → status is demoted (typically `resumable`), `can_open_result=False`, note
  `結果檔案不存在` (`test_s9_05_completion_output.py::test_completed_missing_output_is_not_faked`).
- Artifact present but persisted `available=False` (only reachable by external tampering):
  `output_exists=True` but status not COMPLETED → no Open Result; no false "missing" note.
  A stale-negative, not a false-positive; no reader-facing corruption.
- Action-time guard: opening a deleted artifact does not call the OS opener and does not
  mutate the Project (`test_open_result_missing_does_not_call_opener_or_mutate`).

### 3.1 Boundary: UI stale display vs real output failure

- **UI stale display**: impossible for the persisted `available` flag to produce a false
  "completed/openable" card, because status and controls are recomputed from live
  `is_file()` at render.
- **Real output/usability failure**: only if the artifact genuinely does not exist at the
  referenced path (deleted, or `NTPE_HOME` relocated). In both cases the system reports a
  truthful non-completed / missing-result state — no fake control, no data corruption.
- The two are therefore correctly distinguished: there is no reader-facing inconsistency
  where "artifact absent but UI offers open", nor "artifact present but project cannot
  locate it" within the same filesystem location.

## 4. Existing evidence

- `tests/ui/test_s9_05_completion_output.py` (12 tests): completion vs availability,
  missing-output demotion, open/reveal guards, no-mutation on open, per-project isolation,
  restart persistence (`test_completion_output_survives_reload`).
- `tests/reader_project/test_project_store.py`: output reference persisted (not guessed).
- `tests/e2e/test_s9_07_txt_reader_flow.py`, `test_s9_07_failure_recovery.py`,
  `tests/e2e/test_s10_03_epub_reader_first_e2e.py`,
  `test_s10_03_epub_recovery_e2e.py`, `tests/integration/test_s11_10_*`: real restart /
  read-back of output from the persisted Project.
- Prior conclusions: `artifacts/NTPE_S9_05_COMPLETION_OUTPUT_UX_REPORT.md` §Design;
  `artifacts/NTPE_S11_11_PROGRAM_AUDIT.md` §4.5; `artifacts/NTPE_S12_08_PROGRAM_AUDIT.md` §9.

## 5. Required classification

| Item | Classification |
|---|---|
| Absolute-path portability | **DEFERRED** (by-design limitation; truthful failure; no corruption) |
| Stale `available` state | **QUALITY DEBT** (redundant persisted derived flag; fully mitigated at 3 gates) |
| Output persistence | **CLOSED** (atomic, schema v1, restart-verified) |
| Output reader-facing usability | **CLOSED** (no fake control; truthful missing state) |
| Output/project reference consistency | **CLOSED** (per-project isolation; relocation caveat deferred) |
| Existing output tests | **PASS** |
| Second output pipeline | **ABSENT (confirmed)** |

No item qualifies as `ACTIVE CORRECTNESS GAP` or `ACTIVE PRODUCT GAP` for normal
same-location operation.

## 6. Result

```text
Output portability finding : absolute references are deliberate; relocation yields a
                             truthful missing-result state, not corruption; no recompute.
Stale available finding    : persisted derived snapshot, re-gated by live is_file() at
                             derive/render/action; no false-positive UI; QUALITY DEBT only.
Persistence finding        : CLOSED (atomic schema-v1 OutputRecord; restart verified).
Restart finding            : CLOSED (S9-05/S9-07/S10-03/S11-10 evidence).
Relocation finding         : DEFERRED product decision; concrete scenario = TXT later run
                             reuses/creates the stale absolute output_dir.
```

See `artifacts/NTPE_S13_01_OUTPUT_DECISION.md` for the product decision.

## 7. Acceptance criteria

- [x] baseline = `a970133`
- [x] Output behavior verified by source + tests/evidence
- [x] absolute-path portability defined (DEFERRED)
- [x] stale `available` defined (QUALITY DEBT, mitigated)
- [x] reader-facing impact separated (UI stale vs real failure)
- [x] persistence / restart / relocation confirmed
- [x] no hidden second output pipeline
- [x] no production code modified
- [x] no tests modified
- [x] Provider / Network / Real Translation = 0 / 0 / 0
- [x] pre-existing dirty state preserved
- [x] artifacts only under `artifacts/`
- [x] no new production correctness blocker

**FINAL: PASS**
