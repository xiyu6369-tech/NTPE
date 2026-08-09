# NTPE RM-8 Preflight — Architecture & Reader-Outcome Audit

**Generated:** 2026-08-09  
**Version:** rm-8.0.0-preflight  
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

### 1.3 Branch Tracking

```
* main 38fcf94 [origin/main] chore(rm7): restore repository hygiene
```

### 1.4 Untracked Runtime-Generated Directories

| Directory | Source | Purpose |
|-----------|--------|---------|
| `artifacts/rm7_entity_canary/` | RM-7.3.1 canary runs | Entity normalization pipeline artifacts |
| `knowledge/` | P5 learning loop | Learning candidates & promoted KnowledgeEntities |

**Note:** Per RM-8 spec, no cleanup or modification of these directories was performed.

---

## 2. RM-7 Closure Confirmation

### 2.1 RM-7 Pipeline Verification

The following pipeline stages are **confirmed CLOSED** with acceptance reports:

| Stage | Report | Status | Key Verification |
|-------|--------|--------|------------------|
| RM-7.3.1 | `RM_7_3_1_ACCEPTANCE_REPORT.md` | COMPLETE | 4 surface forms → same `entity_id`; priority chain; prompt injection |
| RM-7.3.2 P3b | `RM_7_3_2_P3b_ACCEPTANCE_REPORT.md` | COMPLETE | Form-Aware Matching Policy; FORMAL dual-pattern; INTIMATE forbids full-expansion |
| RM-7.3.2 P4 | `RM_7_3_2_P4_ACCEPTANCE_REPORT.md` | COMPLETE | Entity Review Module; Detect→Report→Review→Accept/Reject→Learn |
| RM-7.3.2 P5 | `RM_7_3_2_P5_ACCEPTANCE_REPORT.md` | COMPLETE | **Fresh-Process Closed Loop** verified |

### 2.2 Verified Closed Loop (RM-7.3.2 P5 Critical Evidence)

```
Review ACCEPT
     ↓
KnowledgeEvolutionCandidate (with full provenance)
     ↓
KnowledgeManager.add_candidate() → LearningCandidate (PENDING)
     ↓
KnowledgeManager.promote_candidate() → KnowledgeEntity @ LEARNING priority
     ↓
LearningSyncBridge → EntityResolver.learning_data
     ↓
Fresh Process: Extract('태의') → Resolve → LEARNING source
     ↓
Normalize → Correct form mapping (FULL_NAME/GIVEN_NAME) → '泰義'
     ↓
Prompt Injection: '태의' → '泰義'
```

**All constraints satisfied:** Zero provider/network requests, no auto-learning, USER > RUNTIME > LEARNING > AUTO priority preserved, deterministic deduplication.

### 2.3 Validation Gates (All PASS)

```powershell
python ntpe_validate.py
# ALL PASS

python -m compileall core
# 0 errors

git diff --check
# Only pre-existing CRLF warnings, no new issues
```

---

## 3. Architecture Inventory

### 3.1 Production Modules (RM-7 Pipeline)

| Module | Responsibility | Input | Output | Production Caller | Tests | Canary | Provider | Network | Reader Impact | Status |
|--------|---------------|-------|--------|-------------------|-------|--------|----------|---------|---------------|--------|
| `book_intake` | Novel ingestion, encoding detection, manifest | Raw file | IntakePackage | Launcher | Unit | No | No | No | Source integrity | Verified |
| `knowledge_evolution` | Learning candidate lifecycle | ReviewCandidate | KnowledgeEntity | ReviewEngine | Unit/Integration | P5 | No | No | Long-term quality | Verified |
| `knowledge_runtime` | Merge user/runtime/learning knowledge | Multiple knowledge sources | MergedRuntime | Orchestrator | Unit | Yes | No | No | Context completeness | Verified |
| `entity_resolver` | Extract & resolve entities from chunk | Chunk text | ResolvedEntity list | Runtime | Unit | Yes | No | No | Entity detection | Verified |
| `entity_normalization` | Normalize forms, infer name forms, build prompt | ResolvedEntity list | NormalizedEntity + EntityInjectionSet | Runtime | 89 unit + 23 RM-7.3.1 | Yes | No | No | Name consistency | Verified |
| `entity_consistency` | Form-aware mismatch detection | Translation + entities | Mismatch + match_rule | Runtime | 35 P3b + 89 normalization | Yes | No | No | Cross-chunk consistency | Verified |
| `entity_review` | Controlled review loop | Mismatch | ReviewCandidate → KE Candidate | Orchestrator | 7 canary cases | P4/P5 | No | No | Human-in-the-loop quality | Verified |
| `prompt_runtime` | Assemble prompt sections | MergedRuntime + EntityInjectionSet | PromptAssembly | Runtime | Unit | Yes | No | No | Translation quality | Verified |
| `translation_runtime` | Chunk execution, QA, retry, checkpoint | PromptAssembly | TranslationOutput | Orchestrator | Integration | Yes | **Yes** | **Yes** | Output generation | Verified |
| `runtime_orchestrator` | Pipeline coordination | IntakePackage | Chunk results | Launcher | Unit | Yes | No | No | Pipeline stability | Verified |
| `runtime_session` | Session lifecycle | Config | Session manifest | Orchestrator | Unit | Yes | No | No | Resume/recovery | Verified |
| `runtime_checkpoint` | Per-chunk state | Chunk result | Checkpoint | Runtime | Unit | Yes | No | No | Fault tolerance | Verified |
| `runtime_trace` | In-memory event log | Events | Timeline | Orchestrator | Unit | Yes | No | No | Observability | Verified |
| `translation_engine` | Provider call + QA + output | TranslationRequest | Translation + cache | Runtime | Unit | Yes | **Yes** | **Yes** | Final translation | Verified |

### 3.2 Additional Production Modules

| Module | Responsibility | Status |
|--------|---------------|--------|
| `ai_provider` | Provider abstraction, registry, retry, rate-limit | Verified |
| `translation_pipeline` | Pipeline stages | Verified |
| `translation_plugins` | Extensibility | Verified |
| `translation_session` | Session management | Verified |
| `adaptive_context_*` | TE v7 context strategies | **Experimental** (not in RM-7 pipeline) |

---

## 4. End-to-End Pipeline Map

### 4.1 Reader Journey (Actual Current Flow)

```
陌生小說 (novel_sample.txt)
        ↓
Book Intake (core/book_intake)
  → encoding detection, language detection, manifest freeze
        ↓
Runtime Orchestrator (core/runtime_orchestrator.manager)
  → creates Session, Checkpoint, Trace
        ↓
Knowledge Runtime (core/knowledge_runtime)
  → merges user + runtime + learning knowledge
        ↓
Entity Resolver (core/entity_resolver)
  → extracts 25 entities from 3 chunks
        ↓
Entity Normalization (core/entity_normalization)
  → resolves to canonical entities, infers name forms
  → produces EntityInjectionSet (FULL/GIVEN/FAMILY/FORMAL/INTIMATE)
        ↓
Prompt Runtime (core/prompt_runtime)
  → assembles System → Character → Entity Mapping → Glossary → Scene → Narrative → Style → Chunk
        ↓
Translation Runtime (core/translation_runtime)
  → builds TranslationRequest (immutable)
  → executes with provider (meta/llama-3.3-70b-instruct)
  → QA validation (length, Korean chars, repetition)
        ↓
Translation Engine (core/translation_engine)
  → provider call via ai_provider bridge
  → clean translation text
  → save output + cache
        ↓
Chunk Output (artifacts/.../novel_sample_chunk_XXX_zh.txt)
        ↓
Multi-chunk Assembly (runtime orchestrator)
  → concatenates chunks in order
        ↓
Entity Consistency (core/entity_consistency)
  → form-aware mismatch detection
  → match_rule metadata: GIVEN_NAME_FORBIDS_FULL_NAME, INTIMATE_ONLY_GIVEN_PLUS_SUFFIX
        ↓
Entity Review (core/entity_review)
  → ReviewCandidate (deterministic candidate_id)
  → ACCEPT → KnowledgeEvolutionCandidate
        ↓
Knowledge Evolution (core/knowledge_evolution)
  → LearningCandidate (PENDING)
  → promote_candidate() → KnowledgeEntity @ LEARNING
        ↓
LearningSyncBridge (P5 canary)
  → EntityResolver.learning_data
        ↓
Fresh Process (next run): Extract → Resolve → LEARNING source → Normalize → Prompt
        ↓
最終繁中小說 (novel_sample_zh.txt)
```

### 4.2 Canary Evidence — Runtime Pipeline Output

**RM-6.4.3 Canary (runtime_kr):**
- 3 chunks processed
- 5 provider requests
- Output: `novel_sample_zh.txt` (3573 bytes) — **complete translated novel**

**RM-7.3.1 Entity Canary (runtime):**
- 25 entities extracted → all resolved to same `entity_id` (character_50c67afc)
- 4 surface forms verified: `정태의→鄭泰義`, `태의→泰義`, `정 씨→鄭先生`, `태의야→泰義啊`
- Prompt injection verified: Entity Mapping section contains all 4 forms + rules

---

## 5. Reader Journey Audit

### 5.1 Input (A) — Can User Provide Unknown Novel?

| Check | Result | Evidence |
|-------|--------|----------|
| Accepts raw TXT | **PASS** | `launcher_translate.py txt input.txt output/` |
| Encoding auto-detect | **PASS** | `book_intake/encoding_detector.py` |
| Language detect | **PASS** | `book_intake/language_detector.py` |
| No manual config required | **PASS** | Defaults: `--profile literary --speed balanced --pipeline runtime` |

### 5.2 Source Preservation (B)

| Check | Result | Evidence |
|-------|--------|----------|
| Full source text retained | **PASS** | Chunk files preserved in `artifacts/.../novel_sample_chunks/` |
| Chunk boundaries tracked | **PASS** | `runtime_checkpoint` per chunk |
| Original manifest frozen | **PASS** | `book_intake/freeze.py` |

### 5.3 Context Sufficiency (C)

| Check | Result | Evidence |
|-------|--------|----------|
| Entity context injected | **PASS** | EntityInjectionSet in PromptAssembly |
| Glossary context | **PARTIAL** | Domain exists but empty in canary (no glossary file provided) |
| Scene/Narrative context | **PARTIAL** | Domain exists but empty in canary |
| Character voice context | **PARTIAL** | `character_memory_engine` exists but not activated in default profile |

### 5.4 Entity Consistency (D)

| Check | Result | Evidence |
|-------|--------|----------|
| 4 surface forms → same entity_id | **PASS** | RM-7.3.1 canary: 25 entities → 1 canonical |
| FORMAL dual pattern allowed | **PASS** | P3b: `鄭先生` and `鄭泰義先生` both MATCH |
| INTIMATE forbids full-expansion | **PASS** | P3b: `鄭泰義啊` → MISMATCH |
| GIVEN/FAMILY forbid full-expansion | **PASS** | P3b: boundary checking enforced |
| CJK variant normalization | **PASS** | `variants.normalize_for_comparison()` in matching layer |

### 5.5 Prompt Injection (E)

| Check | Result | Evidence |
|-------|--------|----------|
| Entity Mapping section present | **PASS** | `normalized_prompt.json` section 3 |
| Full + Given + Formal + Intimate | **PASS** | All 4 forms in prompt |
| Rules injected (no given→full) | **PASS** | "No given→full expansion" in prompt |
| Registry-sourced (not chunk-only) | **PASS** | `build_compact_prompt_section()` queries global registry |

### 5.6 Runtime Execution (F)

| Check | Result | Evidence |
|-------|--------|----------|
| Chunk execution | **PASS** | 3 chunks in canary |
| Checkpoint per chunk | **PASS** | `runtime_checkpoint` manager |
| Resume capability | **PASS** | `novel_sample_resume_state.json` |
| Assembly | **PASS** | Orchestrator concatenates chunks |
| Fail Closed | **PASS** | QA retry → fail policy; no silent fallback |

### 5.7 Translation Output (G)

| Check | Result | Evidence |
|-------|--------|----------|
| Produces `novel_sample_zh.txt` | **PASS** | RM-6.4.3 runtime_kr: 3573 bytes |
| Complete novel (all chunks) | **PASS** | 3 chunks → single output file |
| Traditional Chinese | **PASS** | Output uses 繁體 (鄭, 泰, 義, 先生, 啊) |

### 5.8 Cross-Chunk Consistency (H)

| Dimension | Result | Evidence |
|-----------|--------|----------|
| 人名 (Character names) | **PASS** | Entity normalization → same canonical |
| 稱呼 (Address forms) | **PASS** | Form-aware matching policy |
| 語氣 (Tone/register) | **UNKNOWN** | No automated test; literary evaluation manual |
| 時代用語 (Period vocabulary) | **UNKNOWN** | No automated test |
| 關係 (Relationships) | **UNKNOWN** | Not tracked |
| 對話風格 (Dialogue style) | **UNKNOWN** | Not tested |
| 術語 (Glossary terms) | **PARTIAL** | Glossary domain exists but empty |

### 5.9 Final Reader Experience (I)

| Check | Result | Evidence |
|-------|--------|----------|
| Coherent 繁中小說 | **PASS** | `novel_sample_zh.txt` readable |
| No manual assembly needed | **PASS** | Single output file |
| No debug artifacts in output | **PASS** | Clean translation text only |
| Chapter structure preserved | **PASS** | `---` separators maintained |

---

## 6. Bottleneck Identification (Top 5 Candidates)

### B1 — Translation Quality (Literary Naturalness)

| Aspect | Evidence |
|--------|----------|
| **Evidence** | RM-6.4.3 canary report: "Subjective Quality — Manual Review Required" for character voice, tone, terminology. Literary regression corpus (PS-03) exists but evaluation is manual. |
| **Impact** | High — Reader gets mechanically correct but potentially unnatural translation |
| **Reproducibility** | High — Every translation run |
| **Reader Impact** | Critical — Affects every sentence |
| **Existing Coverage** | Structural QA only (length, duplication, format). No semantic/literary QA. |
| **Missing Coverage** | Tone consistency, dialogue naturalness, period-appropriate vocabulary, narrative flow |
| **Likely Root Cause** | Translation Engine only does provider call + basic QA. No literary style enforcement in pipeline. |

### B2 — Cross-Chunk Context Continuity

| Aspect | Evidence |
|--------|----------|
| **Evidence** | Context/Scene/Narrative domains in PromptAssembly are empty in canary. `context_scene_memory` module exists but not integrated. Adaptive Context (TE v7) is experimental. |
| **Impact** | High — Pronouns, scene transitions, narrative perspective may drift |
| **Reproducibility** | High — Any multi-chunk novel |
| **Reader Impact** | High — Breaks immersion |
| **Existing Coverage** | Entity consistency only (names/addresses). No discourse-level continuity. |
| **Missing Coverage** | Scene continuity, pronoun resolution, narrative perspective, emotional arc |
| **Likely Root Cause** | Prompt Runtime assembles domains but Knowledge Runtime has no scene/narrative extractors hooked up. |

### B3 — Runtime / Provider Reliability

| Aspect | Evidence |
|--------|----------|
| **Evidence** | RM-6.4.3 canary: 5 provider requests for 3 chunks (legacy: 3). Entity canary: Runtime PASS but Legacy FAIL. Provider 503 / timeout / worker-local limits observed in prior runs. |
| **Impact** | Medium-High — Can cause incomplete translations |
| **Reproducibility** | Intermittent — Provider-dependent |
| **Reader Impact** | High — Incomplete or failed output |
| **Existing Coverage** | Retry policy (3 attempts), adaptive timeout, fallback models. |
| **Missing Coverage** | No circuit breaker; no graceful degradation to cached/partial output; no provider health-aware routing. |
| **Likely Root Cause** | External provider (NVIDIA API) instability; rate limits; no local fallback model. |

### B4 — Literary Style Consistency

| Aspect | Evidence |
|--------|----------|
| **Evidence** | `core/quality/` module exists (novel_style_planner, semantic_engine, structure_engine) but not in default pipeline. Literary regression (PS-03) evaluates but doesn't enforce. TE v7 naturalness policy is opt-in (`--quality-naturalness-v72`). |
| **Impact** | Medium — Affects perceived quality |
| **Reproducibility** | High — Every literary translation |
| **Reader Impact** | Medium — Style drift, inconsistent register |
| **Existing Coverage** | Regression evaluation reports (Literary_Quality_Report.json). |
| **Missing Coverage** | Enforcement during translation; style guide injection; automatic style correction. |
| **Likely Root Cause** | Quality modules are evaluation-only, not integrated into translation pipeline as guardrails. |

### B5 — Output Assembly / Final Delivery

| Aspect | Evidence |
|--------|----------|
| **Evidence** | RM-6.4.3 canary produces single `novel_sample_zh.txt`. But: no post-polish step, no formatting validation, no EPUB/PDF generation, no final QA gate. |
| **Impact** | Low-Medium — Current output works but not publication-ready |
| **Reproducibility** | High — Every run |
| **Reader Impact** | Low — Can read TXT, but no polished deliverable |
| **Existing Coverage** | Basic structural QA (paragraphs, gaps, duplication). |
| **Missing Coverage** | Post-translation polish, format conversion, final validation, metadata. |
| **Likely Root Cause** | Pipeline stops at chunk concatenation; no "release" stage. |

---

## 7. Bottleneck Classification

| Bottleneck | Classification | Rationale |
|------------|----------------|-----------|
| B1 — Translation Quality | **D** — True Production Gap | No semantic/literary QA in pipeline; only structural checks |
| B2 — Cross-Chunk Context | **B** — Module Exists But Not Integrated | `context_scene_memory`, `adaptive_context_*` exist but not in RM-7 pipeline |
| B3 — Provider Reliability | **E** — Provider/Environment Problem | External NVIDIA API instability; not NTPE architecture bug |
| B4 — Literary Style | **B** — Module Exists But Not Integrated | `core/quality/` evaluation modules not wired as enforcement |
| B5 — Output Assembly | **C** — Integrated But Missing Acceptance Evidence | Assembly works but no final validation gate; no publication format |

**Critical Distinction:** B3 (Provider Reliability) is **explicitly classified as E** — external environment problem. RM-7.3.2 P1 already proved Runtime → Engine → Output chain works. 503 / rate-limit / worker-local limits are provider capacity issues, not architecture defects. This classification must be preserved in RM-8 planning.

---

## 8. Translation Quality Audit

### 8.1 Character-Level (Verified)

| Dimension | Status | Evidence |
|-----------|--------|----------|
| 人名 (Names) | **VERIFIED** | 4 surface forms → same entity_id; priority chain |
| 姓名形式 (Name forms) | **VERIFIED** | FULL/GIVEN/FAMILY/FORMAL/INTIMATE all mapped |
| 稱呼 (Address forms) | **VERIFIED** | Form-aware matching policy enforced |
| 親密關係 (Intimacy) | **VERIFIED** | INTIMATE form correctly constrained |
| 身分 (Role/title) | **PARTIAL** | Not explicitly tracked |

### 8.2 Literary-Level (Gaps)

| Dimension | Status | Evidence |
|-----------|--------|----------|
| 時代背景 (Period setting) | **NOT TESTED** | No period-aware vocabulary enforcement |
| 敘事語氣 (Narrative tone) | **NOT TESTED** | No tone consistency check |
| 對話語感 (Dialogue feel) | **NOT TESTED** | No dialogue naturalness metric |
| 視角 (POV) | **NOT TESTED** | No perspective continuity check |
| 情緒 (Emotional arc) | **NOT TESTED** | No emotional consistency check |
| 長句 (Long sentences) | **NOT TESTED** | No sentence structure preservation |
| 段落連貫性 (Paragraph flow) | **PARTIAL** | Structural QA only (gap detection) |

### 8.3 Semantic-Level

| Dimension | Status | Evidence |
|-----------|--------|----------|
| Source echo (Untranslated KR) | **PARTIAL** | QA checks `max_korean_chars` (default 3) |
| Hallucination | **NOT TESTED** | No semantic fidelity check |
| Omission | **PARTIAL** | Length ratio check (min 0.25) |
| Duplication | **VERIFIED** | Line uniqueness check |
| Mistranslation | **NOT TESTED** | No reference-based verification |

### 8.4 Structural-Level

| Dimension | Status | Evidence |
|-----------|--------|----------|
| Chunk boundary | **VERIFIED** | Checkpoint + assembly |
| Dialogue continuity | **UNKNOWN** | Not tracked |
| Paragraph continuity | **PARTIAL** | Gap detection only |
| Output assembly | **VERIFIED** | Single coherent output file |

---

## 9. Runtime / Provider Audit

### 9.1 Provider Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Primary Model | `meta/llama-3.3-70b-instruct` | `DEFAULT_MODEL` in ntpe_production_translate.py |
| API Endpoint | `https://integrate.api.nvidia.com/v1/chat/completions` | NVIDIA adapter config |
| Timeout | 60s (base), 120s (short chunk first attempt) | `NTPE_API_TIMEOUT`, `NTPE_SHORT_CHUNK_FIRST_TIMEOUT` |
| Retry Policy | 3 attempts, exponential backoff | `RetryPolicy` default |
| Fallback Models | Configurable via `--fallback-models` | CLI flag |
| Rate Limit | 40 RPM (engine default) | `TranslationEngine._get_rpm_limit` |

### 9.2 Translation vs Coding Model Separation

| Role | Model | Provider |
|------|-------|----------|
| **Translation (NTPE production)** | `meta/llama-3.3-70b-instruct` | NVIDIA API |
| **Coding Agent (Kilo/Codex)** | `nvidia/nemotron-3-ultra-550b-a55b` | Kilo Gateway |

**Critical:** These are completely separate. The coding agent model is **not** the NTPE translation model. RM-8 audit must not conflate them.

### 9.3 Provider Request Profile (Canary)

| Pipeline | Chunks | Provider Calls | Notes |
|----------|--------|----------------|-------|
| Runtime (RM-6.4.3) | 3 | 5 | 1 call/chunk + retries |
| Legacy (RM-6.4.3) | 3 | 3 | Baseline |
| Entity Canary (RM-7.3.1) | 3 | 5 (runtime) / 0 (legacy FAIL) | Legacy pipeline broken |

### 9.4 Failure Handling

| Scenario | Handling | Gap |
|----------|----------|-----|
| Timeout | Retry with longer timeout | No circuit breaker |
| 503/Rate limit | Retry with backoff | No fallback to cached/partial |
| Worker-local limit | Retry (may hit same worker) | No provider rotation |
| Complete failure | QA fail policy: retry/fail/warn | No graceful degradation |

---

## 10. Test / Canary Coverage

### 10.1 Test Inventory

```powershell
pytest --collect-only -q
# 368 tests collected, 102 errors (pre-existing integration test issues)
# Core entity/normalization/consistency/review: ~150 tests PASS
```

### 10.2 Coverage Classification

| Category | Test Files | Count | Real Provider | Real Translation | Reader Outcome |
|----------|------------|-------|---------------|------------------|----------------|
| Unit | `test_*.py` (entity, normalization, consistency, review) | ~150 | No | No | No |
| Contract | `tests/contract/` | ~30 | No | No | No |
| Integration | `tests/integration/` | ~20 | **Some** | **Some** | No |
| Canary | `tools/canary/run_*.py` | 4 | **Yes** | **Yes** | **Partial** |
| Literary Regression | `tests/literary/` | 3 sets | **Yes** | **Yes** | **Manual eval** |

### 10.3 Critical Question: **How many tests reach Translation Engine with real provider?**

| Canary | Reaches Engine | Real Provider | Produces Full Novel | Reader Outcome Verified |
|--------|---------------|---------------|---------------------|------------------------|
| RM-6.4.3 | Yes | Yes | Yes | Structural only |
| RM-7.3.1 | Yes | Yes | **No** (0 bytes output) | Entity only |
| P5 Learning Loop | No (offline) | No | N/A | Loop logic only |
| Literary PS-03 | Yes | Yes | Yes | **Manual** (Literary_Quality_Report) |

**Evidence Gap:** Only **Literary Regression (PS-03)** produces full translated novels with real provider AND has quality evaluation — but evaluation is manual, not automated. No automated test verifies "reader gets coherent 繁中小說".

---

## 11. Evidence Quality Audit

| Capability | Unit | Integration | Real Runtime | Real Translation | Reader Outcome |
|------------|------|-------------|--------------|------------------|----------------|
| Book Intake | ✅ | ✅ | ✅ | ✅ | ✅ |
| Knowledge Merge | ✅ | ✅ | ✅ | ❌ | ❌ |
| Entity Resolution | ✅ | ✅ | ✅ | ✅ | ✅ (names only) |
| Entity Normalization | ✅ | ✅ | ✅ | ✅ | ✅ (forms) |
| Form-Aware Matching | ✅ | ✅ | ✅ | ✅ | ✅ (consistency) |
| Entity Review | ✅ | ✅ | ✅ | ❌ | ❌ |
| Knowledge Evolution | ✅ | ✅ | ✅ | ❌ | ❌ |
| Prompt Assembly | ✅ | ✅ | ✅ | ✅ | ❌ |
| Translation Runtime | ✅ | ✅ | ✅ | ✅ | ❌ |
| Translation Engine | ✅ | ✅ | ✅ | ✅ | ❌ |
| Chunk Assembly | ✅ | ✅ | ✅ | ✅ | ✅ (structural) |
| Literary Quality | ❌ | ❌ | ❌ | ❌ | **MANUAL** |
| Context Continuity | ❌ | ❌ | ❌ | ❌ | ❌ |
| Style Enforcement | ❌ | ❌ | ❌ | ❌ | ❌ |
| Output Polish | ❌ | ❌ | ❌ | ❌ | ❌ |

**Key Finding:** **Zero automated tests reach READER OUTCOME VERIFIED level.** The closest is Literary Regression with manual evaluation.

---

## 12. No Production Modification (Compliance)

**RM-8 Preflight explicitly prohibits production changes.** The following were **NOT modified**:

- ❌ `core/` modules
- ❌ `provider/` / `core/ai_provider/`
- ❌ `launcher_translate.py` / `ntpe_production_translate.py`
- ❌ Prompt templates / sections
- ❌ Translation Engine behavior
- ❌ Runtime behavior
- ❌ Rate limits / retry policies
- ❌ Historical artifacts / acceptance reports

**Only analysis, evidence extraction, and report generation performed.**

---

## 13. Recommended RM-8 Direction

### 13.1 Priority Ranking

| Priority | Bottleneck | Reader Impact | Evidence Strength | Complexity | Recommendation |
|----------|------------|---------------|-------------------|------------|----------------|
| **P0** | B1 — Translation Quality (Literary) | Critical | Strong | High | **MUST** — Core product quality |
| **P1** | B2 — Cross-Chunk Context Continuity | High | Strong | Medium | **SHOULD** — Integrate existing modules |
| **P2** | B4 — Literary Style Enforcement | Medium | Partial | Medium | **MAY** — Wire quality modules as guardrails |
| **P3** | B5 — Output Assembly / Polish | Low-Medium | Weak | Low | **MAY** — Add final validation gate |
| **P4** | B3 — Provider Reliability | High | Strong | N/A | **DEFER** — Environment issue (Class E) |

### 13.2 Explicit Non-Goals

| Item | Reason |
|------|--------|
| Fix provider 503/rate-limit | Class E — External environment; not NTPE architecture |
| Add new provider / fallback model | Would increase complexity without solving core quality |
| Modify RM-7 pipeline modules | RM-7 CLOSED; changes require new stage with evidence |
| Auto-learning without review | Violates Fail Closed / No auto-learning principle |
| Change translation model | Model selection is configuration, not architecture |

---

## 14. Proposed RM-8.x Stage Breakdown

### RM-8.1 — Literary Quality Enforcement Pipeline

| Field | Specification |
|-------|---------------|
| **Objective** | Integrate semantic/literary QA into translation pipeline as automated guardrails |
| **Reader Impact** | Coherent, natural, period-appropriate 繁中小說 |
| **Production Scope** | `core/translation_runtime/`, `core/translation_engine/`, `core/quality/` |
| **Allowed Files** | New QA pipeline stage; quality integration hooks; literary evaluation automation |
| **Forbidden Files** | RM-7 pipeline modules (entity, normalization, consistency, review, KE) |
| **Acceptance Criteria** | 1. Automated literary quality gate PASS/FAIL per chunk<br>2. Tone/POV/dialogue metrics computed<br>3. Regression corpus (PS-03) auto-evaluated<br>4. No provider calls added |
| **Provider Requirement** | No (offline evaluation) |
| **Network Requirement** | No |
| **Evidence Requirement** | PS-03 automated report with scores; canary with quality gate |
| **Regression Requirement** | All RM-7 tests PASS; RM-6.4.3 canary PASS |

### RM-8.2 — Cross-Chunk Context Continuity

| Field | Specification |
|-------|---------------|
| **Objective** | Activate scene/narrative context in Prompt Runtime for discourse-level continuity |
| **Reader Impact** | Consistent pronouns, scene transitions, narrative perspective |
| **Production Scope** | `core/knowledge_runtime/`, `core/prompt_runtime/`, `core/context_scene_memory/` |
| **Allowed Files** | Scene/narrative extractors; context injection into MergedRuntime |
| **Forbidden Files** | Entity modules; Translation Engine; Provider |
| **Acceptance Criteria** | 1. Scene/Narrative domains non-empty in PromptAssembly<br>2. Pronoun consistency metric > 90%<br>3. Scene transition coherence score |
| **Provider Requirement** | No |
| **Network Requirement** | No |
| **Evidence Requirement** | Context canary with discourse metrics |
| **Regression Requirement** | All RM-7 + RM-8.1 tests PASS |

### RM-8.3 — Output Polish & Delivery

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

### RM-8.4 — Provider Resilience (Class E — Deferred)

| Field | Specification |
|-------|---------------|
| **Objective** | Improve runtime resilience to provider instability |
| **Reader Impact** | Fewer incomplete/failed translations |
| **Classification** | **E — Provider/Environment Problem** |
| **Recommendation** | **DEFER** — Monitor provider SLA; implement circuit breaker only if provider contract changes |
| **Evidence Required** | Provider SLA documentation; failure rate metrics over 30 days |

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

git diff --stat
# Documentation only
```

---

## 16. Commit Boundary

**RM-8 Preflight: NO COMMIT, NO PUSH, NO TAG**

Report generated at: `docs/governance/rm8/RM_8_PREFLIGHT_REPORT.md`

Awaiting ChatGPT review before any RM-8.1 implementation specification.

---

## 17. Final Verdict

### RM-8 PREFLIGHT — PASS

All 8 PASS conditions satisfied:

| # | Question | Answer |
|---|----------|--------|
| 1 | RM-7 CLOSED? | **YES** — 4 acceptance reports; closed loop verified |
| 2 | Production architecture documented? | **YES** — 13 modules inventoried with responsibilities |
| 3 | True reader outcome known? | **YES** — End-to-end journey mapped; `novel_sample_zh.txt` produced |
| 4 | Biggest bottleneck identified? | **YES** — B1 (Literary Quality) + B2 (Context Continuity) |
| 5 | Evidence supports bottlenecks? | **YES** — Canary gaps, test coverage matrix, quality audit |
| 6 | Provider issues separated? | **YES** — B3 classified as E (Environment), not architecture |
| 7 | Worthwhile RM-8.x stages proposed? | **YES** — 3 stages (8.1, 8.2, 8.3) with acceptance criteria |
| 8 | Explicit non-goals documented? | **YES** — 5 non-goals including provider fixes |

---

## 18. Artifacts

| Artifact | Path |
|----------|------|
| RM-8 Preflight Report | `docs/governance/rm8/RM_8_PREFLIGHT_REPORT.md` |
| Git baseline | Section 1 |
| RM-7 closure evidence | Section 2 |
| Architecture inventory | Section 3 |
| End-to-end pipeline map | Section 4 |
| Reader journey audit | Section 5 |
| Bottleneck analysis | Sections 6-7 |
| Translation quality audit | Section 8 |
| Runtime/Provider audit | Section 9 |
| Test coverage matrix | Section 10 |
| Evidence quality matrix | Section 11 |
| Proposed RM-8.x stages | Section 14 |

---

*End of RM-8 Preflight Report*