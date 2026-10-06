# NTPE S12-02 — Glossary Minimal Backend / Project Integration Report

Bounded implementation of the S12-01 glossary contract. No UI, no provider/model, no
second runtime, no schema migration.

## 0. Baseline

```text
Baseline HEAD : f011e9882bf9c9619cc34adf389191c7f75c3472
Branch        : main
Pre-existing dirty state preserved (untouched, not staged): memory/character_memory_lts.json,
the four tests/literary/outputs/* residuals (PS-03/README.md still deleted), untracked
S11-01/S11-02 artifacts.
```

## 1. GlossaryRecord

`core/reader_project/models.py` — additive, schema v1:

```text
GlossaryRecord(mode, glossary_id, content_hash, format, original_path, stored_path,
               term_count, entries, aliases, imported_at, source_hash_at_import)
ReaderProject.glossary: GlossaryRecord | None = None
```

- `mode`: `"none"` | `"project_file"`.
- `glossary_id` == `content_hash` (deterministic identity).
- `stored_path`: absolute path to the project-owned snapshot.
- `to_dict` / `from_dict` include `"glossary": null` for legacy projects.

## 2. Persistence

- `ProjectStore.glossary_dir`, `glossary_snapshot_path`, `write_glossary_snapshot`,
  `delete_glossary_snapshots` (`core/reader_project/store.py`).
- Snapshot filename is `<content_hash>.json`; `content_hash` is validated as hex so a
  record can never escape the project directory.
- Writes reuse the existing atomic mechanism (`_atomic_write_json`: temp in same dir +
  `fsync` + `os.replace`). No second atomic-write implementation.
- Attach/replace order: write new hash-named snapshot → update `project.json` atomically
  → collect old snapshots. A failure never leaves the project pointing at a partially
  written snapshot; old snapshots are removed only after new state is persisted.

## 3. Hash / Identity

`canonical_content_hash(entries, aliases)` = SHA-256 over the canonical (sorted,
`ensure_ascii=False`) JSON of the normalized merged map, truncated to 16 hex (mirrors the
`txt_sha256_16` style). Normalization = strip keys/values, drop empties. Same normalized
content → same hash; changed content → different hash. The snapshot stores only the pure
`{source: target}` map so the existing `load_json_pairs` parser reads exactly the
terminology (no metadata keys leak into the locked dictionary).

## 4. Validation

`parse_glossary_file` (`core/reader_project/glossary.py`) reuses the canonical parsers
(`load_glossary_text`, `load_json_pairs`) — no second syntax interpretation. Enforced MUST:

```text
unsupported format (.txt/.json only) · missing/not-a-file · oversized (>5 MiB)
strict UTF-8(-BOM) decode failure · empty / whitespace-only / no valid pairs
```

Malformed rows are skipped by the existing parser (documented); a file whose normalized
result is empty is rejected. No breaking validation was added beyond S12-01.

## 5. Conflict Semantics

- Within a file: last valid row wins (existing parser assignment).
- Across sources: existing `locked_dictionary` order preserved —
  `character_override.json → glossary_override.json → root/glossary.txt → project glossary
  → character memory`. No new precedence layer.

## 6. Runtime Integration

`apply_glossary_to_options(project, options)` returns canonical options
(`dataclasses.replace`, since options are frozen) with `glossary_path` set to the verified
snapshot and `glossary_hash` set when supported. Feature-off returns the options unchanged.

- TXT: `TxtTranslationOptions.glossary_hash` added (additive); `translate_txt` writes
  `resume_state["glossary_hash"]`.
- EPUB: `EpubTranslationOptions.glossary_hash` added (additive); the adapter writes
  `resume_state["glossary_hash"]`.
- Canonical route unchanged: `options.glossary_path` → existing `load_locked_dictionary` /
  `_load_locked_dictionary` → existing prompt (TXT) / post-processing (EPUB). No new
  engine, resolver, or prompt architecture.

## 7. Matching Semantics

Unchanged (reused): substring `src in text`, case-sensitive, longest-first, cap 24;
post-output alias normalization + source→target replacement. No matching redesign.

## 8. TXT Integration (verified)

`tests/integration/test_s12_02_glossary_integration.py::test_project_glossary_reaches_txt_runtime`
builds a project, attaches a glossary, binds options, runs `translate_txt(dry_run=True)`
and asserts the prompt package `knowledge.locked_dictionary` contains the project terms.
Feature-off test asserts no glossary is injected.

## 9. EPUB Integration (verified)

`test_project_glossary_reaches_epub_runtime` binds the snapshot to `EpubTranslationOptions`
and asserts the adapter's `_load_locked_dictionary` returns the terms and
`_apply_locked_dictionary` enforces them. `test_txt_epub_glossary_semantics_parity` asserts
TXT and EPUB loaders yield the same glossary entries from the same record.

## 10. Project Lifecycle

`ReaderProjectManager.attach_glossary`, `replace_glossary`, `detach_glossary`,
`glossary_option_path`, `resolve_glossary` added. `create` stays glossary-free; legacy
projects load with `glossary = None`. Detach clears the record, removes the snapshot, and
leaves unrelated state intact.

## 11. Recovery Hash

- New gate `validate_glossary_binding` inserted as recovery check #7 (before runtime
  state), `blocked_by="glossary"`.
- Active glossary must have an intact snapshot and a matching `glossary_hash` in the
  runtime artifact; otherwise recovery is blocked.
- Feature-off (no glossary, artifact without hash) → unchanged (eligible).
- Legacy artifact without hash + active glossary → blocked (no evidence of same config).
- Removed glossary while artifact recorded one → blocked.

## 12. Backward Compatibility / Feature-off

- Schema v1 unchanged; `glossary` is optional with default `None`.
- No data rewrite of existing `project.json`.
- No-glossary behavior identical: `apply_glossary_to_options` is a no-op, recovery gate
  returns eligible, TXT/EPUB loaders untouched.
- Rollback: ignore `glossary` on read.

## 13. Security

Extension allowlist, size cap, strict decode, is-file/missing checks, hex-only snapshot
filename, and reuse of the project store's path validation + atomic writes. No weakening of
existing atomicity/source identity/project ownership.

## 14. Targeted Tests

```text
tests/reader_project/test_glossary_backend.py          21 tests (A/B/C/D/I + corrupt + security)
tests/integration/test_s12_02_glossary_integration.py   5 tests (E/F/G/H + feature-off)
                                                       26 passed
```

Coverage map: A import, B identity, C project attach/load/replace/detach, D persistence
after external delete, E TXT, F EPUB, G parity, H recovery, I conflict.

## 15. Regression Results

```text
tests/reader_project                      PASS
tests/e2e S9-07 txt/epub/failure, S10-03 reader/recovery, S11-04, S11-07   PASS (per-file)
tests/integration S10-02, S11-03/06/09/10, S12-02                          PASS (31)
lts_stage_03                              89 passed, 2 pre-existing stale failures
```

## 16. Broad Regression Classification

```text
unit + contract + reader_project + lts_stage_03 : 3914 passed, 60 failed, 12 collection errors
integration (ignore launcher_*)                 : 1329 passed, 313 failed, 78 collection errors
```

- S12-02-caused: **none**.
- 60 = S11-11 baseline 58 (stale unit/contract expectations, incl. pre-existing
  `core/quality` optional-import `TypeError`) + 2 newly-in-scope `lts_stage_03` dry-run
  status failures. Both `lts_stage_03` failures assert `status=="success"` while the
  baseline HEAD already returns `"dry_run"` (`git show HEAD:lts/txt_translation_runtime.py`
  contains the same logic) — pre-existing Category E.
- Integration 313 failures unchanged; the glossary/reader-matching failed lines are legacy
  stage122x provider/prompt-policy tests, not S12-02.
- Qt e2e directory-run flaky access violation is pre-existing (S11-10 finding); each e2e
  lock file passes individually. No new e2e module was added.

## 17. Modified Files

```text
core/reader_project/glossary.py            (new)
core/reader_project/models.py              (+GlossaryRecord, +ReaderProject.glossary)
core/reader_project/store.py               (+snapshot helpers)
core/reader_project/manager.py             (+attach/replace/detach/glossary accessors)
core/reader_project/recovery.py            (+validate_glossary_binding gate)
core/epub_translation/runtime/adapter.py   (+glossary_hash option, +1 resume-state line)
lts/txt_translation_runtime.py             (+glossary_hash option, +1 resume-state line)
tests/reader_project/test_glossary_backend.py        (new)
tests/integration/test_s12_02_glossary_integration.py (new)
artifacts/NTPE_S12_02_GLOSSARY_BACKEND_INTEGRATION_REPORT.md
```

Excluded/untouched: `ui/`, `cli/`, provider, model, `engine/`, `core/context/`,
`core/glossary.py`, `core/validator.py`, `name_resolution_contract_v72`, Character/Context
Memory defaults, Literary, pre-existing residuals.

## 18. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
```

## 19. S12-02 Acceptance

GlossaryRecord bounded; project attachment persisted; project-owned snapshot; atomic
write reused; deterministic content hash; text+JSON import; CSV deferred; MUST validation
enforced; last-wins + existing precedence preserved; matching unchanged; TXT+EPUB
integrated with shared semantics; canonical runtime preserved; provider/model unchanged;
recovery glossary identity handled incl. legacy compat; detach/replace/corrupt/missing
handled; security preserved; UI/CLI/Character/Context/Literary untouched; feature-off
regression clean; diff hygiene PASS.

## 20. Commit

```text
feat(glossary): integrate project-scoped glossary backend
Push origin main · Tag: NO
```
