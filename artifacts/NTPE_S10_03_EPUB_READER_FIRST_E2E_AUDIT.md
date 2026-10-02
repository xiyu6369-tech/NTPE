# NTPE S10-03 — EPUB Reader-First Production E2E Audit

Baseline HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Branch: `main`
Tag: `s9-complete`

Purpose: record the canonical entry path, the production/test seams used by the
S10-03 E2E, the fixture, output path, runtime injection, packaging path, the
findings surfaced by the real E2E, and the minimal repairs applied.

---

## 1. Canonical Entry Path (real, not mocked)

```
EPUB file
  -> EpubExtractionBoundary.extract()            core/adapters/epub_extraction_boundary.py
  -> ExtractedTextIntakeRequest                   core/adapters/epub_extraction_boundary.py
  -> CanonicalBookIntakeAdapter.ingest_extracted  core/adapters/canonical_book_intake_adapter.py
  -> EpubTranslationInput (built inline in UI)    ui/translation_studio/pages/project_page.py
  -> chunk_epub_translation_input()               core/epub_translation/chunking.py
  -> EpubTranslationOptions
  -> TranslationRunner / TranslationWorker        ui/translation_studio/translation_worker.py
  -> injected runtime execution (deterministic)   [SEAM]
  -> build_epub_reader_chapter_map_with_metadata  core/epub_translation/reader_chapter_map.py
  -> pack_epub_resource_aware()                   core/epub_translation/runtime/epub_packager.py
  -> final EPUB on disk
  -> Project output.artifact_path persistence      ui/translation_studio/pages/project_page.py
  -> Open Result via injected ResultOpener         ui/translation_studio/result_opener.py
```

Entry used by the E2E: `ProjectPage.add_project` (real persistence) ->
`ProjectPage._on_translate()` (real route) -> real `TranslationRunner`.
The recovery E2E additionally uses `ProjectPage._on_resume()` (real route).

---

## 2. Test Seams

| Concern | Real | Injected / faked |
|---|---|---|
| Extraction | YES | - |
| Intake | YES | - |
| EpubTranslationInput | YES | - |
| Chunking | YES | - |
| Packaging | YES | - |
| Project persistence | YES | - |
| Output path | YES | - |
| Runtime execution | - | `translate_epub_translation_input` patched to a deterministic function |
| Provider / network | 0 | never invoked |
| OS opener | - | `FakeResultOpener` |
| Qt dialogs | - | `QMessageBox` patched (modal dialogs) |

No production extraction/intake/chunking/packaging/Project/output-path is
mocked. Only runtime *execution* and the OS opener/dialogs are injected.

---

## 3. Fixture

`tests/e2e/test_s10_03_epub_reader_first_e2e.py::make_book_epub`
- deterministic EPUB3 in `pytest` tmp dirs only
- metadata: title / creator / language / identifier (`urn:uuid:...`)
- 2 linear chapters, spine, nav TOC
- one referenced resource `img.png` (`<img src="img.png"/>` in ch1)
- body text per chapter

Isolation: tmp `NTPE_HOME`, tmp source/output, no repo output, no network.

---

## 4. Output Path

Real worker path: `<source.parent>/output/epub_translation/<safe id>/<stem>_zh.epub`,
computed by `core/epub_translation/output_layout.py::epub_output_dir`.
Project persistence stores the exact runtime-returned path
(`_persist_translation_result`), never a reconstructed guess.

---

## 5. Findings Surfaced by the Real E2E

### F2 — Unsafe EPUB identifier used as output directory name (classification B, FIXED)
- After S10-02 restored metadata fidelity, `metadata.identifier` (e.g.
  `urn:uuid:...`) reached `output_dir.mkdir()` unsanitized. On Windows this
  raises `OSError [WinError 123]`.
- Evidence: `mkdir` of `output/epub_translation/urn:uuid:s10-03-fixture` fails.
- Minimal repair: new pure module `core/epub_translation/output_layout.py`
  (`safe_output_segment`, `epub_output_dir`) used by the EPUB runtime adapter and
  both UI workers. Raw identifier remains in metadata; only the path segment is
  sanitized. No packaging logic rewritten, no schema change.

### F3 — Recovery project/source binding not enforced (classification C, FIXED)
- S9-06 `validate_project_binding` / `validate_source_binding` returned `True`
  unconditionally (the S9-06 test itself notes "might not catch this yet").
  S10-03 §26/§27 require wrong-project and wrong-source artifacts to BLOCK.
- Minimal repair: enforce that a resume state with a recorded `output_dir` lives
  inside it, and that a resume state recording `input` matches the project
  source. Unverified (no recorded output dir / no recorded input) remains
  non-blocking, preserving existing semantics.

### F4 — Persisted library drops preview_text (classification D/C, DEFERRED)
- `_add_persisted_project` rebuilds rows from persisted data without
  `preview_text`, so the toolbar Preview button is disabled after persistence.
- The reader journey's preview is produced by real extraction at import time and
  is validated by the E2E; the dashboard-button limitation is a pre-existing
  S9-04 UI concern and is DEFERRED (out of S10-03 scope).

### Deferred, unchanged
- S3 non-linear spine ordering: DEFERRED (all-linear fixtures; not exercised).
- TOC title fallback: DEFERRED (in-document `<h1>` titles present).

---

## 6. Known Gaps / Notes

- The EPUB runtime adapter's own output dir now uses the same safe-layout helper,
  so unpatched production and the E2E worker share one canonical layout.
- The recovery E2E writes deterministic resume-state JSON directly (the E2E
  injects runtime execution, so the runtime does not create it). The recovery
  layer only reads the artifact; this is the canonical contract boundary.
- The E2E patches `QMessageBox` because the real completion/failure paths raise
  modal dialogs; this is an OS/UI dependency, not a production-path bypass.

---

## 7. Validation Evidence

```
E2E (single run):       tests/e2e  -> 45 passed
S10-03 focused:         18 passed (10 journey/production + 8 recovery)
Combined regression:    520 passed, 1 skipped
  (reader_project, s1..s5c contract, extraction unit+integration, s10-02,
   ui epub/s8/s9 suites, epub launcher)
S6-03 acceptance:       7 passed (isolated; batched Qt+Tk threads abort)
Pre-existing (re-verified, not S10-caused):
  reader_structure packager : 3 failed / 29 passed (Windows permission env)
  lts_stage_01 TXT          : 3 failed / 2 passed (missing root script + stale expectations)
```
