# NTPE S13-07 — Translation Release Live Dependency Split

Implementation of the S13-06 Option B boundary: move the canonical EPUB reader models out
of the legacy `core.translation_release` namespace, so canonical EPUB production no longer
imports `core.translation_release`.

## 0. Baseline / actual

```text
Baseline HEAD : 0b6b1416140e2ed9d6240096b379cbefbaf3fed4
origin/main   : 0b6b141
Actual HEAD   : S13-07 commit (this commit; see final report / git log)
Branch        : main
```

Pre-existing dirty state preserved. No reset / clean / restore --source / force-pull /
force-push / discard performed.

## 1. Pre-migration live closure (re-verified)

Independent re-verification of S13-06's closure (not assumed):

```text
live symbols   : ChapterBoundary, ReaderChapterMap
live module    : core/translation_release/reader_structure/models.py
canonical importer (production): core/epub_translation/reader_chapter_map.py:19   (ONLY)
other importers:
  legacy  : core/translation_release/reader_structure/{__init__,chapter_mapper,epub_packager}.py,
            core/translation_release/exporters/epub_exporter.py
  tests   : tests/contract/test_s4_epub_reader_chapter_map.py:33,
            tests/ui/test_s6_03_acceptance.py (4 inline),
            tests/unit/translation_release/reader_structure/{test_chapter_mapper,test_epub_packager}.py
package initializers: core/translation_release/__init__.py (-> polish -> runtime_formatter),
                      core/translation_release/reader_structure/__init__.py (-> models, chapter_mapper, epub_packager)
```

**Minimal live closure = the two dataclasses only** (`ChapterBoundary`, `ReaderChapterMap`;
stdlib `dataclasses` only). `polish`, `chapter_mapper`, legacy `epub_packager` are
historical neighbors pulled only by package `__init__` side effects; they were **not**
moved.

No `pickle` / `asdict` / `__module__` / `__qualname__` coupling to these models was found;
the only identity-sensitive check is `isinstance(reader_chapter_map, ReaderChapterMap)` in
`tests/contract/test_s4_epub_reader_chapter_map.py:244` (satisfied by the shared class).

## 2. Before / after architecture

```text
BEFORE
  core/epub_translation/reader_chapter_map.py
        -> core.translation_release.reader_structure.models   (legacy namespace)
              -> executes translation_release/__init__ -> polish -> runtime_formatter
              -> executes reader_structure/__init__ -> chapter_mapper, epub_packager

AFTER
  core/epub_translation/reader_chapter_map.py
        -> core.epub_translation.reader_models                (canonical EPUB-owned)
  core/translation_release/reader_structure/models.py         (legacy shim, re-export only)
        -> core.epub_translation.reader_models
```

## 3. Moved files / symbols

| Item | From | To |
|---|---|---|
| `ChapterBoundary` | `core/translation_release/reader_structure/models.py:6-18` | `core/epub_translation/reader_models.py:6-18` |
| `ReaderChapterMap` | `core/translation_release/reader_structure/models.py:21-25` | `core/epub_translation/reader_models.py:21-25` |

Definitions moved **verbatim** (same field names, order, types, docstrings,
`@dataclass(frozen=True)`).

## 4. Modified / new files

```text
NEW      core/epub_translation/reader_models.py            (canonical definitions)
MODIFIED core/epub_translation/reader_chapter_map.py:19    (import from canonical)
MODIFIED core/translation_release/reader_structure/models.py (compatibility shim, re-export)
NEW      tests/unit/test_s13_07_epub_reader_models_split.py (focused regression + boundary)
```

## 5. Compatibility decision

Active importers of the old namespace remain (legacy delivery, legacy reader_structure,
and legacy tests) → per S13-07 §8, a **compatibility shim** is required and was created:

```text
core.translation_release.reader_structure.models  ==  re-export of
core.epub_translation.reader_models
```

- Single implementation (no duplicate class definitions) — verified by identity test.
- No compatibility shim was created anywhere else (none needed).
- The legacy delivery adapter `core/adapters/rm8_delivery_adapter.py` is **unchanged**.

## 6. Remaining legacy files

The whole legacy package is preserved except the live-copy definition (now a re-export):

```text
core/translation_release/{__init__,polish,models,metadata,package,validator,delivery_pipeline,
    release_contract,release_manifest,release_validation,te_v6_release}.py
core/translation_release/exporters/*
core/translation_release/reader_structure/{__init__,chapter_mapper,epub_packager}.py
core/adapters/rm8_delivery_adapter.py
```

None of these was deleted; `engine/`, `core/quality/`, `core/context/`, `core/translator.py`
were not touched.

## 7. Behavior preservation

Identical by construction (verbatim dataclass move):

```text
ChapterBoundary behavior      : unchanged (frozen, field order, 0-based chapter_order)
ReaderChapterMap behavior     : unchanged (frozen tuple container)
chapter ordering / spine_position : unchanged (reader_chapter_map.py logic untouched)
linear / non-linear semantics : unchanged
EPUB packaging / TOC          : unchanged (runtime/epub_packager.py untouched)
offset contract / Glossary / Output / Recovery : unchanged
```

No production behavior change was required to complete the split (none made).

## 8. Verification summary

```text
collect-only   : 3954 (baseline 3950 + 4 new S13-07 tests; explained)
contract       : 338 passed
reader_project : 86 passed
e2e            : 55 passed
runtime        : 10 passed
S12-06 + S12-07: 14 passed
test_s4        : 41 passed
new split test : 4 passed
compileall     : exit 0
```

Pre-existing, environment-sensitive failures unrelated to this change:
`tests/unit/translation_release/reader_structure/test_epub_packager.py` has 3 failures
(`..._fails_gracefully_on_permission_error`, `..._fails_gracefully_on_invalid_path`,
`test_epub_exporter_failure_isolation`). **Verified pre-existing**: the same 3 tests fail
identically when the baseline file contents are restored (ebooklib does not raise on the
injected write failure in this environment). Not caused by, and not fixed by, S13-07.

## 9. Acceptance

```text
Production Files Modified : 2 (+1 new canonical module)
Tests Modified            : 0 (1 new test added)
Provider / Network / Real Translation : 0 / 0 / 0
```

**FINAL: PASS**
