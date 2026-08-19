# NTPE RM-8.3 Preflight ??Output Polish & Delivery Capability Audit

**Generated:** 2026-08-10
**Version:** rm-8.3.0-preflight
**Status:** COMPLETED

---

## 1. Git Baseline

### 1.1 Repository State

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	deleted:    RM_6_4_0_ACCEPTANCE_REPORT.md
	deleted:    RM_7_3_1_ACCEPTANCE_REPORT.md
	modified:   artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json
	modified:   artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json
	modified:   docs/governance/rm6/RM_6_4_3_CANARY_REPORT.md
	modified:   tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
	modified:   tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
	modified:   tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
	modified:   tests/literary/outputs/Regression_History.json
	modified:   tools/canary/run_canary.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	artifacts/rm7_entity_canary/
	knowledge/

no changes added to commit (use "git add" and/or "git commit -a")
```

### 1.2 Recent Commit History (main)

```
38fcf94 chore(rm7): restore repository hygiene
5783303 feat(rm7): integrate knowledge evolution learning loop
476890b feat(rm7): add entity review module
34ac584 feat(rm7): add form-aware entity consistency matching
34fb1d1 feat(rm7): add entity normalization runtime
c098b3c feat(rm7): add entity pre-translation resolver
8cf5fd3 feat(consistency): add entity consistency runtime
6077085 feat(knowledge): add knowledge evolution foundation
ab418fb RM-6.4.3 Production Canary Translation: Runtime Pipeline first novel translation validated
26fc98b feat(runtime): add production runtime pipeline switch
```

---

## 2. RM-8.1 / RM-8.2 Closure Confirmation

### 2.1 RM-8.1 (Literary Quality Enforcement) ??Status: SPECIFIED, NOT IMPLEMENTED

| Spec Document | `docs/governance/rm8/RM_8_1_IMPLEMENTATION_SPECIFICATION.md` |
|---------------|---------------------------------------------------------------|
| Status | Ready for implementation; zero behavior change; reuses existing `_NATURALNESS_PATTERNS` + `naturalness_guard_policy="literary_retry"` |
| Files to Modify | `core/translation_runtime/runtime_qa.py`, `core/adaptive_context_production_rollout/outcome.py`, `core/adaptive_context_production_rollout/quality_bridge.py`, `lts/txt_translation_runtime.py` (manifest only) |
| Non-Goals Locked | No new policy, no synthetic score, no new detectors, no LLM judge, no RM-8.2/8.3 scope |

### 2.2 RM-8.2 (Cross-Chunk Context Continuity) ??Status: SPECIFIED, NOT IMPLEMENTED

| Spec Document | `docs/governance/rm8/RM_8_2_IMPLEMENTATION_SPECIFICATION.md` |
|---------------|---------------------------------------------------------------|
| Preflight | `docs/governance/rm8/RM_8_2_PREFLIGHT_REPORT.md` ??80% infrastructure exists (models, selection, prompt slots); only extractors + wiring missing |
| Audit | `docs/governance/rm8/RM_8_2_PRE_IMPLEMENTATION_AUDIT.md` ??Authoritative file/class/call-site mapping |
| Feature Flag | `quality_context_scene_v72` (default OFF) in `TxtTranslationOptions` |
| Non-Goals Locked | No chunking modification, no RM-7 changes, no provider calls, no new dataclasses for context_state |

### 2.3 Validation Gates (Current ??All PASS)

```powershell
python ntpe_validate.py
# ALL PASS

python -m compileall core
# 0 errors

git diff --check
# Only pre-existing CRLF warnings, no new issues
```

---

## 3. Current Output & Delivery Architecture

### 3.1 Production Output Path (Current)

```
Translation Runtime (core/translation_runtime/ or lts/txt_translation_runtime.py)
        ??Chunk-by-chunk translation ??chunk files (artifacts/.../novel_sample_chunk_XXX_zh.txt)
        ??Post-translation processing (locked dict, formatting, canonicalization, QA)
        ??Simple concatenation: "\n\n".join(translated_chunks).strip() + "\n"
        ??Final output: output_dir/{input_stem}_zh.txt
        ??Manifest generation: output_dir/{input_stem}_translation_manifest.json
```

### 3.2 Existing Output Components

| Component | Location | Capability | Status |
|-----------|----------|------------|--------|
| **Chunk Writer** | `core/translation_runtime/runtime_output.py:8-11` | `write_text_output(path, text)` ??thin wrapper | ??Minimal |
| **JSON Writer** | `core/translation_runtime/runtime_output.py:14-17` | `write_json_output(path, payload)` ??thin wrapper | ??Minimal |
| **Formatter** | `core/translation_runtime/runtime_formatter.py` | Clean provider output, punctuation normalization, Taiwan traditional normalization | ??Complete, per-chunk |
| **Locked Dictionary** | `lts/txt_translation_runtime.py:287-300` | Post-translation term enforcement | ??Complete |
| **Canonicalization** | `core/translation_naturalness` | `canonicalize_novel_chinese()`, `apply_literary_collocation_guard()` | ??Per-chunk |
| **Manifest** | `lts/txt_translation_runtime.py:2406-2437` | Aggregates literary quality metrics, records, config | ??Complete |

### 3.3 Current Final Assembly (lines 960-965 in txt_translation_runtime.py)

```python
final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
if not options.dry_run and any(translated_chunks):
    final_text = "\n\n".join(translated_chunks).strip() + "\n"
    if options.strict_lock_terms and locked_dictionary:
        final_text = apply_locked_dictionary(final_text, locked_dictionary)
    save_text(final_output, final_text)
```

**Key Observation:** Final assembly is a naive double-newline join. No paragraph validation, no formatting consistency check, no metadata injection, no publication format generation.

---

## 4. Output Polish & Delivery Capability Inventory

### 4.1 Existing Capabilities (Reusable ??Class A)

| Capability | Location | Evidence | Reusable for RM-8.3 |
|------------|----------|----------|---------------------|
| **Per-chunk formatting** | `core/translation_runtime/runtime_formatter.py` | Punctuation, Taiwan traditional, cleanup | ??Yes ??apply to final assembly |
| **Locked dictionary enforcement** | `lts/txt_translation_runtime.py:287-300` | Post-translation alias + source replacement | ??Yes ??final pass |
| **Canonicalization** | `core/translation_naturalness` | `canonicalize_novel_chinese()`, `apply_literary_collocation_guard()` | ??Yes ??final pass |
| **Manifest generation** | `lts/txt_translation_runtime.py:2406-2437` | Structured JSON with literary quality aggregation | ??Extend for delivery metadata |
| **Resume state** | `lts/txt_translation_runtime.py:329-350` | Per-chunk SHA256 + status | ??Track delivery completion |
| **Live progress** | `lts/txt_translation_runtime.py:433-438` | JSON progress updates | ??Extend for delivery phase |

### 4.2 Partially Existing (Class B ??Needs Integration)

| Capability | Location | Gap |
|------------|----------|-----|
| **Quality V5 reports** | `tests/literary/outputs/PS-03-*/Literary_Quality_Report.json` | Manual evaluation only; no automated gate |
| **Discipline audit trail** | `lts/txt_translation_runtime.py:2146-2148` | Per-chunk; no final synthesis |
| **Character memory** | `memory/character_memory_lts.json` | Updated post-translation; not in final output |

### 4.3 Missing Capabilities (Class D ??True Gaps)

| Capability | Description | Evidence |
|------------|-------------|----------|
| **Post-assembly polish** | No stage runs after chunk concatenation | Current: join ??write ??done |
| **Paragraph validation** | No check for empty paragraphs, excessive breaks, inconsistent spacing | `format_translation_output()` is per-chunk only |
| **Format consistency gate** | No validation of punctuation consistency, quote style, paragraph structure across chunks | Each chunk formatted independently |
| **Metadata injection** | No title, author, chapter TOC, translation metadata in final output | Manifest is separate JSON only |
| **Publication formats** | No EPUB, PDF, HTML, Markdown generation | Zero implementation |
| **Final QA gate** | No automated validation of complete novel before delivery | Only per-chunk QA |
| **Delivery manifest** | No standardized delivery package (output + manifest + QC report) | Ad-hoc file layout |

---

## 5. Reader Outcome Audit

### 5.1 Current Reader Experience (From RM-8 Preflight Section 5)

| Dimension | Status | Evidence |
|-----------|--------|----------|
| **Coherent ÁπÅ‰∏≠Â∞èË™™** | PASS | `novel_sample_zh.txt` readable (3573 bytes, 3 chunks) |
| **No manual assembly needed** | PASS | Single output file produced |
| **No debug artifacts in output** | PASS | Clean translation text only |
| **Chapter structure preserved** | PASS | `---` separators maintained from source |

### 5.2 Reader Outcome Gaps (Publication-Ready Criteria)

| Criterion | Current Status | Gap |
|-----------|---------------|-----|
| **Consistent paragraph formatting** | UNKNOWN | No cross-chunk validation |
| **Unified punctuation style** | UNKNOWN | Per-chunk only |
| **Chapter/TOC navigation** | MISSING | No TOC generation |
| **Metadata (title, author, translator, date)** | MISSING | Not in output |
| **EPUB/PDF for reading devices** | MISSING | Zero implementation |
| **Quality certificate** | MISSING | No final QC report bundled |

---

## 6. RM-8.3 Scope Definition (Per RM-8 Preflight Section 14)

### 6.1 Proposed RM-8.3 Specification (from RM-8 Preflight)

| Field | Specification |
|-------|---------------|
| **Objective** | Add post-translation polish stage and final validation gate |
| **Reader Impact** | Publication-ready output (clean paragraphs, consistent formatting) |
| **Production Scope** | `core/translation_runtime/`, new `core/translation_release/` |
| **Allowed Files** | Polish pipeline; format validators; EPUB/PDF exporters (optional) |
| **Forbidden Files** | Core translation pipeline; Entity/KE modules |
| **Acceptance Criteria** | 1. Post-polish stage executes after assembly<br>2. Final validation gate (paragraphs, formatting, metadata)<br>3. Single deliverable artifact per novel |
| **Provider Requirement** | No |
| **Network Requirement** | No |
| **Evidence Requirement** | Before/after polish comparison; format validation report |
| **Regression Requirement** | All prior stages PASS |

### 6.2 Explicit Non-Goals (Locked for RM-8.3)

| Item | Reason |
|------|--------|
| ??**Chunking rule modifications** | `split_text()` is frozen; RM-8.2 explicitly forbids re-chunking |
| ??**Directory-based paragraph splitting** | No filesystem-based chunking; chunks are in-memory only |
| ??**RM-7 pipeline modifications** | Entity/consistency/review/KE remain CLOSED |
| ??**RM-8.1 literary quality enforcement** | Separate stage (RM-8.1); RM-8.3 consumes its metrics |
| ??**RM-8.2 cross-chunk context** | Separate stage (RM-8.2); RM-8.3 consumes its metadata |
| ??**New provider/LLM calls** | Zero network; offline polish only |
| ??**Auto-learning** | Violates Fail Closed principle |

---

## 7. Proposed RM-8.3 Architecture

### 7.1 Data Flow (Post RM-8.1/8.2 Integration)

```
All chunks translated (RM-7 pipeline + RM-8.1 quality + RM-8.2 context)
        ??Chunk files: artifacts/.../novel_sample_chunk_XXX_zh.txt
        ???å‚??Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä????                   RM-8.3 DELIVERY PIPELINE                     ???? core/translation_release/delivery_pipeline.py (NEW)           ???ú‚??Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä???? 1. ASSEMBLY                                                    ????    ??Read all chunk files in order                             ????    ??Join with double newline (existing)                       ????    ??Apply locked dictionary (final pass)                      ????    ??Apply canonicalization (final pass)                       ????                                                                ???? 2. POLISH (core/translation_release/polish.py) (NEW)          ????    ??Paragraph validation & normalization                      ????    ??Punctuation consistency across chunks                     ????    ??Quote style unification                                   ????    ??Empty paragraph removal / consolidation                   ????    ??Whitespace normalization                                  ????                                                                ???? 3. VALIDATION GATE (core/translation_release/validator.py)    ????    ??Paragraph count vs chunk count                            ????    ??No Korean residue (global check)                          ????    ??Locked term coverage (global)                             ????    ??Length ratio (global)                                     ????    ??Format consistency score                                  ????    ??Literary quality aggregate (from RM-8.1 metrics)          ????    ??PASS/FAIL with detailed report                            ????                                                                ???? 4. METADATA INJECTION (core/translation_release/metadata.py)  ????    ??Title, author, translator, date, model, pipeline version ????    ??Chapter TOC from scene/chapter markers (RM-8.2 metadata) ????    ??Quality certificate (RM-8.1 aggregate)                    ????    ??Generation manifest reference                             ????                                                                ???? 5. DELIVERY PACKAGE (core/translation_release/package.py)     ????    ??Primary: {novel}_zh.txt (polished)                       ????    ??Manifest: {novel}_delivery_manifest.json                 ????    ??QC Report: {novel}_quality_certificate.json              ????    ??Optional: EPUB/PDF via pluggable exporters               ???î‚??Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä?Ä??        ??Delivery artifacts in output_dir/
```

### 7.2 New Module Structure

```
core/
?ú‚??Ä translation_release/           # NEW DIRECTORY
??  ?ú‚??Ä __init__.py
??  ?ú‚??Ä delivery_pipeline.py       # Main orchestrator
??  ?ú‚??Ä polish.py                  # Post-assembly text polish
??  ?ú‚??Ä validator.py               # Final validation gate
??  ?ú‚??Ä metadata.py                # Metadata injection
??  ?ú‚??Ä package.py                 # Delivery package assembly
??  ?ú‚??Ä exporters/
??  ??  ?ú‚??Ä __init__.py
??  ??  ?ú‚??Ä base.py                # Exporter interface
??  ??  ?ú‚??Ä epub_exporter.py       # Optional EPUB
??  ??  ?î‚??Ä pdf_exporter.py        # Optional PDF
??  ?î‚??Ä models.py                  # Delivery dataclasses
?î‚??Ä translation_runtime/
    ?î‚??Ä runtime_output.py          # EXTEND: add delivery write helpers
```

---

## 8. Reusable Components Detail

### 8.1 Formatter (Runtime Formatter ??Final Polish)

```python
# core/translation_runtime/runtime_formatter.py ??EXISTING
def format_translation_output(text: str, *, enabled: bool = True,
                              taiwan_traditional_normalization: bool = True) -> str
```

**RM-8.3 Adaptation:** Create `core/translation_release/polish.py` that:
- Reuses `clean_provider_output()`, `normalize_punctuation_for_zh_tw()`, `normalize_taiwan_traditional()`
- Adds paragraph-level operations: `normalize_paragraphs()`, `unify_quote_style()`, `consolidate_whitespace()`
- Operates on **full novel text** (not per-chunk)

### 8.2 Locked Dictionary (Final Pass)

```python
# lts/txt_translation_runtime.py:287-300 ??EXISTING
def apply_locked_dictionary(text: str, locked_dictionary: dict[str, str]) -> str
```

**RM-8.3 Use:** Single final pass on assembled novel (catches any cross-chunk term drift).

### 8.3 Canonicalization (Final Pass)

```python
# core/translation_naturalness ??EXISTING
canonicalize_novel_chinese(text) -> CanonicalizationResult
apply_literary_collocation_guard(text) -> CollocationGuardResult
```

**RM-8.3 Use:** Single final pass on assembled novel.

### 8.4 Manifest Generation (Extended)

```python
# lts/txt_translation_runtime.py:2406-2437 ??EXISTING
manifest["literary_quality"] = {hits, errors, warnings, passed, issue_codes}
```

**RM-8.3 Extension:** Add delivery metadata, QC results, format validation scores.

---

## 9. Gap Analysis (What Must Be Built)

| # | Component | Description | Complexity | Dependencies |
|---|-----------|-------------|------------|--------------|
| 1 | `delivery_pipeline.py` | Orchestrates assembly ??polish ??validate ??metadata ??package | Medium | RM-8.1 metrics, RM-8.2 metadata |
| 2 | `polish.py` | Full-novel text polish (paragraphs, punctuation, quotes) | Medium | Reuses runtime_formatter |
| 3 | `validator.py` | Final QC gate with PASS/FAIL | Medium | Needs acceptance criteria |
| 4 | `metadata.py` | Inject title/author/TOC/quality cert | Low | RM-8.2 scene/chapter IDs |
| 5 | `package.py` | Write delivery artifacts | Low | Standard file ops |
| 6 | `models.py` | Delivery dataclasses | Low | None |
| 7 | Exporters (optional) | EPUB/PDF generation | High (optional) | External libs |

---

## 10. Acceptance Criteria (Minimum Verifiable)

| # | Gate | Verification |
|---|------|--------------|
| 1 | **Assembly executes** | All chunk files read in order; joined with `\n\n` |
| 2 | **Polish stage runs** | Before/after text differs (paragraphs normalized, quotes unified) |
| 3 | **Validation gate** | Returns PASS/FAIL with structured report; FAIL blocks delivery |
| 4 | **Metadata injected** | Output contains title, author, TOC, quality certificate |
| 5 | **Delivery package** | 3 files: `{novel}_zh.txt`, `{novel}_delivery_manifest.json`, `{novel}_quality_certificate.json` |
| 6 | **Regression** | All RM-7, RM-8.1, RM-8.2 tests PASS; canary produces valid delivery |
| 7 | **No provider calls** | Zero network requests in delivery pipeline |
| 8 | **Backward compatible** | Existing `translate_txt()` returns success; delivery is additive |

---

## 11. Test Strategy

| Test | Location | Scope |
|------|----------|-------|
| Unit: polish functions | `tests/unit/translation_release/test_polish.py` | Paragraph normalization, quote unification, whitespace |
| Unit: validator | `tests/unit/translation_release/test_validator.py` | QC gate logic, PASS/FAIL conditions |
| Integration: delivery pipeline | `tests/integration/test_delivery_pipeline.py` | End-to-end with fixture chunks |
| Golden master | `tests/acceptance/rm8_delivery_test.py` | Fixed input ??deterministic delivery output |
| Canary | `tools/canary/run_delivery_canary.py` | Real translation ??delivery package |

---

## 12. File Edit Summary (Minimal Set)

| File | Priority | Change Type |
|------|----------|-------------|
| `lts/txt_translation_runtime.py` | P0 | Add delivery pipeline invocation after final assembly (feature-gated) |
| `core/translation_runtime/runtime_output.py` | P1 | Add `write_delivery_package()` helper |
| `core/translation_release/delivery_pipeline.py` | P0 | NEW ??Main orchestrator |
| `core/translation_release/polish.py` | P0 | NEW ??Post-assembly polish |
| `core/translation_release/validator.py` | P0 | NEW ??Final QC gate |
| `core/translation_release/metadata.py` | P0 | NEW ??Metadata injection |
| `core/translation_release/package.py` | P0 | NEW ??Delivery artifact writer |
| `core/translation_release/models.py` | P0 | NEW ??Dataclasses |
| `core/translation_release/exporters/__init__.py` | P2 | NEW ??Optional exporters |
| Tests | P2 | NEW ??Unit + integration + acceptance |

---

## 13. Integration with RM-8.1 / RM-8.2

### 13.1 Consumes RM-8.1 (Literary Quality)

- Aggregates `literary_quality_*` metrics from all chunks (already in manifest lines 2389-2404)
- Includes in quality certificate
- Uses `literary_quality_passed` as validation gate input

### 13.2 Consumes RM-8.2 (Cross-Chunk Context)

- Reads `scene_id`, `chapter_id` from chunk metadata (RM-8.2 `context_state_metadata`)
- Generates chapter TOC for metadata injection
- Uses `scene_version` for continuity certificate

### 13.3 Feature Flag

```python
# In TxtTranslationOptions (ADD)
quality_delivery_v83: bool = False  # Default OFF
quality_delivery_formats_v83: tuple[str, ...] = ("txt",)  # "epub", "pdf" optional
```

---

## 14. Compliance Checklist

| Principle | Addressed By |
|-----------|--------------|
| No production code modification (preflight) | ??Report only; no implementation |
| No chunking modification | ??Explicitly forbidden in non-goals |
| No directory-based paragraph splitting | ??Explicitly forbidden in non-goals |
| No RM-7 modification | ??Entity/KE modules forbidden |
| No provider/network calls | ??Zero network requirement |
| Reuses existing formatters | ??`runtime_formatter.py` functions |
| Reuses locked dictionary | ??Final pass on assembled text |
| Reuses canonicalization | ??Final pass on assembled text |
| Extends manifest (not replace) | ??Additive delivery metadata |
| Feature-gated | ??`quality_delivery_v83` default OFF |

---

## 15. Final Validation

```powershell
python -m compileall core
# 0 errors

python ntpe_validate.py
# ALL PASS

git diff --check
# Only pre-existing CRLF warnings

git status --short
# No new production code changes
```

---

## 16. Artifacts

| Artifact | Path |
|----------|------|
| RM-8.3 Preflight Report | `docs/governance/rm8/RM_8_3_PREFLIGHT_REPORT.md` |
| RM-8 Preflight (parent) | `docs/governance/rm8/RM_8_PREFLIGHT_REPORT.md` |
| RM-8.1 Spec | `docs/governance/rm8/RM_8_1_IMPLEMENTATION_SPECIFICATION.md` |
| RM-8.2 Spec | `docs/governance/rm8/RM_8_2_IMPLEMENTATION_SPECIFICATION.md` |
| RM-8.2 Preflight | `docs/governance/rm8/RM_8_2_PREFLIGHT_REPORT.md` |
| RM-8.2 Audit | `docs/governance/rm8/RM_8_2_PRE_IMPLEMENTATION_AUDIT.md` |

---

## 17. Final Verdict

**RM-8.3 PREFLIGHT ??PASS**

All 8 PASS conditions satisfied:

| # | Question | Answer |
|---|----------|--------|
| 1 | RM-7 CLOSED? | **YES** ??4 acceptance reports; closed loop verified |
| 2 | RM-8.1 Specified? | **YES** ??Implementation spec complete; ready for implementation |
| 3 | RM-8.2 Specified? | **YES** ??Implementation spec complete; preflight + audit done |
| 4 | Output architecture documented? | **YES** ??Current pipeline mapped; components inventoried |
| 5 | Reusable components identified? | **YES** ??Formatter, locked dict, canonicalization, manifest |
| 6 | Gaps clearly classified? | **YES** ??Class A (reuse), B (integrate), D (build) |
| 7 | Reader outcome gaps known? | **YES** ??Publication-ready criteria vs current state |
| 8 | Explicit non-goals locked? | **YES** ??Chunking, directory-splitting, RM-7, provider calls |

---

## 18. Next Step

**Await review of this RM-8.3 Preflight Report.**

Upon approval ??Produce **RM-8.3 Implementation Specification** with:
1. Exact function signatures for `delivery_pipeline.py`, `polish.py`, `validator.py`, `metadata.py`, `package.py`
2. `DeliveryManifest` and `QualityCertificate` dataclasses
3. Integration point in `lts/txt_translation_runtime.py` (feature-gated)
4. Acceptance test specification with golden master
5. File edit list with line references

**No production code changes until Specification is reviewed and approved.**

---

*End of RM-8.3 Preflight Report*
