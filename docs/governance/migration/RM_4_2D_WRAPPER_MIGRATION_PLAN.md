# RM-4.2D — Wrapper Migration Planning

## Phase
RM-4: Repository De-Historicization  
`RM-4.2D` — MOVE_WITH_WRAPPER Re-analysis and Batch Planning

## Date
2026-07-30T18:00:00+08:00

## Baseline
- **RM-4.2B Classification Report**: `docs/governance/migration/RM_4_2B_REVIEW_CLASSIFICATION_REPORT.md`
- **RM-4.2B Classification Data**: `docs/governance/migration/RM_4_2B_CLASSIFICATION_DATA.json`
- **RM-4.2C Test Migration**: COMPLETE (285 SAFE_MOVE test files → `archive/stage_tests/`)

---

## Scope

Re-analyze the **35 entries** classified as `MOVE_WITH_WRAPPER` in RM-4.2B to determine which genuinely require a root compatibility wrapper after relocation, versus those which can be downgraded to `SAFE_MOVE`, upgraded to `KEEP_ROOT`, or `ARCHIVE`.

**This is a read-only audit. No files are moved or modified.**

---

## Methodology

Each candidate was evaluated on four axes:

1. **Entrypoint Analysis** — Production entrypoint? CLI entrypoint? Internal module? Legacy tool? One-shot script?
2. **Import Graph** — Who imports it? Who does it import? Are there `lts/` or production-runtime dependencies?
3. **External References** — README, CI scripts, batch files, `ntpe_validate.py`, `lts/*_validation.py` subprocess references, documentation commands
4. **Wrapper Justification** — Is external backwards compatibility genuinely needed? Or can we update all internal consumers and do a `SAFE_MOVE`?

---

## Per-File Analysis

### Group 1 — DT Launchers (Core Tool Wrappers)

These are thin wrappers that import from `core.*` — zero side effects, zero lazy imports. They serve as CLI launch points for individual tools.

| # | File | Who Imports It? | External Ref? | Wrapper? | Decision | Reason |
|---|------|-----------------|---------------|----------|----------|--------|
| 1 | `launcher.py` | `ntpe_launcher.py`, `ntpe_validate.py` REQUIRED_ENTRYPOINTS, `lts/compatibility_validation.py` | None outside governance | **YES** | **Wrapper Confirmed** | Listed in REQUIRED_ENTRYPOINTS; ntpe_validate fails if missing from root |
| 2 | `launcher_analyzer.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | Zero runtime consumers; 3-line wrapper around `core.document_analyzer.main` |
| 3 | `launcher_character_db.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | Zero runtime consumers |
| 4 | `launcher_glossary.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | Zero runtime consumers |
| 5 | `launcher_kb.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | Zero runtime consumers |
| 6 | `launcher_memory.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | Zero runtime consumers |
| 7 | `launcher_profile.py` | 0 importers | Governance artifacts only | NO | **Downgrade → SAFE_MOVE** | One-shot inspection script with zero consumers |

### Group 1 Summary

| Decision | Count | Files |
|----------|-------|-------|
| Wrapper Confirmed | 1 | `launcher.py` |
| Downgrade → SAFE_MOVE | 6 | `launcher_analyzer.py`, `launcher_character_db.py`, `launcher_glossary.py`, `launcher_kb.py`, `launcher_memory.py`, `launcher_profile.py` |
---

### Group 2: Quality / Prompt / Structure Test Launchers

These are single-shot test / diagnostic tools that run a sample pipeline flow. All have **zero Python importers** beyond governance documents.

| # | File | Wrapper? | Decision | Reason |
|---|------|----------|----------|--------|
| 8 | `launcher_coverage_test.py` | NO | Downgrade → SAFE_MOVE | One-shot coverage checker; zero consumers |
| 9 | `launcher_expansion_plan.py` | NO | Downgrade → SAFE_MOVE | One-shot expansion planner; zero consumers |
| 10 | `launcher_novel_prompt_test.py` | NO | Downgrade → SAFE_MOVE | One-shot smoke test; zero consumers |
| 11 | `launcher_prompt_builder.py` | NO | Downgrade → SAFE_MOVE | One-shot demo script; zero consumers |
| 12 | `launcher_quality_benchmark.py` | NO | Downgrade → SAFE_MOVE | CLI quality benchmark; zero importers |
| 13 | `launcher_retranslate_chunk.py` | NO | Downgrade → SAFE_MOVE | v0.9.1.2 legacy tool; zero importers |
| 14 | `launcher_semantic_repair.py` | NO | Downgrade → SAFE_MOVE | One-shot repair tool; zero importers |
| 15 | `launcher_semantic_test.py` | NO | Downgrade → SAFE_MOVE | Smoke test script; zero importers |
| 16 | `launcher_structure_test.py` | NO | Downgrade → SAFE_MOVE | TQF-01 smoke test; zero importers |
| 17 | `launcher_style_expansion.py` | NO | Downgrade → SAFE_MOVE | Style expansion tool; zero importers |
| 18 | `launcher_style_planner_test.py` | NO | Downgrade → SAFE_MOVE | Style planner smoke test; zero importers |

### Group 2 Summary: 11 files → Downgrade → SAFE_MOVE

---

### Group 3 — Legacy/Demo Pipeline Demos

Vintage `engine.pipeline.*` demo launchers with zero active consumers.

| # | File | Wrapper? | Decision | Reason |
|---|------|----------|----------|--------|
| 19 | `launcher_adaptive_recovery.py` | NO | Downgrade → SAFE_MOVE | v0.9.2 legacy; zero importers |
| 20 | `launcher_pipeline.py` | NO | Downgrade → SAFE_MOVE | Demo launcher; only RM-3.2 tool refs it |
| 21 | `launcher_pipeline_production.py` | NO | Downgrade → SAFE_MOVE | Demo; same pattern |
| 22 | `launcher_pipeline_recovery.py` | NO | Downgrade → SAFE_MOVE | Legacy recovery; zero consumers |
| 23 | `launcher_pipeline_v1.py` | NO | **Archive** | Superseded by `launcher_translate.py` |

### Group 3 Summary: 4 SAFE_MOVE + 1 Archive

---

### Group 4 — Translation Entry Point Chain (CRITICAL External Surface)

These form the production translation surface with direct README.md, lts/, and ntpe_validate.py dependencies.

| # | File | Wrapper? | Decision | Reason |
|---|------|----------|----------|--------|
| 24 | `launcher_translate.py` | N/A | **ALREADY KEEP_ROOT** | This was NOT in the 35 MWW set — it was already classified KEEP_ROOT by RM-4.2B. The JSON dump had it as MWW in error. |
| 25 | `ntpe_translate_batch.py` | **YES** | Wrapper Confirmed | `lts/long_run_recovery.py` subprocess: `python ntpe_translate_batch.py`. 10 lts/*.py files check its path. ntpe_validate REQUIRED_ENTRYPOINTS. Wrapper essential. |
| 26 | `ntpe_translate_txt.py` | **YES** | Wrapper Confirmed | lts/ layer checks path; ntpe_validate requires it. Root wrapper must remain. |

### Group 4 Summary: 2 Wrappers Confirmed

---

### Group 5 — Provider Execution / Enforcer CLLI Tools

Production-grade provider control tools with true CLLI API intent.

| # | File | Wrapper? | Decision | Reason |
|---|------|----------|----------|--------|
| 27 | `ntpe_authorized_provider_invocation.py` | **YES** | Wrapper Confirmed | Imported by `core/` at runtime; referenced by integration tests; TE-V7 manifests |
| 28 | `ntpe_controlled_real_provider_retry.py` | **YES** | Wrapper Confirmed | Integration test references; TE-V7 manifests|
| 29 | `ntpe_lcr_batch107_real_provider_validation.py` | NO | Downgrade → SAFE_MOVE | Zero Python importers; only referenced in archive audit docs |
| 30 | `ntpe_provider_benchmark_session.py` | **YES** | Wrapper Confirmed | 3 integration tests import it; TE-V7 manifests document it |
| 31 | `ntpe_single_real_provider_invocation.py` | **YES** | Wrapper Confirmed | Integration test references; TE-V7 manifest |
| 32 | `ntpe_provider_setup.py` | NO | Downgrade → SAFE_MOVE | Only 1 regression tests references; no README/docsurface |
| 33 | `ntpe_provider_verify.py` | NO | Downgrade → SAFE_MOVE | Only 1 regression test; no external surface |
| 34 | `ntpe_provider_audit.py` | NO | Downgrade → SAFE_MOVE | Only archived test; only RM-3.2 tool refs |

### Group 5 Summary: 4 Wrapper Confirmed / 4 Downgrade → SAFE_MOVE

---

### Group 6 — Misclassified Production Import

| # | File | Wrapper? | Decision | Reason |
|---|------|----------|----------|--------|
| 35 | `ntpe_literary_evaluation.py` | ⚠ MISCLASSIFIED | **Upgrade → KEEP_ROOT** | Imported by `ntpe_production_translate.py` at runtime. Already in KEEP_ROOT list; appears as MWW in error in JSON. |
---

## FINAL SUMMARY — ALL 35 RECLASSIFIED DECISIONS

| Category | Count | Percentage |
|----------|------:|-----------:|
| Wrapper Confirmed | 7 | 20.0% |
| Downgrade → SAFE_MOVE | 26 | 74.3% |
| Upgrade → KEEP_ROOT | 1 | 2.9% |
| Archive | 1 | 2.9% |
| | **35** | **100%** |

### Wrapper Reduction Rate

**Original RM-4.2B MWW count**: 35  
**Genuinely requiring wrapper**: 7  
**Wrapper reduction rate**: **80%** (28 files no longer need a wrapper)

---

## BATCH PLANNING for RM-4.3 Execution

### Batch A: ONE-SHOTS (17 files — SAFE_MOVE, no wrapper)

Zero Python importers. Zero operational CLLI/docs references beyond governance docs.

Target: `tools/one_shots/`

| File |
|------|
| `launcher_analyzer.py` |
| `launcher_character_db.py` |
| `launcher_coverage_test.py` |
| `launcher_expansion_plan.py` |
| `launcher_glossary.py` |
| `launcher_kb.py` |
| `launcher_memory.py` |
| `launcher_novel_prompt_test.py` |
| `launcher_prompt_builder.py` |
| `launcher_profile.py` |
| `launcher_quality_benchmark.py` |
| `launcher_semantic_repair.py` |
| `launcher_semantic_test.py` |
| `launcher_structure_test.py` |
| `launcher_style_expansion.py` |
| `launcher_style_planner_test.py` |
| `launcher_retranslate_chunk.py` |

---

### Batch B: LEGACY PIPELINE DEMOS (5 files — SAFE_MOVE + 1 Archive)

Target: `tools/legacy_pipeline_launchers/`

| File | Action |
|------|--------|
| `launcher_adaptive_recovery.py` | SAFE_MOVE |
| `launcher_pipeline.py` | SAFE_MOVE |
| `launcher_pipeline_production.py` | SAFE_MOVE |
| `launcher_pipeline_recovery.py` | SAFE_MOVE |
| `launcher_pipeline_v1.py` | ARCHIVE → `archive/legacy_tools/` |

---

### Batch C: Provider Utilities (4 files — SAFE_MOVE)

Used only by regression/integration tests; no external CLI surface.

Target: `tools/provider_utils/`

| File |
|------|
| `ntpe_provider_setup.py` |
| `ntpe_provider_verify.py` |
| `ntpe_provider_audit.py` |
| `ntpe_lcr_batch107_real_provider_validation.py` |

**Note:** Tests referencing these by path will need import updates (RM-4.3 scope).

---

### Batch D: Provider Wrappers (4 files — Wrapper Confirmed)

These move with a thin root compatibility stub.

Target: `tools/provider_controls/`
Wrapper pattern: minimal `if __name__ == "__main__": from tools.provider_controls.xxx import main; raise SystemExit(main())`

| File |
|------|
| `ntpe_authorized_provider_invocation.py` |
| `ntpe_controlled_real_provider_retry.py` |
| `ntpe_provider_benchmark_session.py` |
| `ntpe_single_real_provider_invocation.py` |

**Scheduled for RM-4.4 — deferred; higher risk due to import graph.**

---

### Batch E: Translation Entry Wrappers (3 files — CONFIRMED)

| File | Target | Wrapper Needed? | External Binding |
|------|--------|-----------------|------------------|
| `launcher.py` | `tools/translation_adapter/` | **YES** | ntpe_validate REQUIRED_ENTRYPOINTS list; lts/compatibility_validation.py path checks |
| `ntpe_translate_batch.py` | `tools/translation_adapter/` | **YES** | lts/long_run_recovery.py subprocess: `python ntpe_translate_batch.py`; 10 lts/*.py files check path; ntpe_validate REQUIRED_ENTRYPOINTS |
| `ntpe_translate_txt.py` | `tools/translation_adapter/` | **YES** | 9 lts/*.py files check path; ntpe_validate REQUIRED_ENTRYPOINTS |

**Scheduled for RM-4.4.**

---

## VALIDATION GATES (Per Batch for RM-4.3)

| Gate | Check |
|------|-------|
| Python compile | `python -m compileall tools/` zero errors |
| `ntpe_validate.py` | Must pass (path-based checks preserved by wrappers) |
| `git diff --check` | No whitespace violations |
| `git diff --stat` | Only expected files moved |
| `git status` | Only moved; zero in-place content modifications |

---

## IMMEDIATE NEXT STEP

After ACCEPTANCE → **RM-4.3**: Execute Batches A, B, C (26 SAFE_MOVEs in three groups, 1 ARCHIVE).

---

## VALIDATION COMPLIANCE (THIS REPORT)

| Validation | Result | Notes |
|------------|--------|-------|
| `git diff --check` | N/A | No modifications — read-only audit |
| Python modifications | **0** | No files modified |
| Runtime modifications | **0** | No runtime changes |
| Provider Requests | **0** | No provider calls |
| Network Requests | **0** | No network calls |
| Files moved | **0** | No files moved |
| Git commit | **No** | Audit only |
| Git push | **No** | Audit only |