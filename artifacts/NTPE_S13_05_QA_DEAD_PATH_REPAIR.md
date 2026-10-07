# NTPE S13-05 — Bounded QA Dead-Path Consolidation (Repair Report)

Implementation of the S13-04 Decision A boundary: remove only zero-caller QA dead code
and unused imports. No QA unification, no legacy archive, no semantics change.

## 0. Baseline / actual

```text
Baseline HEAD : c35abb7682c34a341e96d0bfb6d1a94768670070
Baseline branch: main
origin/main   : c35abb7
Actual HEAD   : S13-05 cleanup commit (this commit; see final report / git log)
```

Pre-existing dirty state preserved (identical before/after). No reset / clean / restore /
force-pull / force-push performed.

## 1. Removed symbols

| Symbol | File | Pre-removal callers | Post-removal callers | Evidence |
|---|---|---|---|---|
| `should_soft_fail_naturalness` | `core/translation_runtime/runtime_qa.py` | only `soft_fail_naturalness_report` (also removed); no production/test caller | 0 | `git grep` empty; not in any `__all__` |
| `soft_fail_naturalness_report` | `core/translation_runtime/runtime_qa.py` | unused import in `lts/txt_translation_runtime.py:32` (removed); historical archived test `archive/stage_tests/ntpe_te_v30_stage022_runtime_speed_policy_test.py` | 0 | no tracked production/test importer |
| `has_retry_worthy_naturalness_issue` | `lts/txt_translation_runtime.py` | no production/test caller; historical archived test only | 0 | `git grep` empty |
| `qa_retry_delay_seconds` | `lts/txt_translation_runtime.py` | none | 0 | `git grep` empty |
| `NATURALNESS_GUARD_CODE` (constant) | `core/translation_runtime/runtime_qa.py` | sourced solely from the two removed functions | 0 | only owners were the removed functions (residue) |
| `Validator` + `ValidationResult` | `core/validator.py` (whole file) | 0 | 0 | see §3 |

The runtime `"NATURALNESS_GUARD"` **issue code** (string literal) is unchanged and still
emitted by `analyze_runtime_quality` (`runtime_qa.py:201-202`); only the dead helper
constant was removed.

## 2. Removed imports

| Import | File | Pre-removal | Post-removal |
|---|---|---|---|
| `soft_fail_naturalness_report` | `lts/txt_translation_runtime.py:32` | imported, never referenced | removed |
| `RuntimeQAPolicy, analyze_runtime_quality` | `core/epub_translation/runtime/adapter.py:43` | imported, never referenced | removed |

`RuntimeQAPolicy` and `analyze_runtime_quality` are **retained** in
`lts/txt_translation_runtime.py` because they are actively consumed by
`analyze_translation_quality` (`txt_translation_runtime.py:1396,1407`) — the S13-04
deliberate back-compat wrapper, which is preserved unchanged.

## 3. `core/validator.py` removal justification

Re-verified before deletion (S13-04 §4 conditions):

```text
production caller          = 0   (git grep "core.validator" -> none)
test caller                = 0   (git grep -> none)
import/export caller       = 0   (not exported; core/__init__.py empty)
CLI/UI caller              = 0
dynamic registry/factory   = 0   (not listed in any loader/manifest)
compatibility surface      = NONE (no __all__, no packaging/pyproject reference)
```

Only residual references are in `artifacts/` classification reports (documents, not code)
and historical `docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json`
(evidence record, not an importer). `core/glossary` is imported *by* the file, not the
reverse. Removed as a single dead file (not a legacy subsystem).

## 4. Compatibility assessment

- No removed symbol is exported by any package `__init__` / `__all__`.
- `core/translation_runtime/__init__.py` exports only `RuntimeQAPolicy`,
  `analyze_runtime_quality`, `count_korean_characters`, `detect_repeated_lines` — all kept.
- No tracked production or test module imports a removed symbol (verified with
  `git grep`).
- Historical references remain only in:
  - `archive/stage_tests/ntpe_te_v30_stage022_runtime_speed_policy_test.py` (archived,
    out of collection scope; **not modified** per the no-archive-cleanup rule — this
    archived test would now fail to import if run explicitly, which is expected and
    documented);
  - `docs/governance/migration/RM_2_3B_ROOT_DEPENDENCY_EVIDENCE.json` (frozen evidence).

Compatibility impact = **none** for the canonical product.

## 5. QA semantics preservation

- `analyze_translation_quality` (back-compat wrapper) — **unchanged**, still delegates to
  `analyze_runtime_quality`.
- `analyze_runtime_quality` detection logic / thresholds / codes — **unchanged**.
- `BasicTranslationQA` / EPUB `qa_report` propagation — **unchanged**.
- QA remains **advisory**; no new blocking state, no `qa_failed`, no `failed_chunk`, no QA
  manifest field, no retry loop, no output rejection.
- `qa_fail_policy` remains **inert / unchanged** (not touched).

## 6. Deferred consolidation items (explicitly not done)

```text
DEFERRED D1: BasicTranslationQA <-> runtime_qa merge            (format-contract risk)
DEFERRED D2: legacy archive: core/quality, engine/, core/translator.py, core/expansion/
DEFERRED D3: TIC offline gate, knowledge_validation, SDK TranslationValidator
UNCHANGED  : build_qa_retry_user_prompt (test-only; retained)
UNCHANGED  : qa_fail_policy (inert; retained)
UNCHANGED  : S13-03 pytest collection boundary (tests/conftest.py)
```

## 7. Files changed

```text
core/translation_runtime/runtime_qa.py   (-43: constant + 2 dead functions)
lts/txt_translation_runtime.py           (-13: import + 2 dead functions)
core/epub_translation/runtime/adapter.py (-1 : unused import)
core/validator.py                        (-65: entire dead file removed)
```

## 8. Static verification

```text
python -m compileall core lts ui                -> exit 0
git grep removed symbols (tracked prod/test)    -> 0 active callers
python -c import/symbol checks                  -> OK
git diff --check                                -> exit 0 (no whitespace errors)
```

No ImportError, NameError, circular import, or runtime behaviour change observed.
