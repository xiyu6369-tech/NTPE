# NTPE RM-8.5 Requirements / Architecture Inventory

**Baseline**: RM-8.3 (d901c92), RM-8.4 final commit (e4af617), main branch  
**Date**: 2026-08-13  
**Status**: Comprehensive inventory against actual repository and existing RM-8.x specifications

---

## 1. Current NTPE Capability Inventory

### 1.1 RM-8.1: Literary Quality Enforcement (IMPLEMENTED, ACCEPTED)

**Scope**: Formalize existing literary quality detection via `_NATURALNESS_PATTERNS` → explicit metrics propagation.

**Files Modified**:
- `core/translation_runtime/runtime_qa.py`: `classify_literary_quality_hits()`, extended `analyze_runtime_quality()` metrics
- `core/adaptive_context_production_rollout/outcome.py`: 5 new `ProductionOutcome` fields
- `core/adaptive_context_production_rollout/quality_bridge.py`: Metrics propagation
- `lts/txt_translation_runtime.py`: Manifest includes `literary_quality` block

**Runtime/Data Structures**:
- `_LITERARY_QUALITY_CODES = {"NATURALNESS_PERSON_HUMAN_WORLD", "NATURALNESS_BREATH_ACTION", "NATURALNESS_REDUNDANT_COUNTING", "NATURALNESS_TOURIST_PERSON", "NATURALNESS_OVERLITERAL_ENTANGLED"}`
- QA Report metrics: `literary_quality_hits`, `literary_quality_errors`, `literary_quality_warnings`, `literary_quality_passed`, `literary_quality_issue_codes`
- ProductionOutcome fields: same 5 metrics
- Manifest: `"literary_quality": {"hits": 3, "errors": 1, "warnings": 2, "passed": false, "issue_codes": [...]}`

**Policy Matrix** (unchanged from pre-RM-8.1):
| Policy / Profile | Hits | Errors | Warnings | Passed | Chunk Saved |
|---|---:|---:|---:|---|---|
| `off` | 2 | 0 | 0 | true | Yes |
| `warn` + literary | 2 | 0 | 2 | true | Yes |
| `literary_retry` + literary | 2 | 2 | 0 | false | No (qa_fail≠warn) |
| `literary_retry` + non-literary | 2 | 0 | 2 | true | Yes |
| `fail` | 2 | 2 | 0 | false | No |

**Key Property**: Detection ≠ Enforcement. Metrics always reflect detection; `passed` reflects enforcement outcome.

---

### 1.2 RM-8.2: Cross-Chunk Context Continuity (IMPLEMENTED, ACCEPTED)

**Scope**: Attach Scene/Chapter metadata to chunks; propagate context state N→N+1; token-budgeted selection; checkpoint/resume.

**Files Modified**:
- `core/translation_runtime/boundary_detector.py`: **NEW** — conservative explicit-marker detection
- `core/context_scene_memory/*`: Store, selection, scene_state, models, serialization (existing, wired in)
- `core/intelligence/narrative_engine.py`: `analyze_chunk()`, `get_context_for_prompt()`, checkpoint persistence
- `core/prompt_runtime/builder.py`: Feature-gated `enable_cross_chunk_context`
- `core/prompt_runtime/sections.py`: New `build_context_selection()`, parameterized `build_character`, `build_scene`, `build_narrative`
- `core/runtime_orchestrator/manager.py`: Extended `execute()` metadata pass-through
- `lts/txt_translation_runtime.py`: Chunk loop integration (feature-gated `quality_context_scene_v72`)

**Runtime/Data Structures**:
- `BoundaryResult {type: BoundaryType, scene_id, chapter_id, confidence, metadata}`
- `BoundaryType`: `SAME_SCENE`, `SCENE_TRANSITION`, `CHAPTER_TRANSITION`, `UNKNOWN_TRANSITION`
- `ContextSelectionResult {selected_records, selected_chars, estimated_tokens, fingerprint, ...}`
- `SceneMemoryRecord {scene_id, scene_version, chapter_id, location, time_state, participants, ...}`
- `NarrativeState {perspective, voice, tense, emotional_tone, scene_history, counters}`
- Per-chunk `metadata.context_state`: `{context_selection_fingerprint, scene_id, scene_version, narrative, boundary, selected_context_ids}`

**Conservative Boundary Detection** (explicit markers only):
- Chapter: `제N장`, `第N章`, `Chapter N`
- Scene: `제N절`, `第N節`, `Scene N`, `***`/`---`/`===`
- Heuristics (location/time/speaker) → `UNKNOWN_TRANSITION` only, no auto scene_id

**Checkpoint/Resume**: `ContextMemoryStore.to_dict()/from_dict()`, `NarrativeState.to_dict()/from_dict()`, scene/chapter IDs + prev_chunk_text in checkpoint metadata.

**Feature Flag**: `quality_context_scene_v72` default OFF → zero regression when disabled.

---

### 1.3 RM-8.3: Output Polish & Delivery (IMPLEMENTED)

**Scope**: Post-assembly polish, validation gate, metadata injection, delivery package (TXT + manifest + QC cert), optional EPUB/PDF.

**Files Implemented**:
- `core/translation_release/polish.py`: `normalize_paragraphs()`, `unify_quote_style()`, `polish_full_novel()`
- `core/translation_release/validator.py`: `validate_final_novel()` — 9 deterministic checks
- `core/translation_release/metadata.py`: `build_toc_from_chunk_records()`, `inject_metadata_into_text()`, `generate_delivery_manifest()`, `generate_quality_certificate()`
- `core/translation_release/package.py`: `write_txt_delivery()`, `write_json_delivery()`, `write_delivery_package()`
- `core/translation_release/delivery_pipeline.py`: `run_delivery_pipeline()` orchestrator
- `core/translation_release/exporters/epub_exporter.py`, `pdf_exporter.py`: Optional exporters
- `core/translation_release/models.py`: `DeliveryManifest`, `QualityCertificate`, `DeliveryResult`, `TOCEntry`
- `lts/txt_translation_runtime.py`: Integration via `quality_delivery_v83` flag

**Polish Pipeline** (full-novel scope):
1. `clean_provider_output()` — preamble removal, line ending normalization
2. `normalize_paragraphs()` — empty paragraph removal, 3+ newline consolidation, whitespace normalization
3. `unify_quote_style()` — conservative ASCII quote → CJK corner bracket conversion (apostrophes/measurements/code protected)
4. `normalize_punctuation_for_zh_tw()` — ASCII → CJK punctuation
5. `normalize_taiwan_traditional()` — Simplified → Traditional Chinese
6. `clean_provider_output()` — final cleanup

**Validation Gate** (9 checks, weighted scoring, PASS ≥ 70 + no critical failures):
| Check | Severity | Key Criteria |
|---|---|---|
| paragraph_structure | critical | No empty paragraphs, no 3+ newlines, count > 0 |
| punctuation_consistency | major | CJK ratio > 95%, quote style unified |
| korean_residue_global | critical | Korean chars < max_korean_chars × chunks × 0.5 |
| locked_term_compliance | major | Only matched terms validated; no glossary-only failures |
| length_ratio_global | major | Translated/source ∈ [min_ratio, 2.0] (source from chunk_records) |
| chinese_char_ratio | minor | Chinese char ratio > 80% |
| repeated_lines_global | minor | No consecutive duplicate lines |
| quote_balance | minor | Corner brackets balanced |
| empty_content | info | Non-empty text |

**Delivery Package** (core, always):
- `{novel}_zh.txt` — polished text with metadata header + TOC
- `{novel}_delivery_manifest.json` — full pipeline metadata
- `{novel}_quality_certificate.json` — QC results + dimension scores

**Optional EPUB/PDF** (graceful fallback, non-blocking):
- EPUB: `ebooklib` dependency, 1 chapter = 1 XHTML document, nav.xhtml + NCX
- PDF: `reportlab` dependency, basic pagination

**Feature Flag**: `quality_delivery_v83` default OFF; `quality_delivery_formats_v83` = `("txt",)` default.

---

### 1.4 RM-8.4: Reader Structure / Optional EPUB Packaging (IMPLEMENTED)

**Scope**: Deterministic chapter mapping from RM-8.3 TXT body + RM-8.2 metadata → `ReaderChapterMap`; optional EPUB packaging driven by map.

**Core (Required)**:
- `core/translation_release/reader_structure/models.py`: `ChapterBoundary`, `ReaderChapterMap` (frozen dataclasses)
- `core/translation_release/reader_structure/chapter_mapper.py`: `build_reader_chapter_map()` — **read-only**, computes 0-based UTF-8 code point offsets
- `core/translation_release/reader_structure/epub_packager.py`: `pack_epub()` — slices by `ReaderChapterMap` positions

**Chapter Provenance** (single source, priority order):
1. RM-8.2 `context_state.boundary.chapter_id` (deterministic, already exists)
2. Explicit marker in TXT: `第N章`, `Chapter N` (fallback only)
3. Deterministic fallback: `chapter_N`

**Position Mapping**:
- `start_position` / `end_position` = offsets in RM-8.3 TXT body (excludes metadata header/TOC)
- 0-based, end-exclusive, UTF-8 code points
- Deterministic: same input → same positions

**Content Preservation Invariant**:
```
join(EPUB_chapter_texts) == RM-8.3_TXT_body
```
Verified by construction: chapters slice the body by positions.

**Validation Gates**:
- **Core Critical**: content_preservation, chapter_completeness, chapter_uniqueness, position_integrity, first_chapter_starts_at_zero, last_chapter_ends_at_body_length
- **EPUB Critical** (only when requested): epub_chapter_count==map_count, epub_boundaries_from_map, no_overlap, no_gap, content_preservation, no_provider_network

**Core/Optional Boundary**:
| Layer | Classification | Failure Blocks Core? |
|---|---|---|
| Chapter Mapper + ReaderChapterMap + QC | **Core** | Yes |
| EPUB Packaging | **Optional EPUB Packaging** | No (graceful fallback) |
| PDF Packaging | **Truly Optional** | No |

**CLI Separation**:
- `quality_delivery_v83=True` → Core delivery (includes ReaderChapterMap)
- `--export-epub` → Optional EPUB (requires Core first)
- `--export-pdf` → Optional PDF

---

### 1.5 Existing Quality/Continuity/Character/Glossary/Prompt/Delivery/Reader Capabilities

| Capability | Location | Status |
|---|---|---|
| Literary quality detection (6 patterns) | `context_intelligence.py:_NATURALNESS_PATTERNS` | ✅ Stable |
| Literary quality classification/metrics | `runtime_qa.py:classify_literary_quality_hits()` | ✅ RM-8.1 |
| Naturalness guard policies | `RuntimeQAPolicy.naturalness_guard_policy` | ✅ Pre-existing |
| Cross-chunk context store | `ContextMemoryStore` + `SceneMemoryRecord` | ✅ RM-8.2 |
| Token-budgeted context selection | `select_context_for_translation()` | ✅ RM-8.2 |
| Narrative intelligence engine | `NarrativeIntelligenceEngine` | ✅ RM-8.2 (Stage 16.2) |
| Prompt section injection (Context/Scene/Narrative/Character) | `prompt_runtime/sections.py` | ✅ RM-8.2 |
| Checkpoint/resume with context | `RuntimeCheckpointManager` + metadata snapshots | ✅ RM-8.2 |
| Locked dictionary enforcement | `apply_locked_dictionary()` + aliases | ✅ Pre-existing |
| Canonicalization/collocation guard | `canonicalize_novel_chinese()`, `apply_literary_collocation_guard()` | ✅ Pre-existing |
| Per-chunk formatting | `runtime_formatter.py` | ✅ Pre-existing |
| Full-novel polish | `translation_release/polish.py` | ✅ RM-8.3 |
| Deterministic validation gate | `translation_release/validator.py` | ✅ RM-8.3 |
| Metadata injection + TOC | `translation_release/metadata.py` | ✅ RM-8.3 |
| Delivery package (TXT/manifest/QC) | `translation_release/package.py` | ✅ RM-8.3 |
| Chapter boundary mapping | `reader_structure/chapter_mapper.py` | ✅ RM-8.4 |
| EPUB packaging (1 chapter = 1 doc) | `reader_structure/epub_packager.py` | ✅ RM-8.4 |
| Production runtime switch | `NTPE_RUNTIME_PIPELINE=runtime\|legacy` | ✅ RM-6.4.2 |

---

## 2. Reader-Facing Gap Analysis

**Perspective**: Ordinary reader who may not understand Korean, may not understand original novel structure, should be able to import an unfamiliar novel, should receive a readable, coherent, consistent Traditional Chinese novel.

### 2.1 What Works Today (RM-8.1 through 8.4)

| Reader Need | Current Solution |
|---|---|
| Single output file | `{novel}_zh.txt` with metadata header + TOC |
| Chapter navigation | TOC in TXT; `ReaderChapterMap` for EPUB nav |
| No Korean residue | Global QC gate (`korean_residue_global` critical) |
| Consistent formatting | Full-novel polish (paragraphs, punctuation, quotes) |
| Term consistency | Locked dictionary + alias normalization (global validation) |
| EPUB for reading devices | Optional EPUB (1 chapter = 1 document, nav.xhtml) |
| Quality assurance | QC certificate with dimension scores |

### 2.2 Remaining Reader-Facing Gaps

| Gap | Evidence | Impact |
|---|---|---|
| **No glossary/character reference in output** | TXT/EPUB contain only novel text; no appended glossary, character list, or pronunciation guide | Reader cannot look up unfamiliar terms/names |
| **No reading progress / bookmark sync** | EPUB has nav but no reading position persistence across devices | Reader loses place |
| **No alternative reading formats** | Only TXT + optional EPUB/PDF | Mobile/web readers may prefer HTML, MOBI, or web reader |
| **No inline annotations/footnotes** | Korean cultural terms, honorifics, idioms translated inline without explanation | Reader misses nuance |
| **No "first chapter free" / sample generation** | Full novel only | Cannot preview before committing |
| **No bilingual/parallel text option** | Source Korean completely removed | Learners cannot cross-reference |
| **No audio/TTS preparation** | No SSML markup, no chapter-level audio segmentation hints | TTS readers get poor prosody at boundaries |
| **No reading statistics** | No word count, estimated reading time, chapter length info in metadata | Reader cannot plan reading sessions |

---

## 3. Translation-Quality Gap Analysis

**Problems NOT already solved by RM-8.1–8.4:**

| Quality Problem | Current Coverage | Remaining Gap |
|---|---|---|
| **Cross-chunk pronoun resolution accuracy** | RM-8.2 propagates Scene/Narrative state; tests verify infrastructure NOT semantic accuracy | Pronouns (他/她/您/這裡/那裡) may still flip at boundaries |
| **Dialogue speaker attribution consistency** | RM-8.2 tracks `active_speaker` in SceneMemoryRecord; not validated end-to-end | Speaker names may drift across chunks |
| **Narrative POV stability** | RM-8.2 `NarrativeState.perspective` propagated; not validated | POV may shift unintentionally mid-scene |
| **Term consistency for non-locked terms** | Only `locked_dictionary` enforced globally; glossary terms not in locked_dict unchecked | Character names, place names, faction terms may vary |
| **Tense/voice consistency** | RM-8.2 `NarrativeState.tense/voice` tracked; no validation gate | Past/present mix, formal/casual voice drift |
| **Emotional tone continuity** | RM-8.2 `emotional_tone` tracked; no cross-chunk validation | Tone shifts at scene boundaries |
| **Cultural nuance preservation** | No dedicated detector; relies on literary patterns only | Honorifics, speech levels, idioms may be flattened |
| **Name transliteration consistency** | Only locked terms; Korean→Chinese name variants unchecked for non-locked | Same character rendered differently across chapters |
| **Sentence-level flow across chunk boundaries** | Per-chunk QA only; no cross-chunk flow check | Abrupt transitions, repeated/redundant content at joins |
| **Long-range entity consistency** | RM-7 entity resolution per-chunk; RM-8.2 context selection limited by token budget | Entities beyond token budget lose consistency |

**RM-8.2 Acceptance Report explicitly states** (§5): *"已驗證跨 Chunk 的 NarrativeState、SceneState、Context selection、Prompt injection 與 checkpoint/resume propagation；reader-outcome continuity tests 驗證狀態延續基礎設施，但不等同於完整語意層面的翻譯正確性。"*

---

## 4. Architecture Gap Analysis

### 4.1 Missing Capabilities

| Missing Capability | Layer | Evidence |
|---|---|---|
| **Cross-chunk semantic validation** | Quality | RM-8.2 infrastructure exists but no semantic QC gate |
| **Global term consistency (beyond locked_dict)** | Quality/Entity | RM-7 per-chunk only; no novel-wide consistency check |
| **Pronoun/speaker/POV/tense validation** | Quality | NarrativeState propagated but never verified |
| **Reader reference appendices (glossary, characters)** | Delivery | RM-8.3/8.4 output only novel text |
| **Bilingual/parallel output option** | Delivery | Source text discarded after translation |
| **Reading progress / annotation layer** | Reader | EPUB has nav only |
| **Audio/TTS-ready markup** | Delivery | No SSML, no prosody hints |
| **Sample/preview generation** | Delivery | Full novel only |

### 4.2 Duplicated Capabilities

| Duplication | Location | Assessment |
|---|---|---|
| **Paragraph normalization** | `runtime_formatter.py:clean_provider_output()` (per-chunk) AND `polish.py:normalize_paragraphs()` (full-novel) | Intentional: per-chunk cleanup + final consolidation. Acceptable. |
| **Quote normalization** | `runtime_formatter.py:normalize_punctuation_for_zh_tw()` (per-chunk) AND `polish.py:unify_quote_style()` (full-novel) | Per-chunk is lossy; full-novel is conservative. Acceptable. |
| **Taiwan traditional normalization** | `runtime_formatter.py` + `txt_translation_runtime.py` (per-chunk) AND `polish.py` (full-novel) | Double application (intentional per spec). Acceptable. |
| **Locked dictionary application** | Per-chunk + final assembly + delivery pipeline (3×) | Defensive; alias map ensures idempotency. Acceptable. |
| **Chapter boundary detection** | `boundary_detector.py` (runtime) AND `chapter_mapper.py` (post-hoc) | Runtime uses explicit markers; mapper uses RM-8.2 metadata + TXT fallback. Different purposes. Acceptable. |

### 4.3 Dangerous Coupling

| Coupling | Risk | Evidence |
|---|---|---|
| **`txt_translation_runtime.py` imports `translation_release` modules** | Circular import risk; delivery pipeline coupled to runtime internals | Lazy import used (`# RM-8.3 Delivery import is lazy`), but tight coupling remains |
| **`delivery_pipeline.py` calls `canonicalize_novel_chinese`/`apply_literary_collocation_guard`** | Re-runs canonicalization on already-canonicalized text | Defensive but duplicates work; spec says "reuse existing" |
| **`chapter_mapper.py` reimplements assembly logic** (`_assemble_txt_body`, `_compute_chunk_positions`) | Must stay perfectly in sync with `txt_translation_runtime.py` assembly | Spec requires exact replication; `skip_assembly_validation` flag acknowledges drift risk |
| **`epub_packager.py` duplicates chapter title extraction** (`_extract_chapter_title` vs `chapter_mapper.py:_extract_chapter_title_from_text`) | Divergence risk | Both use same regex but separate implementations |
| **`NarrativeIntelligenceEngine` state not fully checkpointed** | `counters` dict checkpointed but internal `pipeline`/`event_bus` not | Spec §6.3 verifies `to_dict/from_dict` exist but `restore_state_from_checkpoint` only restores `NarrativeState` |

### 4.4 Unnecessary Complexity

| Complexity | Why Unnecessary |
|---|---|
| **Three-tier quality profile system** (`quality_profile` + `naturalness_guard_policy` + `quality_v5_enabled`) | Overlapping controls; `literary_retry` only activates for specific profile+policoy combos |
| **`quality_context_scene_v72` + `quality_character_memory_v72` + `quality_integration_v72`** | Multiple feature flags for related RM-8.2 capabilities; could be unified |
| **Per-chunk AND full-novel polish** | Two-pass formatting with overlapping operations; spec mandates both |
| **Separate `chapter_mapper.py` assembly replication** | Could compute positions during RM-8.3 assembly instead of post-hoc reconstruction |
| **`matched_terms` computation duplicated** | In `delivery_pipeline.py:_compute_matched_locked_terms` and `txt_translation_runtime.py:collect_matched_locked_terms` |

---

## 5. Performance / Stability Analysis

### 5.1 Translation Efficiency

| Area | Current | Opportunity |
|---|---|---|
| **Provider request batching** | Sequential per-chunk | No batching; each chunk = 1 request |
| **Prompt token budget management** | Fixed budgets (512 context / 256 character) | Dynamic budget based on chunk complexity |
| **Retry loops** | Up to `max_retries` (default 3) × provider attempts | Exponential backoff + model fallback; can burn time on degraded models |
| **Context selection overhead** | Full store scan per chunk | Incremental index / caching |
| **Canonicalization/polish duplication** | Per-chunk + full-novel (2-3 passes) | Single full-novel pass if per-chunk formatting removed |

### 5.2 Runtime Stability

| Risk | Evidence |
|---|---|
| **Provider degradation fast-fail** | TER-v2.1/2.4 implements fast-fail for degraded/timeouts, but only when `NTPE_FALLBACK_MODELS` configured |
| **Checkpoint corruption** | `ContextMemoryStore.from_dict` validates schema but `snapshot_version` not cross-checked |
| **Resume state drift** | `prev_chunk_text` in checkpoint enables boundary detection continuity, but `translated_chunks[-1]` used for narrative analysis may differ if resume skips chunks |
| **Memory growth** | `ContextMemoryStore` accumulates all contexts + history; no TTL/eviction for long novels |
| **Token budget overflow** | `select_context_for_translation` drops over-budget items silently; no warning in metrics |

### 5.3 Provider Usage Efficiency

| Metric | Current |
|---|---|
| **Requests per novel** | = chunk count (no batching, no caching) |
| **Retry multiplier** | Up to 3× per chunk on failure |
| **Fallback model usage** | Only via `NTPE_FALLBACK_MODELS` env var |
| **Context tokens per request** | ~512 (context) + 256 (character) + system + chunk + other sections |

### 5.4 Memory / Storage Efficiency

| Component | Growth Pattern |
|---|---|
| `ContextMemoryStore.contexts` | O(chunks × context_types) — unbounded |
| `ContextMemoryStore.context_history` | Full history retained — unbounded |
| `SceneMemoryRecord` | O(scenes) — bounded by explicit markers |
| Checkpoint snapshots | Full store serialization per checkpoint — O(chunks²) potential |
| Chunk artifact files | 1 file per chunk — preserved for resume |

### 5.5 Large-Novel Handling

| Challenge | Current Status |
|---|---|
| **1000+ chunks** | Context store memory grows linearly; checkpoint size grows |
| **Token budget pressure** | Fixed 512/256 budgets; long novels exceed selection capacity |
| **Checkpoint I/O** | Full store snapshot per checkpoint; slow for large stores |
| **EPUB generation** | Single `ebooklib` book with all chapters; memory scales with novel size |
| **Validation gate** | Full-text scans (Korean residue, punctuation ratio) — O(n) acceptable |

---

## 6. Candidate RM-8.5 Directions

Only directions supported by repository evidence.

### Candidate A: Cross-Chunk Semantic Quality Gate

| Aspect | Detail |
|---|---|
| **Problem** | RM-8.2 propagates narrative/scene state but no validation that pronouns, speakers, POV, tense, emotional tone remain consistent across chunks. RM-8.2 acceptance report explicitly states semantic correctness NOT verified. |
| **Existing Capability** | `NarrativeState` (perspective, voice, tense, emotional_tone), `SceneMemoryRecord` (active_speaker, participants), `ContextSelectionResult` (selected context records), checkpoint/restore |
| **Missing Capability** | Deterministic validation checks on final assembled novel: pronoun consistency, speaker attribution stability, POV/tense/voice continuity, emotional tone coherence, cross-chunk entity consistency |
| **Expected Quality Benefit** | Catches semantic drift that per-chunk QA misses; directly improves reader experience |
| **Expected Performance Benefit** | None (adds validation pass); may reduce provider retries by catching issues earlier |
| **Complexity** | Medium — new validation checks in `validator.py` style, consuming existing RM-8.2 metadata |
| **Risk** | False positives if heuristics imperfect; must be conservative (warning not error) |
| **Dependencies** | RM-8.2 metadata in chunk_records; RM-8.3 validator framework |
| **Core/Optional** | **Core** — quality gate is core delivery requirement |

### Candidate B: Global Term Consistency (Beyond Locked Dictionary)

| Aspect | Detail |
|---|---|
| **Problem** | Only `locked_dictionary` terms enforced globally. Glossary terms, character names, place names, faction terms not in locked_dict vary across chapters. RM-7 entity resolution is per-chunk; RM-8.2 context selection limited by token budget. |
| **Existing Capability** | `ContextMemoryStore` with `TERMINOLOGY_STATE` contexts, `EntityResolver` (RM-7), glossary files, character memory |
| **Missing Capability** | Novel-wide term consistency validation: collect all terminology contexts → verify consistent translation across all occurrences → report violations |
| **Expected Quality Benefit** | Eliminates name/term drift for non-locked but important terms |
| **Expected Performance Benefit** | None (validation only); may reduce manual review |
| **Complexity** | Medium — terminology extraction from context store + cross-reference validation |
| **Risk** | Over-enforcement on legitimately polysemous terms; needs allowlist/override mechanism |
| **Dependencies** | RM-7 entity/glossary pipeline; RM-8.2 context store |
| **Core/Optional** | **Core** — consistency is core quality requirement |

### Candidate C: Reader Reference Appendices (Glossary, Characters, Pronunciation)

| Aspect | Detail |
|---|---|
| **Problem** | Output TXT/EPUB contains only novel text. Reader has no glossary, character list, pronunciation guide, or cultural notes. |
| **Existing Capability** | `locked_dictionary`, glossary files, character memory, `ContextMemoryStore` terminology contexts, `build_toc_from_chunk_records` |
| **Missing Capability** | Appendix generation: glossary appendix (source→target), character appendix (name + description + aliases), pronunciation guide (Korean names → zhuyin/pinyin), cultural notes |
| **Expected Quality Benefit** | Reader can look up unfamiliar terms; improves accessibility for non-Korean readers |
| **Expected Performance Benefit** | None (post-processing only) |
| **Complexity** | Low-Medium — data already exists; formatting/appendix injection needed |
| **Risk** | Appendix size; must be optional and not modify novel text (Source of Truth invariant) |
| **Dependencies** | RM-8.3 delivery pipeline; RM-8.4 ReaderChapterMap for chapter-aligned appendices |
| **Core/Optional** | **Optional** — reader enhancement, not quality requirement |

### Candidate D: Bilingual / Parallel Text Output Option

| Aspect | Detail |
|---|---|
| **Problem** | Source Korean text discarded after translation. Learners/researchers cannot cross-reference. |
| **Existing Capability** | `chunk_records` contain `source.chunk_text`; assembly logic in `txt_translation_runtime.py` |
| **Missing Capability** | Optional parallel output: interleaved Korean/Chinese paragraphs, or side-by-side EPUB, or separate source file with alignment markers |
| **Expected Quality Benefit** | Enables learning, verification, academic use |
| **Expected Performance Benefit** | None |
| **Complexity** | Low — data already in chunk_records; formatting only |
| **Risk** | Doubles output size; must be strictly optional, never modify Source of Truth |
| **Dependencies** | RM-8.3 delivery pipeline |
| **Core/Optional** | **Optional** — niche use case |

### Candidate E: Audio/TTS-Ready Markup (SSML, Prosody Hints)

| Aspect | Detail |
|---|---|
| **Problem** | EPUB/TXT have no prosody markup. TTS readers produce flat narration at chapter/scene boundaries. |
| **Existing Capability** | RM-8.2 `SceneMemoryRecord` (location, time_state, active_speaker, POV), `NarrativeState` (emotional_tone, voice), `ReaderChapterMap` boundaries |
| **Missing Capability** | SSML generation: `<prosody>` tags for emotional tone, `<break>` at scene boundaries, speaker voice hints, paragraph-level pacing |
| **Expected Quality Benefit** | Natural TTS narration; accessibility for visually impaired |
| **Expected Performance Benefit** | None |
| **Complexity** | Medium — requires SSML exporter, voice mapping, prosody heuristics |
| **Risk** | SSML not universally supported; EPUB 3 media overlays complex |
| **Dependencies** | RM-8.4 EPUB packager; RM-8.2 narrative/scene metadata |
| **Core/Optional** | **Optional** — accessibility enhancement |

### Candidate F: Translation Efficiency & Stability Improvements

| Aspect | Detail |
|---|---|
| **Problem** | Sequential provider requests, no batching, duplicate polish passes, unbounded context store growth, checkpoint I/O scales poorly. |
| **Existing Capability** | `RuntimeOrchestrator`, `ContextMemoryStore`, `RuntimeCheckpointManager`, `RuntimeSpeedPolicy` |
| **Missing Capability** | Request batching (multiple chunks per provider call), incremental context indexing, single-pass polish, checkpoint delta encoding, memory-bounded context store |
| **Expected Quality Benefit** | Indirect — faster iteration enables more QA runs |
| **Expected Performance Benefit** | **High** — 2-5× throughput improvement for large novels |
| **Complexity** | High — core runtime changes, provider protocol implications |
| **Risk** | Violates "chunk = execution unit" principle (RM-8.2 Core Principle #2); batching breaks per-chunk QA/retry |
| **Dependencies** | RM-6/7/8.1/8.2 runtime architecture |
| **Core/Optional** | **Core** but **high risk** — requires architecture review |

### Candidate G: Sample / Preview Generation

| Aspect | Detail |
|---|---|
| **Problem** | No way to generate "first chapter free" or preview without full translation. |
| **Existing Capability** | `ReaderChapterMap` with chapter positions, `quality_delivery_v83` pipeline |
| **Missing Capability** | `--generate-sample` flag: translate first N chapters only, produce sample EPUB/TXT with metadata |
| **Expected Quality Benefit** | User can evaluate quality before full commitment |
| **Expected Performance Benefit** | **High** for evaluation workflows |
| **Complexity** | Low — subset of existing pipeline |
| **Risk** | Sample may not represent full novel quality; must be clearly labeled |
| **Dependencies** | RM-8.3/8.4 delivery pipeline |
| **Core/Optional** | **Optional** — workflow enhancement |

---

## 7. Eliminated False Candidates

| False Candidate | Reason Eliminated |
|---|---|
| **New literary quality detectors / LLM judge** | RM-8.1 Non-Goals: ❌ New detector patterns, ❌ LLM judge / external model calls |
| **New chunking engine / re-chunking by scene** | RM-8.2 Non-Goals: ❌ New chunking engine, ❌ Modifying `split_text()`/`DEFAULT_CHUNK_SIZE` |
| **RM-7 Entity/Review/Learning pipeline changes** | RM-8.2/8.3 Non-Goals: ❌ Modifying RM-7 pipeline |
| **EPUB as Core delivery prerequisite** | RM-8.4 Core Principle: EPUB is **Optional EPUB Packaging**; failure must not block Core |
| **EPUB auto-generation on every translation** | RM-8.4 Explicit Non-Goals: ❌ EPUB 自動於每次翻譯後產生 |
| **EPUB using AI/LLM for chapter detection** | RM-8.4 Explicit Non-Goals: ❌ 使用 LLM 判斷章節, ❌ EPUB 自行猜測 chapter boundary |
| **TXT → EPUB → TXT round-trip** | RM-8.4 Source of Truth: RM-8.3 TXT body = 唯一正文 Source of Truth; 禁止 TXT → EPUB → TXT |
| **Heuristic chapter title inference** | RM-8.3/8.4: Chapter title ONLY from explicit marker; deterministic fallback only |
| **Re-translation / re-polish / re-assembly in EPUB** | RM-8.4: EPUB 不得重新翻譯、重新 chunk、重新 assembly、重新 polish |
| **New QA gate / retry engine for literary quality** | RM-8.1 Non-Goals: ❌ New QA gate / retry engine |
| **Synthetic literary_quality_score (0-100)** | RM-8.1 Non-Goals: ❌ `literary_quality_score` (synthetic 0–100) |
| **Auto-learning / online adaptation** | NTPE principle: Fail Closed; RM-8.3 Non-Goals: ❌ Auto-learning |
| **Human-in-the-loop review interfaces** | RM-8.1 Non-Goals: ❌ Human-in-the-loop review interfaces |
| **Modifying `TranslationEngine` core logic** | RM-8.2 Non-Goals: ❌ Modifying `TranslationEngine` core logic |
| **Provider/LLM/Network calls for reader packaging** | RM-8.4 Provider/Network Contract: Provider Requests = 0, Network Requests = 0 |

---

## 8. Recommended Primary RM-8.5 Direction

### **RM-8.5: Cross-Chunk Semantic Quality Gate (Core)**

**Why this is the highest-value next step:**

1. **Directly addresses the largest verified quality gap**: RM-8.2 acceptance report (§5) explicitly states infrastructure is verified but *"不等同於完整語意層面的翻譯正確性"* — pronoun resolution, speaker attribution, POV stability, tense/voice consistency, emotional tone continuity are **not validated**.

2. **Leverages existing infrastructure**: RM-8.2 already propagates `NarrativeState` (perspective, voice, tense, emotional_tone), `SceneMemoryRecord` (active_speaker, participants), and `ContextSelectionResult` to every chunk. The metadata exists in `chunk_records[].metadata.context_state` — validation just needs to consume it.

3. **Extends existing RM-8.3 validator framework**: `validate_final_novel()` already has 9 deterministic checks with weighted scoring. Adding cross-chunk semantic checks follows the same pattern (critical/major/minor severity, PASS ≥ 70, no critical failures).

4. **Zero provider cost / zero network**: Purely deterministic validation on final assembled text + existing metadata. Aligns with RM-8.1/8.2/8.3/8.4 principle: **Provider Requests = 0**.

5. **Backward compatible & feature-gated**: New checks added to validator; existing `quality_delivery_v83` flag controls execution. When OFF, zero behavior change.

6. **Measurable quality improvement**: Each check produces pass/fail + score + details. Violations directly map to reader-visible issues (pronoun flips, speaker confusion, POV shifts).

7. **Completes the RM-8 quality stack**:
   - RM-8.1: Per-chunk literary quality (micro)
   - RM-8.2: Cross-chunk context propagation (infrastructure)
   - RM-8.3: Full-novel format validation (macro format)
   - **RM-8.5: Cross-chunk semantic validation (macro semantics)**
   - RM-8.4: Reader structure/packaging (delivery)

---

## 9. Preliminary RM-8.5 Boundary

| Aspect | Definition |
|---|---|
| **Scope** | Add deterministic cross-chunk semantic validation checks to RM-8.3 `validate_final_novel()`: pronoun consistency, speaker attribution stability, narrative POV/tense/voice continuity, emotional tone coherence, cross-chunk entity consistency (non-locked terms). Consumes RM-8.2 metadata from `chunk_records`. |
| **Non-Goals** | ❌ New provider/LLM calls, ❌ Re-translation, ❌ Modify RM-8.2 propagation logic, ❌ Auto-fix/correction (detection only), ❌ Human review interfaces, ❌ New chunking, ❌ Modify RM-7, ❌ Synthetic semantic score |
| **Inputs** | 1. RM-8.3 polished TXT body (full novel text)<br>2. `chunk_records` with `metadata.context_state` (scene_id, chapter_id, narrative, boundary, selected_context_ids)<br>3. `locked_dictionary` (for term consistency baseline)<br>4. RM-8.2 `ContextMemoryStore` snapshot (optional, for terminology contexts) |
| **Outputs** | Extended `ValidationResult` with new `ValidationCheck` entries:<br>- `pronoun_consistency` (major)<br>- `speaker_attribution_stability` (major)<br>- `narrative_pov_continuity` (major)<br>- `tense_voice_consistency` (major)<br>- `emotional_tone_coherence` (minor)<br>- `cross_chunk_entity_consistency` (major)<br>Updated `QualityCertificate` with new dimension scores |
| **Dependencies** | RM-8.2 (metadata), RM-8.3 (validator framework), RM-8.1 (literary quality aggregate) |
| **Core/Optional** | **Core** — quality gate is mandatory for delivery |
| **Provider/Network Requirements** | **Provider Requests = 0, Network Requests = 0** — purely local deterministic validation |
| **Relationship to RM-8.3** | Extends `validate_final_novel()` in `core/translation_release/validator.py`; new checks integrated into weighted scoring; `QualityCertificate` gains new dimension scores |
| **Relationship to RM-8.4** | No direct dependency; RM-8.4 consumes validated TXT body. RM-8.5 validation runs before RM-8.4 chapter mapping. |
| **Feature Flag** | `quality_delivery_v83` (existing) controls full delivery pipeline including RM-8.5 checks. No new flag needed. |
| **Acceptance Gates** | 1. All new checks implemented and deterministic<br>2. Unit tests for each check with fixture data<br>3. Integration test: known pronoun/speaker/POV drift detected<br>4. Regression: all RM-7/8.1/8.2/8.3/8.4 tests PASS<br>5. `ntpe_validate.py` PASS, `compileall` PASS, `git diff --check` PASS<br>6. Zero provider requests in validation |

---

## 10. Final Verdict

**RM-8.5 INVENTORY — READY FOR SPECIFICATION**

The inventory is complete. Evidence from actual repository files and RM-8.1 through RM-8.4 specifications supports a single, well-bounded RM-8.5 direction: **Cross-Chunk Semantic Quality Gate** as a Core extension to the RM-8.3 validation framework. All false candidates eliminated per governance constraints. The preliminary boundary is defined with clear scope, non-goals, inputs, outputs, dependencies, and acceptance criteria.

---

**Next Step**: Produce **RM-8.5 Implementation Specification** with exact function signatures, check algorithms, test specifications, and file edit list — following the same rigor as RM-8.1 through RM-8.4 specifications.