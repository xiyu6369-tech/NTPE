# NTPE S12-01 — Glossary Integration Design (Bounded, Pre-Implementation)

Companion to `artifacts/NTPE_S12_01_GLOSSARY_PRODUCT_CONTRACT_AUDIT.md`.
Baseline `cf8768b`. Design only — no implementation, schema migration, UI, or runtime wiring.

## 1. Glossary Product Definition

A **Glossary** is a user-supplied, project-scoped list of terminology pairs:

```text
source term (Korean) -> target term (Traditional Chinese)
+ optional aliases (wrong-target variants to normalize)
```

It is **not** a full terminology-management system. It reuses the existing runtime
concept of a `locked_dictionary` (`dict[str, str]`) and the existing
`GlossaryContext`/`apply_locked_dictionary` semantics. No new matching engine, no provider,
no model change.

## 2. Scope

```text
project-scoped  : attached to one ReaderProject; copied into project-owned storage.
global default  : the existing root/glossary.txt remains a lower-precedence default.
session-only    : not supported.
```

Rationale: `ReaderProject` is the single reader source of truth; project-scoped attachment
fits the existing persistence/isolation model and requires only a bounded schema extension.

## 3. Supported Import Format(s)

Reuse existing parsers; do not invent formats.

| Format | Status | Parser |
|---|---|---|
| Text (`src=dst`, `src->dst`, `src→dst`, `#` comments, blank lines) | MVP | existing `load_glossary_text` |
| JSON (nested `str→str` pairs) | MVP | existing `_extract_pairs` |
| CSV | DEFERRED | none exists; builder only writes CSV |

Encoding: UTF-8 / UTF-8-BOM (existing `utf-8-sig` behaviour); invalid encoding ⇒ explicit
import error.

## 4. Data Model

Bounded additive extension of schema v1 (old projects load unchanged, field defaults to
`None`):

```text
ReaderProject
  + glossary: GlossaryRecord | None = None

GlossaryRecord
  mode: str = "none"            # "none" | "project_file"
  format: str                   # "text" | "json"
  original_path: str            # user-selected path (informational only)
  stored_path: str              # project-owned copy, relative to project dir
  content_hash: str             # sha256 (16-hex, mirrors txt_sha256_16 style)
  term_count: int
  imported_at: str
  source_hash_at_import: str | None   # external file hash at import time (change detection)
```

No second project model; no SQLite; the record lives in the existing `project.json`.

## 5. Identity / Version

- `content_hash` = SHA-256 over canonical `source→target` pairs (sorted), 16 hex, mirroring
  the existing `txt_sha256_16` source-identity style.
- `stored_path` = project-owned snapshot: `<project_dir>/glossary/glossary.<ext>` written
  atomically (`tmp` + `os.replace`, like `ProjectStore`).
- Version is the content hash (no separate integer); a changed file ⇒ different hash.

## 6. Project Attachment

```text
User imports file -> validate -> copy into project-owned storage -> record GlossaryRecord
-> ReaderProject.glossary set -> atomic ProjectStore write.
```

Attach / replace / detach are all project-record updates; detach sets `mode="none"` and
removes the stored snapshot. The project-owned snapshot is immutable for the duration of a
translation run.

## 7. Import Validation

MUST: non-empty source and target after trim; at least one valid pair; file readable and
decodable; extension in allowlist; size cap; path not absolute/traversal (reuse project
store normalization for the stored copy).

SHOULD: report malformed rows (skipped) with line numbers; warn on duplicate source keys;
report term count.

OPTIONAL: alias column; notes; category (these exist on `SeriesGlossaryTerm` but are not
required for a project glossary).

## 8. Conflict Semantics

- Within one import file: **last valid row wins** for a duplicate source (existing
  `dict` assignment) — documented, deterministic.
- Across sources: existing fixed merge order (see §10). No new conflict layer.

## 9. Matching Semantics

Reuse existing semantics verbatim (no redesign):

```text
match = source term appears as a substring of the chunk text (case-sensitive),
        longest source first, capped (GlossaryContext max_terms=24).
enforcement = post-output alias normalization + source→target replacement (longest-first).
```

Documented known limitation: no word-boundary/case-fold/morphological matching. This is the
current, tested TXT/EPUB behaviour and is retained for parity and determinism.

## 10. Precedence

Single merged `locked_dictionary` (no new layer), user glossary occupies the existing
`glossary_path` slot:

```text
1. character_override.json
2. glossary_override.json
3. root/glossary.txt
4. project glossary  (mapped to options.glossary_path)
5. character-memory file
```

Later overrides earlier. `DEFAULT_LOCKED_TRANSLATION_ALIASES` normalization applies on top.
"Locked terminology" and "user glossary" are the same mechanism; this reconciles them by
construction.

## 11. Runtime Integration Point

Canonical route only. A single helper maps `ReaderProject.glossary` → the existing
`options.glossary_path` (absolute project-owned stored path) immediately before building
`TxtTranslationOptions` / `EpubTranslationOptions`. No engine/provider/model/prompt-builder
change for MVP.

## 12. TXT Integration

```text
project glossary -> TxtTranslationOptions.glossary_path
-> load_locked_dictionary (existing) -> LiteraryPromptBuilder (prompt) + apply_locked_dictionary (post)
```

## 13. EPUB Integration

```text
project glossary -> EpubTranslationOptions.glossary_path
-> _load_locked_dictionary (existing) -> _apply_locked_dictionary (post-processing)
```

Post-processing deterministically enforces target terms and normalizes aliases. Prompt
injection parity with TXT is a **bounded DESIGN DECISION** recorded for the implementation
task (optional: pass matched glossary into the EPUB orchestrator prompt). MVP relies on
post-processing; if parity is required, it must be added without altering provider/model.

## 14. Persistence

`GlossaryRecord` persisted in `project.json`; glossary content copied into project-owned
storage. Restart loads `ReaderProject.glossary` and resolves `stored_path` relative to the
project directory — no dependence on the original external path.

## 15. Restart

```text
reopen project -> read GlossaryRecord -> project-owned snapshot exists? 
  yes -> attach as options.glossary_path
  no  -> surface "glossary file missing" state (do not silently translate without it)
```

## 16. Recovery

- Runtime artifact / resume identity should include `glossary.content_hash` so a recovered
  run is guaranteed to use the same terminology (additive; no removal/rename of existing
  fields).
- Recovery gates (source identity, artifact identity, project/source ownership) are
  unchanged; the glossary hash is an additional bound configuration identity.
- Because the project snapshot is immutable during a run, normal restart and recovery both
  observe the same terminology ⇒ deterministic.

## 17. UI Contract

Location: Project Page (import/edit surface), no new top-level navigation.

```text
attach glossary (file dialog: .txt/.json)   -> enabled
inspect active glossary (term count, hash)  -> read-only summary
replace glossary                            -> enabled when attached
detach glossary                             -> enabled when attached
invalid glossary                            -> explicit error (format/encoding/empty/too large)
missing stored snapshot after restart       -> "glossary missing" state
```

No enabled/disabled fake controls; no manual JSON editing or config editing required of the
user. UI implementation is deferred to a dedicated task.

## 18. Error States

`unsupported format`, `encoding failure`, `empty glossary`, `no valid pairs`,
`file too large`, `unsafe path`, `missing stored snapshot`, `external file changed`.

## 19. Security

Reuse existing model: project-id path normalization, atomic writes, `expanduser().resolve()`
for user-selected source. Add: extension allowlist (`.txt`, `.json`), size cap, traversal/
absolute-path rejection for the stored copy, decode error handling, and bounded row count.
No security relaxation.

## 20. Test Plan (design only)

Deterministic; provider/network/real-translation = 0.

```text
import: valid text / valid json / malformed rows / empty / unsupported / encoding failure / oversized
conflict: duplicate source within file (last-wins); cross-source precedence order
matching: substring match, longest-first, cap; post-output enforcement
project: attach -> persisted GlossaryRecord + project-owned snapshot; replace; detach
restart: reopen project -> same glossary hash + terms; missing snapshot -> explicit state
TXT integration: project glossary reaches prompt package + post-processing (dry-run metadata)
EPUB integration: project glossary reaches post-processing; final EPUB terms enforced
recovery: resume uses same glossary hash; changed glossary hash blocks/marks mismatch
external change: original file modified -> detected via hash, not silently applied
security: path traversal / absolute path / oversized rejected
```

## 21. Migration / Backward Compatibility

- Schema v1 stays v1; `glossary` is optional with default `None`. Existing projects load and
  behave exactly as today.
- No data rewrite of existing `project.json` files.

## 22. Rollback Strategy

- Ignore `glossary` on read (feature-off) ⇒ behaviour identical to current HEAD.
- Detach removes only the project-owned snapshot and resets the record to `mode="none"`.
- No destructive migration; no legacy code removal.

## 23. Architecture Decision Matrix

| Concern | Existing Capability | Gap | Decision |
|---|---|---|---|
| Glossary data model | `locked_dictionary`, `SeriesGlossaryTerm` | no project record | EXTEND (additive `GlossaryRecord`) |
| Import | text + JSON parsers (duplicated TXT/EPUB) | no UI/single import path; no CSV | KEEP + unify call, DEFER CSV |
| Project persistence | `ProjectStore`, atomic writes, `OutputRecord` | no glossary field | EXTEND `ReaderProject` (bounded) |
| Matching | `GlossaryContext` substring, longest-first | no morphology/word-boundary | KEEP (reuse; document limitation) |
| Precedence | single merged dict, fixed order | not documented as product contract | KEEP + document |
| Runtime integration | `options.glossary_path` slot both adapters | UI never sets it | INTEGRATE (map project → option) |
| TXT | prompt + post-processing | none for glossary | KEEP |
| EPUB | post-processing only | prompt injection asymmetry | KEEP for MVP; bounded enhancement recorded |
| Recovery | source/artifact/ownership gates | no glossary hash in identity | EXTEND (additive hash) |
| UI | Project Page | no glossary controls | NEW (separate task) |
| Security | path normalization, atomic writes | import guards | EXTEND (allowlist/size/traversal) |
| Tests | `lts_stage_03`, resources, series | no reader-first glossary tests | NEW test plan (§20) |

## 24. Explicit Non-Goals

No UI implementation, no schema migration execution, no runtime/provider/model change, no
TXT/EPUB pipeline change, no recovery-engine change, no Character/Context memory enablement,
no literary calibration coupling, no legacy archive/cleanup, no CSV import in MVP.

## 25. Stop Conditions

None triggered. Scope, matching, precedence, runtime, schema, recovery, parity and security
are all resolved from repository evidence with bounded, additive designs. The two recorded
DESIGN DECISION items (EPUB prompt parity; recovery glossary hash) have recommended bounded
resolutions and do not require a new runtime, provider, model, or a schema redesign.

## 26. Next Boundary

```text
Decision: IMPLEMENT (bounded)
S12-02 — Glossary Minimal Backend / Project Integration
(fields, import/validation, project-owned snapshot, option mapping, tests)
S12-03 — Glossary Reader-facing Import UX (attach/inspect/replace/detach)
```

Implementation order must follow this design; no code before contract acceptance.
