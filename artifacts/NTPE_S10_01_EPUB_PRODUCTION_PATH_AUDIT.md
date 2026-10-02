# NTPE S10-01 — EPUB Production Translation Path Audit

Status: AUDIT COMPLETE (no production code modified)
Phase: S10-01 (Audit + Repair Design only)
Baseline HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Branch: `main`
Tag: `s9-complete`

This document is the authoritative S10-01 audit. It records the current state of
the EPUB production translation path, the root cause of deferred gap **F1**, and
the boundary/owner classification. No repair is performed here (that is S10-02).

---

## 0. Governance Result

```
git status --short
 M memory/character_memory_lts.json                (pre-existing, extra, OUT-OF-SCOPE)
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json  (pre-existing, OUT-OF-SCOPE)
 D tests/literary/outputs/PS-03/README.md          (pre-existing, OUT-OF-SCOPE)
 M tests/literary/outputs/Regression_History.json  (pre-existing, OUT-OF-SCOPE)
 M tests/literary/outputs/Regression_History.md    (pre-existing, OUT-OF-SCOPE)

git rev-parse HEAD   -> 4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e   (MATCH)
git branch --show-current -> main                                   (MATCH)
git describe --tags --always -> s9-complete                         (MATCH)
```

`memory/character_memory_lts.json` was also dirty and is not in the task's
four-file list. It is treated identically: pre-existing, out-of-scope, untouched.

No `reset/clean/stash/revert/pull/push`. No commit. No tag. All dirty files untouched.

---

## 1. Scope Inventoried

Full path audited, layer by layer:

```
EPUB file
  -> EpubExtractionBoundary            core/adapters/epub_extraction_boundary.py
  -> ExtractedTextIntakeRequest        core/adapters/epub_extraction_boundary.py:92
  -> CanonicalBookIntakeAdapter        core/adapters/canonical_book_intake_adapter.py
  -> EpubTranslationInput (built inline in TWO production call sites)
                                       ui/translation_studio/pages/project_page.py:1125
                                       ui/translation_launcher/controller.py:176
  -> chapter_map                       core/epub_translation/contract/models.py:32
  -> chunk_epub_translation_input      core/epub_translation/chunking.py:205
  -> EpubTranslationOptions            core/epub_translation/runtime/adapter.py:63
  -> TranslationRunner                 ui/translation_studio/translation_worker.py:245
                                       ui/translation_launcher/worker.py:276
  -> EPUB runtime                      core/epub_translation/runtime/adapter.py:245
  -> EPUB packaging                    core/epub_translation/runtime/epub_packager.py:805
  -> final EPUB artifact               <src.parent>/output/epub_translation/<id>/<stem>_zh.epub
  -> Project persistence               ui/translation_studio/pages/project_page.py:849
  -> Open Result                       ui/translation_studio/pages/project_page.py:597
```

---

## 2. Layer Contracts (Input / Output / Owner / Persistence / Failure / Tests / Production Use)

### 2.1 EpubExtractionBoundary
- Input contract: `extract(epub_path: Path)`; validated by `validate_epub`.
- Output contract: `EpubExtractionResult` with `original_hash` (full SHA256),
  `extracted_text` (marker-inclusive), `chapter_map: tuple[ChapterBoundary]`,
  `metadata`, `extraction_manifest`, `status`, `warnings`.
  - `ChapterBoundary` DECLARES `start_offset/end_offset` AND
    `body_start_offset/body_end_offset` (`epub_extraction_boundary.py:44-45`).
  - Only `start_offset/end_offset` are ever populated. `body_*_offset` are
    **always `None`** (`epub_extraction_boundary.py:210-222`).
- Owner: `core/adapters/epub_extraction_boundary.py`.
- Persistence: none (pure).
- Failure semantics: raises `EpubExtractionError(blocked=...)`; security blocks raise.
- Current tests: `tests/unit/adapters/test_epub_extraction_boundary.py` (UNIT ONLY),
  `tests/integration/test_epub_extraction_e2e.py` (extraction→intake only).
- Actual production use: YES, via both UI call sites.

### 2.2 ExtractedTextIntakeRequest / CanonicalBookIntakeAdapter
- Input contract: `ExtractedTextIntakeRequest` mirrors `EpubExtractionResult`
  (`chapter_map`, `extraction_manifest`, hashes, `epub_metadata: dict`).
- Output contract: `CanonicalIntakeResult` preserving `chapter_map`,
  `resource_refs`, `extraction_manifest`, `extraction_provenance`,
  `epub_metadata` (friendly-key dict).
- Owner: `core/adapters/canonical_book_intake_adapter.py`.
- Persistence: none.
- Failure semantics: raises `EpubExtractionError` when status is
  `blocked`/`manual_review_required` (`:125-137`).
- Current tests: `tests/integration/test_epub_extraction_e2e.py` (PARTIAL INTEGRATION).
- Actual production use: YES.
- Note: `chapter_map` is passed through **unchanged** (`:192`), so the missing
  `body_*_offset` is preserved, not repaired, not dropped.

### 2.3 EpubTranslationInput (contract)
- Input: built from `CanonicalIntakeResult` in two duplicated call sites.
- Output: `EpubTranslationInput` with `chapter_map: tuple[EpubChapterBoundary]`.
- Owner: contract `core/epub_translation/contract/models.py`.
- `EpubChapterBoundary.body_start_offset/body_end_offset` are `int | None`
  defaulting to `None` (`models.py:61-62`). The docstring states these are
  "pure chapter body ranges ... may be unavailable (None) if extraction layer
  has not yet provided them" (`models.py:44-47`). Ownership is assigned to the
  extraction layer.
- Persistence: none.

### 2.4 chunk_epub_translation_input
- Input: `EpubTranslationInput`, `extracted_text`, optional `ChunkingOptions`.
- Output: `tuple[EpubTranslationChunk]` (pure body text, chapter-owned).
- Owner: `core/epub_translation/chunking.py`.
- Failure semantics: **raises `ValueError`** when any chapter is missing body
  offsets (`chunking.py:237-241`). It deliberately does NOT derive them.
- Current tests: `tests/contract/test_s2_epub_chunking.py` (UNIT ONLY) — the test
  helper *fabricates* body offsets (`make_chapter_boundary` defaults
  `body_start_offset=start+30`), so this layer never sees extraction's real
  output in tests.
- Actual production use: YES, but unreachable because of §3.

### 2.5 EPUB runtime / TranslationRunner / packaging (downstream, for boundary check)
- Runtime adapter delegates to canonical `RuntimeOrchestrator` → `TranslationEngine`
  (`adapter.py:283-288`); it consumes `chunk.source_text` only and does not need
  body offsets. No runtime change is required to fix F1.
- Workers package the final EPUB and return `output` = packaged path
  (`translation_worker.py:127-144`, `worker.py:148-165`).
- Packaging consumes `translation_input.metadata`, chapter identity,
  `source_href`, resources; it does not consume body offsets
  (`epub_packager.py:862-1008`). So it is downstream-safe but metadata-fidelity
  impaired while §4's metadata defect stands.

---

## 3. F1 Root-Cause Audit

### 3.1 Reproduction (offline, deterministic, provider/network = 0)

```
status success
raw_meta_keys ['http://purl.org/dc/elements/1.1/:title', ... ':creator', ':language', ':identifier']
body_offsets   [(1, 1, 0, 126, None, None), (2, 2, 126, 210, None, None)]
intake epub_metadata title= None
contract metadata title= None
CHUNK RAISED: ValueError Chapter ch0001 missing body offsets; cannot perform chapter-aware chunking
```

### 3.2 A. Chapter offsets
- Extraction computes `start_offset`/`end_offset` from the full marker-inclusive
  string `marker + chapter_text + "\n"` where
  `marker = f"=== CHAPTER {n}: {title} ===\n"` (`epub_extraction_boundary.py:202-206`).
- `body_start_offset`/`body_end_offset` are declared but never assigned. They are
  deterministically derivable at that exact point:
  `body_start = start_offset + len(marker)`, `body_end = body_start + len(chapter_text)`.
- Result: no deterministic body mapping reaches chunking. **BROKEN.**

### 3.3 B. Chapter identity
- `chapter_id` = `f"ch{spine_position:04d}"` (`models.py:72-77`) — stable and
  consistent across contract/chunk/result/packaging.
- Extraction iterates `all_spine_items = linear_items + supplementary_items`
  (`epub_extraction_boundary.py:164,178`). If an EPUB has a non-linear spine
  item between linear items, `chapter_map` will contain non-monotonic
  `spine_position` values, which `validate_epub_translation_input` rejects
  ("spine positions not strictly increasing", `validation.py:146-151`).
  Latent identity/ordering defect (not triggered by the 2-chapter all-linear
  fixture). See §4 secondary finding S3.
- `_resolve_chapter_title_fallback` looks up `spine_item.get("href")`
  (`epub_extraction_boundary.py:1156-1160`), but spine dicts carry only
  `idref/linear/spine_position`, so TOC-title fallback silently degrades to
  `"Chapter N"` whenever a chapter lacks an in-document `<h1>/<h2>/<title>`.
  Title-fidelity defect, not identity-breaking. See §4 secondary finding S4.

### 3.4 C. Extraction vs Intake
- Intake preserves `chapter_map`, `resources`, `metadata.raw`,
  `extraction_manifest`, hashes, provenance. It does not silently drop fields.
- BUT both production call sites pass `epub_metadata=dict(metadata.raw)`
  (`controller.py:103`, `project_page.py:1053`). `metadata.raw` keys are
  namespace-qualified (`"http://purl.org/dc/elements/1.1/:title"`), while
  `ingest_extracted` reads plain keys `get("title")` (`canonical_book_intake_adapter.py:146-154`).
  Net effect: `EpubMetadata.title/author/language/identifier/publisher/date`
  all become `None` on the production path. See §4 secondary finding S1.

### 3.5 First broken contract
```
First broken contract : extraction -> contract chapter body offsets
Exact boundary        : core/adapters/epub_extraction_boundary.py:210-222
Why it breaks         : extraction declares body_*_offset but emits None;
                        chunking requires them and refuses to derive
Owner who should fix  : EpubExtractionBoundary (extraction layer)
Manifestation         : core/epub_translation/chunking.py:237-241 ValueError
Classification        : A. Extraction contract defect
```

---

## 4. Secondary Findings (independent of F1)

- **S1 — Metadata mapping defect (classification B).**
  Production call sites feed namespaced `metadata.raw` into an adapter that reads
  plain keys, so all DC metadata is lost before packaging. Packaging then falls
  back to `original_hash[:16]` title / `None` author (`epub_packager.py:863-874`).
  Output-contract metadata preservation is impaired. Repair remains at the
  extraction/intake boundary (no schema/runtime change).

- **S2 — Duplicated production mapping.**
  `project_page.py:1035-1169` and `controller.py:72-220` duplicate the
  extraction→intake→EpubTranslationInput→chunking mapping. Any fix must be
  applied twice unless a single shared builder is introduced. Not a defect by
  itself, but an atomicity/divergence risk for S10-02.

- **S3 — Non-linear spine ordering.** See §3.3. Violates contract spine
  monotonicity when supplementary items exist.

- **S4 — TOC-title fallback lookup bug.** See §3.3. Title fidelity only.

- **S5 — Post-normalization offset risk.** `extracted_text` is offset-computed
  during the loop and then `\r\n`→`\n` normalized afterward
  (`epub_extraction_boundary.py:228`). Today `_normalize_text` already removes
  `\r` per chapter so this is a no-op, but the body-offset repair must be
  computed on the same already-normalized text (it is) and should not rely on a
  later mutating normalization for correctness.

---

## 5. Chunking Contract Audit (answers)

1. Does chunking require body offsets? **Yes**, hard requirement
   (`chunking.py:237-241`).
2. Offset owner? **Extraction** owns the body span; the contract docstring
   (`models.py:44-47`) and the chunking refusal-to-derive both assign it upstream.
3. On missing offsets, chunking should: **reject** (current behavior is correct
   for a strict contract). It must not derive/repair (repair belongs to the owner).
4. Is the exception a validation failure or production defect? The exception is a
   correct validation failure; the **production defect is that the owner never
   supplies the required data**. i.e. the throw is not the bug — the absent data
   is.

No chunking change is proposed in S10-01.

---

## 6. Production vs Test-Mocked Path Audit

| Test file | Path exercised | Class |
|---|---|---|
| `tests/unit/adapters/test_epub_extraction_boundary.py` | extraction only | UNIT ONLY |
| `tests/integration/test_epub_extraction_e2e.py` | extraction → intake | PARTIAL INTEGRATION |
| `tests/contract/test_s2_epub_chunking.py` | chunking with **fabricated** offsets | UNIT ONLY (masking) |
| `tests/contract/test_s3_epub_runtime.py` | runtime with fabricated chunks | UNIT ONLY |
| `tests/contract/test_s4_epub_reader_chapter_map.py` | map with fabricated chunks | UNIT ONLY |
| `tests/contract/test_s5_epub_packaging.py` | packaging with fabricated chunks | UNIT ONLY |
| `tests/ui/test_epub_translation_launch.py` | **mocks `_build_epub_options`** | MOCKED PATH |
| `tests/ui/test_s8_03_output_policy.py` | **mocks `_build_epub_options`** | MOCKED PATH |
| `tests/ui/test_s8_04_gui_state_acceptance.py` | **mocks `_build_epub_options`** | MOCKED PATH |
| `tests/ui/test_s6_03_acceptance.py` | **mocks `EpubExtractionBoundary.extract`** with a result whose `body_start_offset=30`, and mocks packager + reader map | MOCKED PATH (fabricated offsets) |
| `tests/e2e/test_s9_07_epub_reader_flow.py` | **real extraction**; asserts `ValueError("body offsets")` | REAL PRODUCTION PATH (negative) |

Conclusion: There is **no positive test that runs extraction → chunking on the
real path**. Mocked/`_build_epub_options` and fabricated-offset tests must not be
read as production PASS. S9-07 is the only honest production-path assertion and
it documents the failure. → **GAP**.

---

## 7. UI Entry Audit

| Capability | Present | Evidence |
|---|---|---|
| EPUB import | YES | `project_page.add_project` + `test_epub_import_contract.py` |
| EPUB extraction/intake | YES | `_build_epub_options` step 1–3 |
| EPUB preview | YES | `preview_text` from extraction; `_on_selection_changed` |
| EPUB project persistence | YES | ReaderProject schema v1; `add_project` persists |
| EPUB project selection | YES | `test_a_epub_translate_button_enabled` |
| EPUB translation entry | PARTIAL | `_on_translate` → `_build_epub_options` routes correctly and does NOT fall back to TXT, but cannot complete (F1) |
| Project card / page | YES | `project_view_model.py`, `widgets/project_card.py` |
| Translation worker EPUB route | YES | workers detect `EpubTranslationOptions` and package |

Backend presence of `EpubTranslationOptions` and packaging is NOT equivalent to
reader-facing EPUB translation being implemented. Reader-facing EPUB translation
is **DEFERRED** pending F1.

---

## 8. TXT Regression Boundary

- TXT uses a separate options type (`TxtTranslationOptions`) and
  `TranslationRuntime.translate_txt` (`translation_worker.py:64-65`).
- `CanonicalBookIntakeAdapter.process_path` (TXT hash `sha256[:16]`) is untouched
  by the EPUB extraction repair.
- Proposed repair touches only `core/adapters/epub_extraction_boundary.py` (and,
  for S1, the EPUB metadata handoff). No shared TXT canonical route is modified.
- TXT Impact: **NONE**.

---

## 9. Runtime Boundary

- F1 is resolvable entirely in extraction → mapping → chunking input. It does NOT
  require changes to `TranslationEngine`, `RuntimeOrchestrator`,
  `ProviderManager`, `NvidiaTranslationProvider`, `NvidiaClient`, or the model
  `meta/llama-3.2-90b-vision-instruct`.
- Runtime Boundary: **PASS**. All stop conditions in §21 are avoided.

---

## 10. Output / Persistence / Source Identity / Security

- **Output contract.** Workers set `result["output"]` to the packaged EPUB
  (`<src.parent>/output/epub_translation/<id>/<stem>_zh.epub`). Dry-run returns
  `output=""` and does not package. Resume state is written separately
  (`<stem>_epub_resume_state.json`) and is NOT treated as the final artifact.
  Metadata/chapter/resource preservation inside packaging is structurally
  present (`epub_packager.py:862-1008`) but metadata fidelity is impaired by S1.
  → **DEFERRED** only on the metadata-preservation criterion; structure is sound.

- **Persistence.** `_persist_translation_result` writes `output.artifact_path`,
  `output_dir`, `artifact_kind = source.format`, `available = is_file()`
  (`project_page.py:861-866`); `execution.resume_state_path` is separate
  (`:860`). `_on_open_result` opens the persisted artifact
  (`:597-617`). ReaderProject schema v1 is unchanged. → **PASS**, no schema change
  required (body offsets already exist in the contract model).

- **Source identity.** `compute_source_identity` uses full `sha256` for EPUB,
  kind `epub_sha256` (`identity.py:77-79`), identical to
  `EpubExtractionResult.original_hash`. No new hash/PID/filename identity is
  introduced. → **PASS**.

- **Security.** `_validate_zip_security` blocks traversal, absolute/UNC paths,
  symlinks, duplicate canonical paths, executables, nested archives, zip bombs,
  encryption; `validate_epub` reuses it (`epub_extraction_boundary.py:277-332`).
  Repair must not relax this. → **PASS**, and repair does not touch it.

---

## 11. Deterministic Fixture Audit

- Existing: `tests/e2e/conftest.py::make_epub` — deterministic EPUB3, metadata,
  2 linear chapters, spine, nav TOC, one PNG resource. Sufficient to expose F1.
- Missing: a supplementary/non-linear spine fixture (for S3), and an integration
  test binding `make_epub` → extraction → intake → chunking.
- Fixture status: **PASS** (small deterministic fixture exists). New fixtures may
  be proposed in the Design but were NOT created in S10-01.

---

## 12. Root-Cause Classification

```
F1 = A. Extraction contract defect
First broken contract : EpubExtractionBoundary.chapter_map body offsets
Exact boundary        : core/adapters/epub_extraction_boundary.py:210-222
Why                   : body_start_offset/body_end_offset declared but always None;
                        chunking requires them (chunking.py:237-241) and refuses to derive.
Owner to fix          : EpubExtractionBoundary (extraction layer)
Contributing gaps     : G. Test coverage gap (no positive extraction→chunking test;
                        launch tests mock _build_epub_options; S6 acceptance mocks extract)
Secondary (separate)  : B. Intake metadata mapping defect (S1)
```

This is not simply "EPUB doesn't work": the first broken contract, the reason, and
the owning layer are all identified.

---

## 13. Stop Conditions

None triggered. The defect is solvable within extraction/intake/chunking-input
boundaries. No runtime/provider/model/schema/second-pipeline/security-relaxation
condition applies.

---

## 14. Acceptance Checklist (S10-01)

```
[x] Current HEAD verified as 4a539b8
[x] s9-complete verified
[x] Pre-existing literary residuals untouched
[x] F1 production root cause identified
[x] Extraction contract audited
[x] Chapter offsets audited
[x] Chapter identity audited
[x] Intake mapping audited
[x] Chunking contract audited
[x] Production vs mocked path distinguished
[x] UI entry path audited
[x] Runtime boundary audited
[x] Packaging contract audited
[x] Output contract audited
[x] Persistence contract audited
[x] Source identity audited
[x] Security boundary audited
[x] Test coverage audited
[x] Deterministic fixture status audited
[x] Minimal repair designed (see DESIGN artifact)
[x] TXT impact assessed (NONE)
[x] No schema change
[x] No provider change
[x] No runtime change
[x] No second pipeline
[x] No fake test route
[x] Glossary untouched
[x] Provider = 0
[x] Network = 0
[x] Real translation = 0
[x] No commit
[x] No push
[x] No tag
```
