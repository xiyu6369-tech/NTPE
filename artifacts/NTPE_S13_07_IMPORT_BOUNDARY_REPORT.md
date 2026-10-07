# NTPE S13-07 — Import Boundary Report

Companion to `artifacts/NTPE_S13_07_TRANSLATION_RELEASE_SPLIT.md`. Baseline HEAD `0b6b141`.
Records the canonical ↔ legacy import boundary before/after the split.

## 1. Before — canonical imports

`core/epub_translation/**` production modules importing `core.translation_release`:

```text
core/epub_translation/reader_chapter_map.py:19
    from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap
```

That was the **only** canonical production import of `core.translation_release` on the EPUB
path (via `reader_chapter_map.py`, consumed by `runtime/epub_packager.py:26` and both UI
workers).

## 2. After — canonical imports

```text
core/epub_translation/reader_chapter_map.py:19
    from core.epub_translation.reader_models import ChapterBoundary, ReaderChapterMap
```

Static scan result:

```text
rg -n "core.translation_release" core/epub_translation   ->  (no matches)
```

`core/epub_translation/reader_chapter_map.py` no longer depends on `core.translation_release`.

## 3. `core.translation_release` references — classification

### 3.1 Canonical production (must be 0) — AFTER

```text
core/ / lts/ / ui/ / ntpe_production_translate.py  ->  0 references to core.translation_release
```

(Confirmed by `git grep` over canonical roots; the only surviving reference is the legacy
adapter in §3.2.)

### 3.2 Legacy-only references (retained)

```text
core/adapters/rm8_delivery_adapter.py:7-8
    from core.translation_release.delivery_pipeline import run_delivery_pipeline, DeliveryResult
    from core.translation_release.models import DeliveryManifest, QualityCertificate
```

`rm8_delivery_adapter` has no production importer (only
`tests/unit/adapters/test_rm8_delivery_adapter.py`) → legacy-only; **retained unchanged**
(S13-07 §14).

Internal legacy imports (all inside the preserved package):

```text
core/translation_release/__init__.py, polish.py, models.py, metadata.py, package.py,
validator.py, delivery_pipeline.py, release_*.py, te_v6_release.py, exporters/*,
reader_structure/{__init__,chapter_mapper,epub_packager}.py
```

### 3.3 Compatibility shim (the moved live path)

```text
core/translation_release/reader_structure/models.py
    from core.epub_translation.reader_models import ChapterBoundary, ReaderChapterMap
```

Re-export only — no duplicate definition, single implementation.

## 4. Runtime boundary

```text
UI / CLI
  -> core/epub_translation/runtime/adapter.py            (EpubTranslationOptions / translate)
  -> core/runtime_orchestrator.manager.RuntimeOrchestrator
  -> core/translation_engine.translation_engine.TranslationEngine
  -> core/epub_translation.runtime.epub_packager.pack_epub_resource_aware
  -> core/epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata
  -> core/epub_translation.reader_models  (ChapterBoundary / ReaderChapterMap)
```

No re-introduction of `translation_release` anywhere in this chain.

## 5. Tests proving the boundary

New: `tests/unit/test_s13_07_epub_reader_models_split.py` (4 tests):

```text
test_canonical_reader_chapter_map_binds_canonical_models
    core.epub_translation.reader_chapter_map.ChapterBoundary is core.epub_translation.reader_models.ChapterBoundary
test_legacy_shim_reexports_single_canonical_definition
    core.translation_release.reader_structure.models.{ChapterBoundary,ReaderChapterMap} is canonical
test_canonical_epub_source_has_no_translation_release_import
    scans every core/epub_translation/**/*.py source for "core.translation_release" -> none
test_reader_models_contract_is_preserved
    construction + equality + frozen semantics
```

Existing canonical coverage retained (unchanged): `tests/contract/test_s4_epub_reader_chapter_map.py`
(41 passed) exercises `build_epub_reader_chapter_map[_with_metadata]`;
`tests/integration/test_s12_07_glossary_epub_real_adapter_e2e.py` exercises the real
adapter → packaging → persisted read-back.

## 6. Verification matrix

```text
collect-only   : 3954 (3950 baseline + 4 S13-07 tests)
contract       : 338 passed
reader_project : 86 passed
e2e            : 55 passed
runtime        : 10 passed
S12-06 + S12-07: 14 passed
test_s4        : 41 passed
split test     : 4 passed
compileall     : exit 0
```

Pre-existing env-sensitive failures in `tests/unit/translation_release/reader_structure/test_epub_packager.py`
(3) were proven to fail identically at baseline content and are unrelated to the boundary.

## 7. Result

```text
canonical EPUB production dependency on core.translation_release : ELIMINATED
legacy translation_release package                               : PRESERVED (shim + delivery)
second implementation                                            : NONE (identity-verified)
```
