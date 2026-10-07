# NTPE S13-06 — `core/translation_release` Split Analysis

Highest-priority candidate. Baseline HEAD `79d1acd`. Audit-only; **no split executed**.

## 1. Package inventory (18 modules)

```text
core/translation_release/
  __init__.py                 -> polish (normalize_paragraphs, unify_quote_style, polish_full_novel)
  polish.py                   -> imports core.translation_runtime.runtime_formatter
  models.py                   -> DeliveryManifest, QualityCertificate, DeliveryResult, TOCEntry
  metadata.py                 -> imports models, validator
  package.py                  -> imports models
  validator.py
  delivery_pipeline.py        -> imports models, polish, validator, metadata, package, reader_structure.*, naturalness
  release_contract.py         -> TEV6ReleaseContract
  release_manifest.py
  release_validation.py       -> discipline/evidence/naturalness/production_runtime freezes
  te_v6_release.py            -> TEV6ReleaseContract, build_te_v6_release_contract
  exporters/__init__.py
  exporters/base.py           -> imports models
  exporters/epub_exporter.py  -> imports base, models, reader_structure.*
  exporters/pdf_exporter.py   -> imports base, models
  reader_structure/__init__.py        -> models, chapter_mapper, epub_packager
  reader_structure/models.py          -> ChapterBoundary, ReaderChapterMap (stdlib only)
  reader_structure/chapter_mapper.py  -> build_reader_chapter_map; imports models
  reader_structure/epub_packager.py   -> pack_epub; imports models
```

## 2. Dependency map

### 2.1 Live canonical symbols (reached by the reader-facing EPUB path)

```text
core/epub_translation/reader_chapter_map.py:19
    from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap
        |
        v
ui/translation_studio/translation_worker.py:88-89
ui/translation_launcher/worker.py:109-110
    from core.epub_translation.runtime.epub_packager import pack_epub_resource_aware
    from core.epub_translation.reader_chapter_map import build_epub_reader_chapter_map_with_metadata
```

Type-identity coupling: `core/epub_translation/runtime/epub_packager.py:26` consumes the
**same** `ChapterBoundary, ReaderChapterMap` re-exported by
`core/epub_translation/reader_chapter_map.py`. These are the classes used throughout
canonical EPUB spine/ordering packaging (CLOSED capability).

### 2.2 Import-path closure actually executed by the canonical import

Python executes package `__init__` files on any submodule import, so the canonical import
transitively pulls:

```text
core/translation_release/__init__.py            (-> polish -> core.translation_runtime.runtime_formatter)
core/translation_release/polish.py
core/translation_release/reader_structure/__init__.py   (-> models, chapter_mapper, epub_packager)
core/translation_release/reader_structure/models.py     <-- logically live
core/translation_release/reader_structure/chapter_mapper.py  (import-path only)
core/translation_release/reader_structure/epub_packager.py   (import-path only)
```

### 2.3 Legacy-only symbols (delivery subset)

Reached **only** through the test-only `core/adapters/rm8_delivery_adapter.py`:

```text
models.py, metadata.py, package.py, validator.py, delivery_pipeline.py,
exporters/, release_contract.py, release_manifest.py, release_validation.py, te_v6_release.py
```

`rm8_delivery_adapter` has no production importer (only
`tests/unit/adapters/test_rm8_delivery_adapter.py`); no registry/config/manifest dynamic
reference was found.

### 2.4 Tests-only symbols

`tests/unit/translation_release/*` (delivery + reader_structure + polish),
`tests/contract/test_s4_epub_reader_chapter_map.py:33` (direct import of
`reader_structure.models`), `tests/ui/test_s6_03_acceptance.py` (reader_structure.models).

### 2.5 Unreferenced symbols

None proven: every module is reachable through either the canonical import path or the
delivery/adapter/test path.

## 3. Options

### Option A — keep the whole package, defer

- Viable and lowest risk; zero code change.
- Leaves a mixed package (live models + legacy delivery) that obscures the canonical
  boundary; not a resolution.

### Option B — split the live canonical component, then archive the remainder

Proposed split boundary:

```text
MOVE (live)  : ChapterBoundary, ReaderChapterMap  (reader_structure/models.py)
               -> a canonical location not governed by translation_release/__init__
ARCHIVE      : delivery subset (2.3) + legacy reader_structure packager/chapter_mapper
KEEP/UPDATE  : core/epub_translation/reader_chapter_map.py import target
```

Consequences that make this non-trivial (must be handled in the future task):
- Any relocation must **neutralize the package-`__init__` side effects**: today importing
  the models also executes `translation_release/__init__` (→ `polish` → canonical
  `runtime_formatter`) and `reader_structure/__init__` (→ legacy `chapter_mapper`,
  `epub_packager`). A clean split should avoid pulling the legacy packager.
- Type-identity must be preserved for canonical EPUB packaging
  (`core/epub_translation/runtime/epub_packager.py:26`).
- Importers to update: `core/epub_translation/reader_chapter_map.py:19`,
  `core/epub_translation/runtime/epub_packager.py:26`,
  `tests/contract/test_s4_epub_reader_chapter_map.py:33`,
  `tests/unit/translation_release/reader_structure/*`.

### Option C — prove the whole package is an active production dependency

- Rejected. The delivery subset is reached only through a test-only adapter; no canonical
  route consumes it. Option C is not supportable by evidence.

## 4. Recommendation

**Option B**, executed as its own dedicated, separately-authorized task (not S13-06).
Until then, **Option A** is the safe default: the package is preserved unchanged.

`core/translation_release` is therefore classified **DEPENDENCY TO SPLIT** — it must
**not** be archived as a whole, because `reader_structure/models.py` is a live canonical
dependency of EPUB packaging.

## 5. Live dependency verdict

The live dependency **is safely bounded**:

```text
LIVE canonical : reader_structure/models.py (ChapterBoundary, ReaderChapterMap)
                 + import-path closure: __init__.py, polish.py,
                   reader_structure/__init__.py, chapter_mapper.py, epub_packager.py
LEGACY-only     : delivery subset (2.3)
```

→ S13-06 is **not** inconclusive on this point.
