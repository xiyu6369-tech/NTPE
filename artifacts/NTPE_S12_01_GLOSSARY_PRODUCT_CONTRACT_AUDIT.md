# NTPE S12-01 — Glossary Product Contract Audit (Current Truth)

Audit only. No production, test, schema, runtime, provider or model change.

## 0. Baseline

```text
Baseline HEAD : cf8768b67c3f525b31c6a42f2ea37ecb59a28a2c
Branch        : main
Pre-existing dirty state preserved (untouched, not staged): memory/character_memory_lts.json,
the four tests/literary/outputs/* residuals (PS-03/README.md still deleted), and the
untracked S11-01/S11-02 artifacts.
```

## 1. Current Glossary Surface

| Module | Class / function | Role | Format | Production reachability |
|---|---|---|---|---|
| `core/glossary.py` | `Glossary` | Simple file map: `load`, `prompt_block`, `apply_output_fix`, `check_required_terms` | `src=dst` lines | UNREACHABLE (no importers) |
| `lts/txt_translation_runtime.py` | `load_glossary_text`, `load_json_pairs`, `load_locked_dictionary`, `apply_locked_dictionary`, `build_translation_alias_map` | Canonical TXT glossary loader + post-processing | text `=`/`->`/`→`, JSON pairs | REACHABLE (TXT runtime) |
| `core/epub_translation/runtime/adapter.py` | `_load_locked_dictionary`, `_load_glossary_text`, `_extract_pairs`, `_apply_locked_dictionary` | EPUB duplicate loader + post-processing | same as TXT | REACHABLE (EPUB runtime) |
| `core/literary/glossary_context.py` | `GlossaryContext`, `LockedTerm` | Prompt glossary section (matched terms only) | in-memory | REACHABLE via `LiteraryPromptBuilder` (TXT only) |
| `core/literary/literary_prompt_builder.py` | `LiteraryPromptBuilder.build` | Renders `【Glossary】` block into prompt | in-memory | REACHABLE (TXT); NOT fed by EPUB adapter |
| `core/translation_resources/glossary_resource.py` | `build_glossary_resource` | Points a `TranslationResource` at `glossary.txt` | n/a | REACHABLE? no callers (only exported) |
| `core/glossary_builder.py` | `merge_glossary`, `SeriesGlossary`, `SeriesGlossaryTerm`, `save_csv`, fingerprint | Offline builder + series-scoped persistent glossary | JSON/CSV/text | `SeriesGlossary` reachable via series orchestration; builder via `tools/one_shots` |
| `core/knowledge_runtime/{loader,manager}.py` | `load_glossary_bundle`, `load_series_glossary_knowledge`, `load_series_knowledge` | Knowledge "glossary" domain for prompt | in-memory | Reachable only when populated (series) |
| `core/prompt_runtime/sections.py` | `build_glossary` | Prompt glossary section from merged runtime | in-memory | Reachable; empty unless knowledge populated |
| `core/series_orchestration/*`, `core/series_checkpoint/*` | coordinator/recovery | Series glossary lifecycle | SeriesGlossary | Separate series feature (not reader-first) |
| `core/quality/terminology_*`, `core/knowledge_validation/rules/glossary_rules.py` | QA/report | Advisory terminology consistency | in-memory | Library/advisory |
| `core/name_resolution_contract_v72/*` | resolver | Name-resolution contract | in-memory | UNREACHABLE (no importers; test-only) |
| `core/validator.py` | `Validator` | Legacy checks incl. glossary | n/a | UNREACHABLE (dead) |

## 2. Canonicical Runtime Reachability

Canonical route: `UI/CLI → TranslationRuntime → RuntimeOrchestrator → TranslationEngine → ProviderManager → NvidiaTranslationProvider → NvidiaClient`.

- `TxtTranslationOptions.glossary_path` (`lts/txt_translation_runtime.py:123`) is loaded by
  `load_locked_dictionary` (`:259`) together with `character_override.json`,
  `glossary_override.json`, `root/glossary.txt`, and the character-memory file.
- TXT injects the matched dictionary into the prompt (`build_prompt_package` →
  `LiteraryPromptBuilder().build(..., locked_dictionary=matched)`, `:1541-1543`) and
  post-processes output (`apply_locked_dictionary`, `:774,921,1069`).
- `EpubTranslationOptions.glossary_path` (`core/epub_translation/runtime/adapter.py:81`)
  is loaded by the adapter's own `_load_locked_dictionary` (`:131`) but is used **only**
  post-output (`_apply_locked_dictionary` at `:695` via `_map_canonical_result_to_chunk_result`).
  The EPUB orchestrator prompt path (`RuntimeOrchestrator.execute`) builds the prompt from
  `PromptBuilder` + `KnowledgeRuntimeManager()`, whose `source` is empty by default
  (`core/knowledge_runtime/loader.py:163-164`), so the glossary domain is empty; the
  reader's `locked_dictionary` never reaches the EPUB prompt.
- Classification:
  - TXT glossary loader/prompt/post-processing: **REACHABLE**.
  - EPUB glossary loader/post-processing: **REACHABLE (post-processing only)**.
  - EPUB glossary prompt injection: **UNREACHABLE (asymmetry)**.
  - UI glossary attachment: **UNREACHABLE** — every reader-first call site hardcodes
    `glossary_path=None` (`ui/translation_studio/pages/project_page.py:707,993,1154`,
    `ui/translation_launcher/controller.py:46,205`).
  - CLI: `--glossary` exists (`cli/parser.py:126`) and reaches TXT options; CLI `quality`
    command loads a glossary mapping (`cli/commands/quality.py:62`). CLI is a manual path.
  - Series glossary + knowledge runtime: **REACHABLE via series orchestration only**.
  - `core/glossary.py`, `core/validator.py`, `name_resolution_contract_v72`: **UNREACHABLE / TEST-ONLY / LEGACY**.

## 3. Existing Data Model

No glossary record exists in the reader Project schema. `ReaderProject`
(`core/reader_project/models.py:246-259`) contains `source`, `book`, `target`, `state`,
`execution`, `output`, schema version only. The runtime glossary is an in-memory
`dict[str,str]` (`locked_dictionary`); the only persistent glossary structure is
`SeriesGlossary` (`core/glossary_builder.py:537`), which is **series-scoped**, fail-closed
fingerprinted, and not attached to `ReaderProject` nor to `TxtTranslationOptions`/`EpubTranslationOptions`.

## 4. Existing Import

- Text: `load_glossary_text` / `_load_glossary_text` support `=` , `->` , `→`; skip blank and
  `#` lines; strip leading `- `. (duplicated between TXT and EPUB).
- JSON: `_extract_pairs` recursively extracts `str→str` from nested dicts.
- CSV: `core/glossary_builder.save_csv` **writes** CSV; there is **no CSV importer**.
- No dedicated import CLI/UI; files are read from `root/glossary.txt`,
  `root/glossary_override.json`, `root/character_override.json`, and `options.glossary_path`.

## 5. Matching Semantics (existing)

- Prompt selection: `GlossaryContext.from_locked_dictionary` matches `src in chunk_text`
  (substring, case-sensitive, no word boundary, no morphology), sorts by source length
  descending, caps at 24 terms / 18 aliases (`core/literary/glossary_context.py:39-54`).
- Post-processing: `apply_locked_dictionary` first normalizes known wrong-target aliases
  (`DEFAULT_LOCKED_TRANSLATION_ALIASES`, `lts/txt_translation_runtime.py:287-304`), then
  replaces remaining exact source terms with targets, longest-first.
- Duplicate source within a source file: later line wins (dict assignment).
- `core/glossary.py` matching is a separate legacy `text.replace` implementation.

## 6. Existing Consumers

- TXT reader-first runtime (`lts/txt_translation_runtime.py`).
- EPUB reader-first runtime (`core/epub_translation/runtime/adapter.py`), post-processing only.
- Series orchestration → KnowledgeRuntime glossary domain → prompt sections.
- Advisory QA (`core/quality/terminology_*`).
- CLI `quality` command.

## 7. Product Gaps (current truth)

```text
Product gap   : no reader-facing way to import/attach/inspect/replace/detach a glossary.
Project gap   : ReaderProject has no glossary attachment; no project-owned glossary store.
UI gap        : all reader-first glossary_path call sites are None; no control exists.
Persistence   : glossary is loaded from an absolute/external path at runtime; nothing restored on restart.
Runtime gap   : EPUB prompt does not receive the reader glossary (post-processing only).
Recovery gap  : runtime artifact identity does not include a glossary content hash.
Reproducibility: no glossary version/content identity is recorded with the project or artifact.
Parity gap    : loader code is duplicated TXT vs EPUB; prompt injection exists for TXT only.
```

## 8. Existing Locked Terminology Interaction

"Locked terminology" and "user glossary" are **already the same mechanism**: a single
merged `locked_dictionary` built by `load_locked_dictionary` with a fixed file order:

```text
character_override.json  ->  glossary_override.json  ->  root/glossary.txt
->  options.glossary_path (user glossary)  ->  character-memory file
```

Later sources override earlier (dict.update). `DEFAULT_LOCKED_TRANSLATION_ALIASES` adds
alias normalization on top. Therefore a user glossary attaches at the **existing
`glossary_path` slot** — no new precedence layer is required or justified.

Known locked examples (`정태의→鄭泰義`, `일라이→伊萊`, `리그로우→里格勞`) currently live as
seed/default content; they are an instance of the same mechanism, not a separate contract.

## 9. Character / Context Memory Interaction

Character Memory (`quality_character_memory_v72`) and Context/Scene Memory
(`quality_context_scene_v72`) are default-`False` at every options surface and share the
same `locked_dictionary` merge for character-memory terms. Glossary must not change their
defaults. Integration point only: character-memory terms and glossary terms already merge
into one dictionary; future fusion is out of S12-01 scope.

## 10. TXT / EPUB Parity

- Loader semantics: identical behaviour but **duplicated code** (TXT vs EPUB).
- Post-processing: both apply alias + source→target.
- Prompt injection: TXT yes (`LiteraryPromptBuilder`), EPUB no.
- Persistence/matching/precedence: currently unowned by any Project contract for both.

## 11. Security

- Import reads a user file: no dedicated guard beyond generic file read. Existing repo
  patterns: project-id path normalization and atomic `os.replace` (`core/reader_project/store.py`),
  source-path `expanduser().resolve()`, EPUB zip guards. A glossary import must reuse
  these, plus size cap, extension allowlist, traversal/absolute-path block, and encoding
  handling. No existing security relaxation required.

## 12. Test Coverage

- `tests/lts_stage_03/test_glossary_character_memory.py` — text delimiters, merge order,
  post-processing, dry-run metadata (`locked_dictionary` in prompt package). REAL.
- `tests/resources/translation_resource_manager_test.py`, `tests/rm5/test_glossary_pipeline*.py`,
  `tests/stage_15_3/*`, `tests/unit/test_stage15_3_terminology_consistency.py`,
  `tests/knowledge_validation/test_glossary_rules.py`, `tests/series/*` (SeriesGlossary),
  `tests/unit/test_stage1259_name_resolution_contract.py`.
- Missing coverage: no test for reader-first glossary attachment/persistence/restart; no
  EPUB prompt-vs-post glossary parity test; no conflict/duplicate import contract test; no
  glossary version in recovery identity.

## 13. Unresolved Product Decisions

1. **EPUB prompt parity** — should the reader glossary reach the EPUB prompt (like TXT), or
   is deterministic post-processing enforcement sufficient? Recommended: keep canonical
   route untouched for MVP, rely on post-processing (which guarantees target terms), and
   record prompt-injection parity as a bounded enhancement.
2. **Recovery glossary identity** — whether to add the glossary content hash to the runtime
   artifact identity. Recommended: include it (bounded, additive) for reproducibility.
3. **CSV import** — builder emits CSV but no importer exists. Recommended: defer CSV import
   to a later task; MVP = text + JSON (existing parsers).

None of these blocks the contract; each has a recommended bounded resolution in the design.
No STOP condition is triggered: scope (project-scoped), matching (reuse existing), precedence
(reconcile to existing merged dictionary), runtime (canonical, no new engine), schema
(bounded additive extension), recovery (additive hash), parity (shared semantics), and
security (existing model) are all decidable from repository evidence.

## 14. Decision

```text
Decision: IMPLEMENT (bounded)
Next task: S12-02 — Glossary Minimal Backend / Project Integration
```
