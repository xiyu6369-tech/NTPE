# NTPE S6 Production User-Flow Gap Audit

**Report Date**: 2026-09-26
**Baseline Commit**: 942650d (chore(repo): clean up S5 diagnostic artifacts)
**Branch**: main
**origin/main**: 942650d

---

## 1. Baseline Verification

| Item | Expected | Actual | Status |
|------|----------|--------|--------|
| HEAD | 942650d | 942650d | ✅ PASS |
| origin/main | 942650d | 942650d | ✅ PASS |
| Branch | main | main | ✅ PASS |
| 4 Existing Modifications | Preserved | Preserved | ✅ PASS |
| - tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json | - | Modified | ✅ |
| - tests/literary/outputs/Regression_History.json | - | Modified | ✅ |
| - tests/literary/outputs/Regression_History.md | - | Modified | ✅ |
| - tests/ui/mock_translation_runtime.py | - | Modified | ✅ |
| No production files modified | - | Verified | ✅ PASS |
| No root scratch files created | - | Verified | ✅ PASS |

---

## 2. User-Flow Verification Matrix

| Flow | Result | Evidence |
|------|--------|----------|
| TXT Import | ✅ PASS | CanonicalBookIntakeAdapter.process_path() returns `ready`, `submission_eligible=True`, language=ko |
| TXT Translation Path (dry-run) | ✅ PASS | TranslationRuntime → LTS txt_translation_runtime → dry-run produces resume state, chunk packages |
| TXT Output (dry-run) | ⚠️ PARTIAL | Returns `incomplete` status (expected for dry-run); no final .txt produced in dry-run mode |
| EPUB Import | ✅ PASS | EpubExtractionBoundary.extract() returns `success`, metadata (title, author, language=ko, identifier), chapter_map (2 chapters) |
| EPUB Metadata | ✅ PASS | Title="Test Book", Language=ko, Identifier="test-book" correctly extracted |
| EPUB Chapter/Spine | ✅ PASS | 2 chapters extracted with correct spine order, source_href preserved |
| EPUB Canonical Intake | ⚠️ PARTIAL | Language detector returns `mixed` for short content → `manual_review_required`, `submission_eligible=False` |
| EPUB Translation (CLI) | ❌ FAIL | `main()` function missing handler for "epub" command (parser defines it, main() doesn't dispatch) |
| EPUB Translation (direct run_epub) | ⚠️ PARTIAL | Works when called directly, but blocked by intake `manual_review_required` |
| EPUB Packaging (S5) | ✅ PASS | 37/37 contract tests pass; 39/39 structure tests pass; mimetype, container.xml, OPF, nav, spine, resources all validated |
| EPUB Output Validation | ✅ PASS | _validate_epub_archive() checks mimetype, container.xml, OPF, manifest, spine, nav, XHTML references |
| UI State (Translation Launcher) | ❌ FAIL | "Start Translation" button shows "Translation execution is not enabled in Stage 1" — non-functional |
| UI State (Translation Studio) | ⚠️ PARTIAL | TXT translation connected via TranslationWorker; EPUB translation explicitly blocked with "EPUB translation not supported" |
| Production Route | ✅ PASS | Single canonical route: CLI/UI → TranslationRuntime → TranslationEngine → ProviderManager → NvidiaTranslationProvider → NvidiaClient → M3 |

---

## 3. Findings

### P0 — Production Blockers

#### S6-01: EPUB CLI Command Not Dispatched in main()
- **ID**: S6-01
- **Severity**: P0
- **Observed Behaviour**: `python ntpe_production_translate.py epub input.epub output` prints help/usage instead of running EPUB translation. The `epub` subparser is defined (line 196) but `main()` (line 1099) only handles `doctor`, `corpus`, `regression`, `evaluate`, `txt`, `batch`.
- **Expected Behaviour**: EPUB translation should execute via `run_epub(args)`.
- **Evidence**: `ntpe_production_translate.py:1099-1122` — no `elif args.command == "epub": return run_epub(args)`
- **Production Impact**: Users cannot translate EPUB via CLI at all. Complete blocker for EPUB workflow.
- **Likely Root Cause**: Oversight during CLI command registration; `run_epub` function exists (line 486) but not wired in `main()`.

#### S6-02: Translation Launcher "Start Translation" Button Non-Functional
- **ID**: S6-02
- **Severity**: P0
- **Observed Behaviour**: Clicking "Start Translation" in the Tkinter launcher shows a message box: "Translation execution is not enabled in Stage 1." No translation starts.
- **Expected Behaviour**: Button should launch translation via TranslationRuntime.
- **Evidence**: `ui/translation_launcher/controller.py:24-26` — `start_translation()` raises `RuntimeError`; `ui/translation_launcher/app.py:140-141` — `_start()` only shows message box.
- **Production Impact**: Primary GUI entry point (Translation Launcher) cannot translate anything. Users must use CLI.
- **Likely Root Cause**: Placeholder implementation left from Stage 1; never connected to actual runtime.

---

### P1 — Major Product Defects

#### S6-03: EPUB Translation Blocked in Translation Studio UI
- **ID**: S6-03
- **Severity**: P1
- **Observed Behaviour**: In ProjectPage, selecting an EPUB project shows tooltip "EPUB translation not supported" and "Translate" button remains disabled. Code explicitly checks `if project.get("chapter_map"):` and blocks.
- **Expected Behaviour**: EPUB projects should be translatable via the same canonical flow as CLI.
- **Evidence**: `ui/translation_studio/pages/project_page.py:449-451` — explicit block with `QMessageBox.warning(self, "提示", Strings.TRANSLATION_NOT_SUPPORTED_EPUB)`
- **Production Impact**: Modern PySide6 UI (Translation Studio) cannot translate EPUBs despite having full import/preview support.
- **Likely Root Cause**: EPUB translation pipeline not yet integrated into UI worker; placeholder limitation.

#### S6-04: EPUB Canonical Intake Fails on Short/Mixed-Language Content
- **ID**: S6-04
- **Severity**: P1
- **Observed Behaviour**: `CanonicalBookIntakeAdapter.ingest_extracted()` returns `manual_review_required` with warning "Language detection uncertain: mixed" for the test EPUB (108 chars, Korean+English). `submission_eligible=False` blocks translation.
- **Expected Behaviour**: EPUB metadata declares `language=ko`; intake should respect metadata or have a lower threshold for short texts.
- **Evidence**: Extraction returns `language=ko` (from OPF metadata), but `SourceLanguageDetector` on extracted text returns `mixed`. Intake treats `mixed` as uncertain → `manual_review_required`.
- **Production Impact**: Legitimate Korean EPUBs with short chapters or mixed content (e.g., glossaries, TOC pages) may be incorrectly blocked.
- **Likely Root Cause**: `SourceLanguageDetector` requires sufficient single-language text; short EPUBs fall below threshold. No fallback to OPF metadata language.

#### S6-05: TXT Dry-Run Returns Misleading "incomplete" Status
- **ID**: S6-05
- **Severity**: P1
- **Observed Behaviour**: Dry-run translation returns `status: "incomplete"` with `error: "Translation incomplete: 0/1 chunks succeeded"` instead of a clear dry-run success indicator.
- **Expected Behaviour**: Dry-run should return a distinct status (e.g., `dry_run_complete`) indicating packages were built successfully without provider calls.
- **Evidence**: `lts/txt_translation_runtime.py` dry-run path marks chunks as `dry_run` but final assembly treats 0 successful chunks as incomplete.
- **Production Impact**: Users/automation cannot reliably detect successful dry-run via status field.
- **Likely Root Cause**: Final status logic doesn't account for dry-run mode where all chunks are skipped.

---

### P2 — Quality / UX Defects

#### S6-06: EPUB Contract Test Failures (4 tests)
- **ID**: S6-06
- **Severity**: P2
- **Observed Behaviour**: 4 contract tests fail in `test_s1_epub_contract.py`:
  - `TestValidateEpubTranslationChunk::test_body_offsets_outside_extracted_raise`
  - `TestValidateChunkOwnership::test_chunk_offsets_outside_chapter_raises`
  - `TestValidateChunkOwnership::test_empty_chapter_must_have_exactly_one_chunk`
  - `TestEmptyChapter::test_empty_chapter_produces_one_chunk`
- **Expected Behaviour**: All contract tests should pass.
- **Evidence**: Pytest output shows `ValueError: body_end_offset (1) < body_start_offset (30)` for empty chapters.
- **Production Impact**: Contract validation rejects valid empty-chapter scenarios; may block legitimate EPUBs with empty chapters.
- **Likely Root Cause**: `EpubChapterBoundary.__post_init__` validation doesn't handle empty chapters (word_count=0) correctly.

#### S6-07: No EPUB Output Format in Translation Studio
- **ID**: S6-07
- **Severity**: P2
- **Observed Behaviour**: Translation Studio only outputs TXT. RM-8.3 delivery pipeline supports `quality_delivery_formats_v83: ("txt", "epub", "pdf")` but UI doesn't expose this.
- **Expected Behaviour**: UI should allow selecting output format (TXT/EPUB/PDF) for both TXT and EPUB sources.
- **Evidence**: `project_page.py` hardcodes `TxtTranslationOptions` with `quality_delivery_formats_v83=("txt",)`.
- **Production Impact**: Users wanting EPUB output from TXT source must use CLI with `--quality-delivery-formats-v83 epub`.
- **Likely Root Cause**: UI not updated for RM-8.3 multi-format delivery.

#### S6-08: Progress Reporting Inconsistent Between CLI and UI
- **ID**: S6-08
- **Severity**: P2
- **Observed Behaviour**: CLI shows detailed NTPE progress messages (`[NTPE PROGRESS] provider request start...`); UI shows only chunk-level progress (e.g., "3/10 成功").
- **Expected Behaviour**: Consistent progress granularity across interfaces.
- **Evidence**: `TranslationWorker._poll_progress()` reads `live_progress.json` which only emits chunk-level updates; CLI `emit_progress()` emits provider-attempt-level details.
- **Production Impact**: UI users lack visibility into provider-level retries, timeouts, model fallbacks.
- **Likely Root Cause**: `live_progress.json` written by LTS runtime doesn't include provider-attempt details; UI polls at 1s interval.

---

### P3 — Cosmetic / Documentation

#### S6-09: Translation Launcher "Provider"/"Model" Comboboxes Non-Functional
- **ID**: S6-09
- **Severity**: P3
- **Observed Behaviour**: Comboboxes show provider/model options from catalogs but selection doesn't affect actual translation (hardcoded to Nvidia/M3 in runtime).
- **Expected Behaviour**: Either remove unused controls or wire them to actual provider selection.
- **Evidence**: `app.py:55-60` populates from `provider_catalog()` and `model_catalog()`; `controller.py` never uses these values.
- **Production Impact**: Misleading UI — users think they can switch providers/models.
- **Likely Root Cause**: UI built for multi-provider future; current production route is Nvidia-only.

#### S6-10: Translation Studio "New Project" Button Placeholder
- **ID**: S6-10
- **Severity**: P3
- **Observed Behaviour**: "新增專案" button shows "功能尚未實作" message.
- **Evidence**: `project_page.py:435-438` — `_on_new_project()` shows placeholder message box.
- **Production Impact**: Minor UX gap; users can still import via Home page.

---

## 4. Existing Baselines That Remain Healthy

| Baseline | Status | Evidence |
|----------|--------|----------|
| **S5 EPUB Contracts** | ✅ HEALTHY | 37/37 packaging tests pass; 39/39 structure tests pass |
| **S5 EPUB Resource Preservation** | ✅ HEALTHY | Binary resources (images, fonts, CSS) byte-preserved; deterministic archive structure |
| **S5 EPUB Metadata Preservation** | ✅ HEALTHY | Title, author, language, identifier, publisher, date all preserved |
| **S5 EPUB Chapter Identity/Order** | ✅ HEALTHY | spine_position, source_href, fragment, chapter_id all preserved |
| **S5 EPUB Navigation/TOC** | ✅ HEALTHY | Original nav/NCX entries used; deterministic href mapping |
| **S5 EPUB CSS/Images/Fonts** | ✅ HEALTHY | Resources re-embedded with correct media types; CSS from source used |
| **Canonical Production Route** | ✅ HEALTHY | Single route: NvidiaTranslationProvider → NvidiaClient → M3; no legacy providers |
| **Production Default Model** | ✅ HEALTHY | `meta/llama-3.2-90b-vision-instruct` across all 9 config files |
| **Locked Dictionary (Name Consistency)** | ✅ HEALTHY | 鄭泰義/伊萊/里格勞 + alias map for variants; applied pre/post translation |
| **Glossary System** | ✅ HEALTHY | Multiple sources: character_override.json, glossary_override.json, glossary.txt, character_memory |
| **RM-8.2 Cross-Chunk Context** | ✅ HEALTHY | Feature-gated (quality_context_scene_v72); scene/chapter transition detection |
| **RM-8.3 Delivery Pipeline** | ✅ HEALTHY | Polish → Validation → Metadata/TOC → Multi-format export (txt/epub/pdf) |
| **QA Policies** | ✅ HEALTHY | min_length_ratio, max_korean_chars, max_repeated_lines, literary_quality gates |
| **Resume/Checkpoint System** | ✅ HEALTHY | Chunk-level resume with source_hash validation; live_progress.json polling |

---

## 5. Recommended S6 Work Queue

### S6-01
- **Priority**: P0
- **Problem**: EPUB CLI command not dispatched in `main()`
- **Why It Matters**: Complete blocker for EPUB translation via CLI
- **Affected Files**: `ntpe_production_translate.py` (main function, lines 1099-1122)
- **Expected Fix**: Add `elif args.command == "epub": return run_epub(args)` in main()
- **Acceptance Criteria**: `python ntpe_production_translate.py epub input.epub output --dry-run` executes run_epub and returns exit code 0/1

### S6-02
- **Priority**: P0
- **Problem**: Translation Launcher "Start Translation" button non-functional
- **Why It Matters**: Primary GUI entry point cannot translate anything
- **Affected Files**: `ui/translation_launcher/controller.py` (start_translation), `ui/translation_launcher/app.py` (_start)
- **Expected Fix**: Connect button to TranslationRuntime.translate_txt() via worker thread (like Translation Studio)
- **Acceptance Criteria**: Clicking "Start Translation" launches actual translation, shows progress, produces output file

### S6-03
- **Priority**: P1
- **Problem**: EPUB translation blocked in Translation Studio UI
- **Why It Matters**: Modern UI cannot translate EPUBs despite full import support
- **Affected Files**: `ui/translation_studio/pages/project_page.py` (_on_translate, lines 449-451), `ui/translation_studio/translation_worker.py`
- **Expected Fix**: Extend TranslationWorker to support EPUB via run_epub path; enable button for EPUB projects
- **Acceptance Criteria**: Selecting EPUB project enables "Translate" button; translation produces EPUB output via quality-delivery-v83

### S6-04
- **Priority**: P1
- **Problem**: EPUB canonical intake fails on short/mixed-language content
- **Why It Matters**: Legitimate Korean EPUBs with short chapters incorrectly blocked
- **Affected Files**: `core/adapters/canonical_book_intake_adapter.py` (ingest_extracted), `core/book_intake/language_detector.py`
- **Expected Fix**: Fallback to OPF metadata language when detector returns "mixed/unknown" for short texts; or add threshold parameter
- **Acceptance Criteria**: Test EPUB (108 chars, metadata language=ko) passes intake with `submission_eligible=True`

### S6-05
- **Priority**: P1
- **Problem**: TXT dry-run returns misleading "incomplete" status
- **Why It Matters**: Automation/users cannot detect successful dry-run
- **Affected Files**: `lts/txt_translation_runtime.py` (translate_txt final status logic)
- **Expected Fix**: Return distinct status `dry_run_complete` when all chunks processed in dry-run mode
- **Acceptance Criteria**: Dry-run returns `status: "dry_run_complete"` with chunk_total > 0, chunk_successful == chunk_total

### S6-06
- **Priority**: P2
- **Problem**: 4 EPUB contract test failures for empty chapters
- **Why It Matters**: Contract validation rejects valid empty-chapter EPUBs
- **Affected Files**: `core/epub_translation/contract/models.py` (EpubChapterBoundary.__post_init__), `tests/contract/test_s1_epub_contract.py`
- **Expected Fix**: Allow empty chapters (word_count=0, body_start_offset == body_end_offset)
- **Acceptance Criteria**: All 77 tests in test_s1_epub_contract.py pass

### S6-07
- **Priority**: P2
- **Problem**: Translation Studio lacks EPUB/PDF output format selection
- **Why It Matters**: Users cannot choose output format in UI
- **Affected Files**: `ui/translation_studio/pages/project_page.py` (_on_translate), `ui/translation_studio/translation_worker.py`
- **Expected Fix**: Add format selection UI; pass `quality_delivery_formats_v83` to TxtTranslationOptions
- **Acceptance Criteria**: UI allows selecting TXT/EPUB/PDF; selected format produced in output directory

### S6-08
- **Priority**: P2
- **Problem**: Progress reporting inconsistent between CLI and UI
- **Why It Matters**: UI users lack provider-level visibility
- **Affected Files**: `lts/txt_translation_runtime.py` (emit_progress), `ui/translation_studio/translation_worker.py` (_poll_progress)
- **Expected Fix**: Enhance live_progress.json with provider-attempt details; UI polls and displays
- **Acceptance Criteria**: UI shows provider attempt, model, timeout, retry wait messages like CLI

### S6-09
- **Priority**: P3
- **Problem**: Translation Launcher provider/model comboboxes non-functional
- **Why It Matters**: Misleading UI
- **Affected Files**: `ui/translation_launcher/app.py` (comboboxes), `ui/translation_launcher/controller.py` (config building)
- **Expected Fix**: Either remove comboboxes or wire to actual provider selection (requires multi-provider support)
- **Acceptance Criteria**: If multi-provider not planned, remove comboboxes; if planned, wire to runtime

### S6-10
- **Priority**: P3
- **Problem**: Translation Studio "New Project" button placeholder
- **Why It Matters**: Minor UX gap
- **Affected Files**: `ui/translation_studio/pages/project_page.py` (_on_new_project)
- **Expected Fix**: Implement project creation dialog or remove button
- **Acceptance Criteria**: Button either works or is removed

---

## 6. Acceptance Criteria Checklist

| Criterion | Status |
|-----------|--------|
| HEAD = 942650d | ✅ |
| origin/main = 942650d | ✅ |
| 4 existing modifications preserved | ✅ |
| No production files modified | ✅ |
| No existing features removed | ✅ |
| No model/provider/prompt changes | ✅ |
| No root scratch files created | ✅ |
| S5 functionality not regressed | ✅ |
| TXT flow audited | ✅ |
| EPUB flow audited | ✅ |
| UI flow audited | ✅ |
| Canonical production route audited | ✅ |
| Quality baseline audited | ✅ |
| Findings classified P0-P3 | ✅ |
| S6 work queue produced | ✅ |
| Report stored under artifacts/ | ✅ |
| No commit | ✅ |
| No push | ✅ |
| No tag | ✅ |

---

## 7. Summary

| Category | Count |
|----------|-------|
| Total Findings | 10 |
| P0 — Production Blockers | 2 |
| P1 — Major Product Defects | 3 |
| P2 — Quality/UX Defects | 3 |
| P3 — Cosmetic/Documentation | 2 |
| Production Files Modified | 0 |
| Commit | NO |
| Push | NO |
| Tag | NO |

**Audit Complete**: `S6_PRODUCTION_USER_FLOW_GAP_AUDIT_COMPLETE`
- **Report Path**: `artifacts/NTPE_S6_PRODUCTION_USER_FLOW_GAP_AUDIT.md`
- **Baseline HEAD**: 942650d
- **Findings Count**: 10
- **P0 Count**: 2
- **P1 Count**: 3
- **P2 Count**: 3
- **P3 Count**: 2
- **Production Files Modified**: 0