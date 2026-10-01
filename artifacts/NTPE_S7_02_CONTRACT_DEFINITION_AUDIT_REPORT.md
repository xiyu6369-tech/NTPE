# NTPE S7-02 — Product Contract Definition Audit Report

**Audit Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Contract definition audit for S7-01 follow-ups per S7-02 mandate

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Historical baseline commit | `942650df6ac3183d9e566cceb1a9079332cdaaa1` |
| Latest S6 baseline | `96998ac3e99409ca9712aeeb454535107babeaee` |
| Actual HEAD | `96998ac3e99409ca9712aeeb454535107babeaee` ✓ **MATCHES** |
| Origin/main | `942650df6ac3183d9e566cceb1a9079332cdaaa1` |
| Branch | `main` |
| Working tree status | 4 modified, 25 untracked (all pre-existing, no S6 modifications) |

**Baseline Verdict**: `Actual HEAD = Latest S6 baseline = 96998ac` ✓ — No `S7_02_BLOCKED_BASELINE_INCONSISTENCY`

---

## 2. Candidate Selection Summary

| Area | Candidate Contracts | Evidence Priority | Selected Contract | Selection Reason | Unresolved |
|------|---------------------|-------------------|-------------------|------------------|------------|
| ntpe_launcher.py | CURRENT_CONTRACT_REQUIRES_ENTRYPOINT, LEGACY_TEST_OUTDATED | P1-P3 vs P6 | **LEGACY_TEST_OUTDATED** | No explicit product contract mandates ntpe_launcher.py; canonical entrypoints exist (ntpe_production_translate.py, launcher_translate.py, ntpe_translation_studio.py); test is pre-existing, classified OUT OF SCOPE in S7-01 | None |
| EPUB UI | EPUB_UI_IS_FORMAL_PRODUCT_CONTRACT, EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED | P3 (UI labels) vs P4 (implementation) | **EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED** | UI exposes EPUB import/preview but explicitly blocks EPUB translation (TRANSLATION_NOT_SUPPORTED_EPUB); no product spec defines formal EPUB UI contract | Formal EPUB UI contract decision needed |
| Resume persistence | SESSION_ONLY, PROCESS_RESTART, APPLICATION_RESTART, FULL_PERSISTENCE, UNDEFINED | P3 (UI checkbox), P4 (filesystem state), P5 (tests) | **UNDEFINED** | Filesystem state survives process termination but no product contract guarantees cross-session resume; UI checkbox only proves capability exposure, not persistence semantics | Persistence scope contract needed |
| Quality gates | DEFINED (HARD/SOFT/OBSERVATIONAL), UNDEFINED per gate | P1-P3 (literary eval), P4 (QA checks) | **MOSTLY UNDEFINED** | Literary evaluation exists as tooling (PS-03) but no formal acceptance thresholds; QA checks (length_ratio, korean_chars, etc.) are runtime policies not product gates | Quality gate definitions needed |

---

## 3. Follow-up A — ntpe_launcher.py

### 3.1 Current Behavior

- `ntpe_launcher.py` exists at `tools/one_shots/ntpe_launcher.py` (not in repository root)
- Test `test_cli_dry_run_does_not_create_output_or_resume` in `tests/integration/launcher_product/test_launcher_product_integration.py:46` expects to run `subprocess.run([sys.executable, str(ROOT / "ntpe_launcher.py"), "--dry-run", "--config", str(config_path)])` from repository root
- Test fails with: `python.exe: can't open file 'D:\Python\NTPE\ntpe_launcher.py': [Errno 2] No such file or directory`
- Classified in S7-01 as **PRE-EXISTING, OUT OF SCOPE**

### 3.2 Existing Evidence

| Evidence | Source | Priority |
|----------|--------|----------|
| Test expects `ntpe_launcher.py` at repo root | `test_launcher_product_integration.py:69` | P6 (Historical test) |
| `ntpe_launcher.py` exists in `tools/one_shots/` | File system | P4 (Implementation detail) |
| Canonical CLI entrypoints: `ntpe_production_translate.py`, `launcher_translate.py`, `ntpe_translation_studio.py`, `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py` | Root directory listing | P3 (Current product behavior) |
| S7-01 classification: PRE-EXISTING, OUT OF SCOPE | S7-01 Report Section 6 | P2 (Project governance) |
| No CLI documentation references `ntpe_launcher.py` | Documentation search | P1 (Product specification) |
| Root policy prohibits stage scripts in root | `REPOSITORY_GOVERNANCE_BASELINE.md` | P2 (Governance) |

### 3.3 Candidate Contracts

**CANDIDATE_A = CURRENT_CONTRACT_REQUIRES_ENTRYPOINT**
- Evidence: Test exists and expects the entrypoint
- Priority: P6 (Historical test)

**CANDIDATE_B = LEGACY_TEST_OUTDATED**
- Evidence: Multiple canonical entrypoints exist; test is pre-existing failure; S7-01 classified OUT OF SCOPE; root governance prohibits such scripts in root
- Priority: P1-P3 (Product specification, governance, current behavior)

### 3.4 Selection Reason

Per **Rule 4.3** (Current Product Evidence > Historical Evidence) and **Rule 4.2** (Explicit Contract > Observed Behavior):
- No explicit product contract (P1) mandates `ntpe_launcher.py` at root
- Current product behavior (P3) shows 5 canonical entrypoints in root
- Governance (P2) prohibits stage/one-shot scripts in root
- Historical test (P6) cannot establish current product contract

**SELECTED CONTRACT = LEGACY_TEST_OUTDATED**

### 3.5 Contract Status & Decisions

| Decision | Value |
|----------|-------|
| Current Contract Status | **UNDEFINED** — No contract requires `ntpe_launcher.py` at root |
| TEST_DECISION | **REPAIR_TEST** — Test should be updated to use canonical entrypoint or removed as legacy |
| PROGRAM_DECISION | **NO_CHANGE_REQUIRED** — No production change needed; `ntpe_launcher.py` in `tools/one_shots/` is correctly placed |
| S7 Scope Classification | **LEGACY_TEST_REPAIR** |

---

## 4. Follow-up B — EPUB UI Contract

### 4.1 Current Behavior

**Translation Studio (PySide6 - Modern UI)**:
- HomePage has explicit "匯入 EPUB" button with proper file filter (`Strings.EPUB_FILE_FILTER = "EPUB 電子書 (*.epub)"`)
- EPUB import uses `EpubExtractionBoundary` → extraction result → emits `epub_imported` signal
- Supports `success`, `partial`, `manual_review_required`, `blocked` statuses with distinct UI messages
- MainWindow connects `epub_imported` → adds project to ProjectPage with status "已匯入" or "部分匯入"
- **ProjectPage explicitly blocks EPUB translation**: Line 449-451 in `project_page.py`:
  ```python
  if project.get("chapter_map"):
      QMessageBox.warning(self, "提示", Strings.TRANSLATION_NOT_SUPPORTED_EPUB)
      return
  ```
- `Strings.TRANSLATION_NOT_SUPPORTED_EPUB = "EPUB 專案暫不支援直接啟動翻譯"`

**Translation Launcher (Tkinter - Legacy UI)**:
- File dialog includes `("Planned formats", "*.epub *.docx *.pdf")` in `_choose_input` (line 109)
- Controller `_is_epub()` detects `.epub` extension
- `_build_epub_options()` implements full canonical EPUB pipeline (extraction → intake → chunking → `EpubTranslationOptions`)
- Worker `_runtime_epub_translate()` calls canonical `translate_epub_translation_input()` → packaging → EPUB output
- S6-03 acceptance tests (7/7 PASS) verify complete EPUB success/failure/thread-lifecycle/canonical-route/output-artifact paths

### 4.2 Existing Evidence

| Evidence | Source | Priority |
|----------|--------|----------|
| UI label: "匯入 EPUB" button exists | `home_page.py:68-73`, `translations.py:16` | P3 (User-facing claim) |
| UI label: "EPUB 專案暫不支援直接啟動翻譯" | `translations.py:94`, `project_page.py:450` | P3 (User-facing claim - NEGATIVE) |
| EPUB import → extraction → preview works | `home_page.py:235-336`, `test_epub_import_contract.py` (11/11 PASS) | P4 (Implementation) |
| Translation Launcher: full EPUB pipeline implemented | `controller.py:72-220`, `worker.py:101-172` | P4 (Implementation) |
| S6-03 acceptance: 7/7 EPUB tests PASS | `test_s6_03_acceptance.py` | P5 (Acceptance tests) |
| S6 Production User Flow Gap Audit: S6-03 = P1 Major Defect | `NTPE_S6_PRODUCTION_USER_FLOW_GAP_AUDIT.md:74-81` | P2 (Project governance) |
| No product specification mandating EPUB UI translation | Documentation search | P1 (Product specification) |

### 4.3 Candidate Contracts

**CANDIDATE_A = EPUB_UI_IS_FORMAL_PRODUCT_CONTRACT**
- Evidence: UI exposes EPUB import; Translation Launcher implements full EPUB pipeline; S6-03 tests pass
- Priority: P3 (UI labels), P4 (Implementation), P5 (Tests)

**CANDIDATE_B = EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED**
- Evidence: Translation Studio explicitly blocks EPUB translation with "暫不支援" (temporarily not supported); S6 audit classifies as P1 defect; no product spec defines formal EPUB UI contract
- Priority: P3 (Negative user-facing claim), P2 (Governance audit), P1 (No product spec)

### 4.4 Selection Reason

Per **Rule 4.4** (User-Visible Claim Rule): The UI explicitly states `"EPUB 專案暫不支援直接啟動翻譯"` — this is a **negative product claim** that EPUB translation is NOT formally supported in the UI.

Per **Rule 4.3** (Current Product Evidence > Historical): Current product behavior (Translation Studio blocking EPUB translation) overrides implementation existence (Translation Launcher has EPUB pipeline).

Per **Rule 4.5** (Canonical Architecture Rule): Translation Studio is the modern canonical UI (PySide6); Translation Launcher is legacy (Tkinter). The modern UI blocks EPUB translation.

Per **Rule 4.7** (Minimal-Change): Selecting UNDEFINED avoids expanding scope to include EPUB UI translation without explicit product decision.

**SELECTED CONTRACT = EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED**

### 4.5 Contract Status & Decisions

| Decision | Value |
|----------|-------|
| Current Contract Status | **UNDEFINED** — EPUB import/preview is formal; EPUB translation via UI is explicitly NOT supported |
| TEST_DECISION | **ADD_COVERAGE** — Need tests for EPUB UI translation when/if contract is defined |
| PROGRAM_DECISION | **ARCHITECTURE_DEPENDENCY** — Requires canonical route extension to Translation Studio worker (S6-03 P1 defect) |
| S7 Scope Classification | **DEFINE_LATER** — Awaits product decision on EPUB UI translation support |

---

## 5. Follow-up C — Resume Persistence

### 5.1 Current Behavior

**Resume Implementation (TXT - LTS Runtime)**:
- `get_resume_state_path()` → `<output_dir>/<input_stem>_resume_state.json` (line 349-350)
- `load_resume_state()` / `save_resume_state()` — JSON file persistence (lines 353-370)
- Resume check at line 754-760: verifies `options.resume AND status in {"success","pass_with_warning"} AND source_hash matches AND chunk_file.exists() AND chunk_file has content`
- Source hash: `hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]` (line 752)
- `--no-resume` flag via `options.resume` (default True, configurable)
- UI Resume checkbox: `translation_launcher/app.py:65` `ttk.Checkbutton(..., variable=self.variables["resume_enabled"])`
- Character memory & context memory persisted per-chunk (lines 1015-1020, 1018-1020)

**Resume Implementation (EPUB - Adapter Runtime)**:
- `_load_resume_state()` / `_save_json()` at adapter level (lines 792-805, 114-118)
- Resume check at lines 385-389: `options.resume AND status in {"success","pass_with_warning"} AND source_hash matches`
- Source hash: `hashlib.sha256(chunk.source_text.encode("utf-8")).hexdigest()[:16]` (line 363)
- Resume state path: `<output_dir>/<epub_stem>_epub_resume_state.json` (line 304)

**Filesystem Behavior**:
- Resume state files written to output directory (project-specific)
- Chunk output files (`.txt` per chunk) preserved in `chunk_out_dir`
- State survives process termination (filesystem persistence)
- No evidence of cross-application-restart validation logic beyond source_hash

### 5.2 Existing Evidence

| Evidence | Source | Priority |
|----------|--------|----------|
| Resume checkbox in UI | `app.py:65`, `translations.py:158` | P3 (User-facing capability exposure) |
| `--no-resume` flag in CLI/config | `launcher_product/models.py`, `command_builder.py` | P3 (User-facing capability exposure) |
| Chunk-level resume with source_hash verification | `txt_translation_runtime.py:754-760`, `adapter.py:385-389` | P4 (Implementation) |
| Resume state persisted to filesystem | `save_resume_state()` calls at lines 800, 999, 1000, 589 | P4 (Implementation) |
| Chunk output files preserved | `chunk_file.exists()` check in resume logic | P4 (Implementation) |
| S6-02/03 regression tests verify chunk-level resume | S7-01 Report Section 4 | P5 (Tests) |
| No test for cross-session/application restart resume | Test search | P5 (Tests - NEGATIVE) |
| No documentation defining persistence semantics | Documentation search | P1 (Product specification) |
| No UI/CLI claim about "survives restart" | UI strings, CLI help | P3 (User-facing claim - ABSENT) |

### 5.3 Candidate Contracts

| Candidate | Definition | Evidence Support |
|-----------|------------|------------------|
| SESSION_ONLY | Resume only within same execution session | Weak — filesystem persistence implemented |
| PROCESS_RESTART | Resume after process ends, same product re-run | Moderate — state files persist, source_hash validates |
| APPLICATION_RESTART | Resume after full application close/reopen | Weak — no explicit guarantee, same mechanism as process |
| FULL_PERSISTENCE | Cross-machine/environment with full identity/verification rules | None — no evidence |
| UNDEFINED | No formal contract defines persistence scope | Strong — no product spec, no user-facing guarantee, no test |

### 5.4 Selection Reason

Per **Rule 4.7** (Minimal-Change Selection Rule): Evidence only proves chunk-level resume with source_hash verification exists in current process. Filesystem persistence is an **implementation detail** (P4), not a product guarantee.

Per **Rule 4.4** (User-Visible Claim Rule): UI checkbox and `--no-resume` flag only prove "resume is exposed as a user-facing capability" — **not** that it survives application restart.

Per **Rule 4.9** (Ambiguity Rule): Multiple candidates (PROCESS_RESTART vs APPLICATION_RESTART vs SESSION_ONLY) have similar evidence priority (P4 implementation). Cannot reasonably distinguish.

Per **Rule 4.8** (Quality-First): Not inventing arbitrary persistence scope without product definition.

**SELECTED CONTRACT = UNDEFINED**

### 5.5 Contract Status & Decisions

| Decision | Value |
|----------|-------|
| Current Contract Status | **UNDEFINED** — Chunk-level resume with source_hash exists; persistence scope not defined |
| TEST_DECISION | **ADD_COVERAGE** — Need tests defining persistence scope if contract is established |
| PROGRAM_DECISION | **ARCHITECTURE_DEPENDENCY** — Requires persistence layer design (storage, identity, validation, migration) |
| S7 Scope Classification | **DEFINE_LATER** — Awaits product decision on persistence semantics |

---

## 6. Follow-up D — Translation Quality Gates

### 6.1 Current Behavior

**Runtime QA Policies (Machine-Checkable, Enforced During Translation)**:
- `min_length_ratio=0.18` — Minimum translation length vs source (configurable)
- `max_korean_chars=2` — Maximum Korean residue characters allowed
- `max_repeated_lines=2` — Maximum repeated lines
- `simplified_chinese_policy="normalize|warn|fail"` — Simplified Chinese handling
- `qa_fail_policy="retry|fail|warn"` — Action on QA failure
- `strict_lock_terms=True` — Glossary/name enforcement (pre/post translation)
- `quality_v5_enabled=True` — Quality V5 pipeline (completeness, naturalness, terminology)
- `quality_integration_v72` — Cross-chunk context quality (feature-gated)
- `quality_character_memory_v72` — Character consistency (feature-gated)
- `quality_context_scene_v72` — Scene continuity (feature-gated)
- `quality_naturalness_v72` — Naturalness scoring (feature-gated)

**Literary Quality Evaluation (PS-03 Tooling)**:
- `ntpe_literary_evaluation.py` evaluates translation quality across metrics:
  1. Plot fidelity proxy (length ratio) — 30 pts
  2. Locked names/terms consistency — 20 pts
  3. Natural Chinese proxy (Korean residue, Chinese density, preface detection) — 20 pts
  4. Subject/pronoun proxy — 15 pts
  5. Character voice/dialogue proxy — 10 pts
  6. Format/punctuation/simplified residue — 5 pts
- **Total: 100 pts**, status thresholds: ≥80=success, ≥65=warning, <65=failed
- Runs as **post-hoc evaluation** on test sets (Smoke_Set, Golden_Set, Regression_Set)
- **Not integrated into translation pipeline** — no gate blocks translation

**Production Route Quality**:
- Single canonical route: `TranslationRuntime → TranslationEngine → ProviderManager → NvidiaClient → M3`
- Retry policies: 2 attempts, 10s base backoff (conservative strategy per project.md)
- Model: `meta/llama-3.2-90b-vision-instruct` (fixed across 9 config files)

### 6.2 Candidate Classification per Quality Requirement

| Quality Requirement | Contract Status | Gate Type | Evidence |
|---------------------|-----------------|-----------|----------|
| Terminology consistency (locked names) | **DEFINED** | HARD GATE (runtime enforced) | `strict_lock_terms`, `LOCKED_TERMS`, alias map applied pre/post |
| Character-name consistency | **DEFINED** | HARD GATE (runtime) | Character memory v2, glossary system, locked dictionary |
| Source fidelity (length ratio) | **DEFINED** | HARD GATE (runtime) | `min_length_ratio=0.18`, QA fail policy |
| Traditional Chinese output | **DEFINED** | HARD GATE (runtime) | `taiwan_traditional_normalization=True`, replacements applied |
| Korean residue detection | **DEFINED** | HARD GATE (runtime) | `max_korean_chars=2`, QA fail policy |
| Untranslated residue | **DEFINED** | HARD GATE (runtime) | Length ratio + Korean residue + QA |
| Format preservation | **DEFINED** | HARD GATE (runtime) | `output_formatter_enabled`, punctuation normalization |
| Chapter completeness | **DEFINED** (EPUB) | HARD GATE (contract) | EPUB contract validation, chapter_map integrity |
| Sentence/chunk completeness | **DEFINED** | HARD GATE (runtime) | QA V5 completeness checks |
| Literary quality threshold | **UNDEFINED** | OBSERVATIONAL (PS-03) | PS-03 scoring exists but no gate in pipeline |
| Naturalness score threshold | **UNDEFINED** | OBSERVATIONAL (PS-03) | Naturalness proxy in PS-03, no pipeline gate |
| Consistency across chapters | **UNDEFINED** | SOFT METRIC (feature-gated) | `quality_context_scene_v72` flag exists but off by default |
| Reader-quality / literary quality | **UNDEFINED** | ASPIRATIONAL | Core product goal stated but no measurable contract |

### 6.3 Selection Reason

Per **Rule 4.8** (Quality-First Selection Rule): Quality aspirations (reader-quality, naturalness, literary quality) **cannot** be automatically converted to PASS/FAIL gates without:
1. Measurement method
2. Threshold
3. Acceptance semantics

Per **Rule 4.4** (User-Visible Claim Rule): Product states "reader-quality novel translation" as aspiration, but UI/CLI makes no measurable quality guarantees.

Per **Rule 4.7** (Minimal-Change): Existing runtime QA policies are **HARD GATES** with defined thresholds. PS-03 metrics are **OBSERVATIONAL** tooling. Not promoting observational to hard gate.

Per **Rule 4.6** (Test Evidence Rule): PS-03 tests pass/fail based on arbitrary thresholds (80/65) — these are evaluation criteria, not product acceptance contracts.

### 6.4 Contract Status & Decisions

| Quality Area | Contract Status | Gate Type | TEST_DECISION | PROGRAM_DECISION |
|--------------|-----------------|-----------|---------------|------------------|
| Locked terms/names | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Length ratio / fidelity | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Korean residue | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Traditional Chinese | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Format/punctuation | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Chapter completeness (EPUB) | DEFINED | HARD GATE | NO_CHANGE | NO_CHANGE_REQUIRED |
| Literary quality threshold | UNDEFINED | OBSERVATIONAL | ADD_COVERAGE | ARCHITECTURE_DEPENDENCY |
| Naturalness threshold | UNDEFINED | OBSERVATIONAL | ADD_COVERAGE | ARCHITECTURE_DEPENDENCY |
| Cross-chapter consistency | UNDEFINED | FEATURE-GATED SOFT | ADD_COVERAGE | ARCHITECTURE_DEPENDENCY |
| Reader-quality aspiration | UNDEFINED | ASPIRATIONAL | NO_CHANGE | NO_CHANGE_REQUIRED |

| Decision | Value |
|----------|-------|
| Overall Contract Status | **PARTIALLY DEFINED** — Runtime QA gates defined; literary quality gates undefined |
| TEST_DECISION | **ADD_COVERAGE** for undefined gates |
| PROGRAM_DECISION | **ARCHITECTURE_DEPENDENCY** for quality pipeline integration |
| S7 Scope Classification | **KEEP_AS_DEFINED_CONTRACT** (for runtime QA) + **DEFINE_LATER** (for literary quality gates) |

---

## 7. Test Decision / Program Decision Summary

| Area | Candidate Contracts | Selected Contract | Evidence | TEST_DECISION | PROGRAM_DECISION |
|------|---------------------|-------------------|----------|---------------|------------------|
| ntpe_launcher.py | CURRENT_CONTRACT_REQUIRES_ENTRYPOINT, LEGACY_TEST_OUTDATED | **LEGACY_TEST_OUTDATED** | P1-P3 > P6 | **REPAIR_TEST** | **NO_CHANGE_REQUIRED** |
| EPUB UI | EPUB_UI_IS_FORMAL_PRODUCT_CONTRACT, EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED | **EPUB_UI_IS_EXISTING_CAPABILITY_BUT_CONTRACT_UNDEFINED** | P3 (negative claim) > P4 | **ADD_COVERAGE** | **ARCHITECTURE_DEPENDENCY** |
| Resume persistence | SESSION_ONLY, PROCESS_RESTART, APPLICATION_RESTART, FULL_PERSISTENCE, UNDEFINED | **UNDEFINED** | P4 only, no P1-P3 | **ADD_COVERAGE** | **ARCHITECTURE_DEPENDENCY** |
| Quality gates | Per-gate classification (see Section 6.2) | **PARTIALLY DEFINED** | Runtime QA = DEFINED; Literary = UNDEFINED | **NO_CHANGE** (defined) / **ADD_COVERAGE** (undefined) | **NO_CHANGE_REQUIRED** (defined) / **ARCHITECTURE_DEPENDENCY** (undefined) |

---

## 8. Implementation Authorization

Per S7-02 mandate: **No production implementation authorized in this task.**

| Area | PROGRAM_DECISION | Authorization |
|------|------------------|---------------|
| ntpe_launcher.py | NO_CHANGE_REQUIRED | **NO_PRODUCTION_CHANGE** — Test repair only |
| EPUB UI | ARCHITECTURE_DEPENDENCY | **S7_02_BLOCKED_ARCHITECTURE_DEPENDENCY** — Requires Translation Studio worker extension |
| Resume persistence | ARCHITECTURE_DEPENDENCY | **S7_02_BLOCKED_ARCHITECTURE_DEPENDENCY** — Requires persistence layer design |
| Quality gates (runtime QA) | NO_CHANGE_REQUIRED | **NO_PRODUCTION_CHANGE** — Already implemented |
| Quality gates (literary) | ARCHITECTURE_DEPENDENCY | **S7_02_BLOCKED_ARCHITECTURE_DEPENDENCY** — Requires quality pipeline integration |

**No items authorized for future implementation in this audit cycle.** All UNDEFINED/ARCHITECTURE_DEPENDENCY items require explicit product decisions before any implementation.

---

## 9. S7 Scope Classification

| Follow-up | Final Classification | Rationale |
|-----------|---------------------|-----------|
| ntpe_launcher.py | **LEGACY_TEST_REPAIR** | Test is legacy; no product contract requires entrypoint |
| EPUB UI contract | **DEFINE_LATER** | UI explicitly states "not supported"; needs product decision |
| Resume persistence | **DEFINE_LATER** | Implementation exists but no persistence scope contract |
| Translation quality gates | **KEEP_AS_DEFINED_CONTRACT** + **DEFINE_LATER** | Runtime QA gates defined; literary quality gates need product decision |

---

## 10. Final Verdict

**Case B applies: `S7_02_CONTRACT_DEFINITION_INCOMPLETE`**

### Rationale

1. **ntpe_launcher.py**: Resolved — test is legacy, no contract violation
2. **EPUB UI**: Incomplete — Translation Studio explicitly blocks EPUB translation ("暫不支援"); Translation Launcher has implementation but is legacy UI; no product contract defines EPUB UI translation support
3. **Resume persistence**: Incomplete — Filesystem persistence implemented but no product contract defines scope (SESSION_ONLY vs PROCESS_RESTART vs APPLICATION_RESTART vs FULL_PERSISTENCE)
4. **Quality gates**: Partially incomplete — Runtime QA gates (length, Korean residue, Traditional Chinese, locked terms, format) are DEFINED and enforced; literary quality gates (naturalness, cross-chapter consistency, reader-quality) are UNDEFINED aspirations

**No production defects identified** (Case C).
**No protected architecture modifications needed** (Case D not triggered — architecture dependencies acknowledged but not modified).

---

## 11. Completion Definition Status

| Requirement | Status |
|-------------|--------|
| S7-01 follow-ups audited | ✅ |
| Candidate contracts identified | ✅ |
| Candidate selection rules applied | ✅ |
| Each contract explicitly classified | ✅ |
| Selection evidence recorded | ✅ |
| Test Decision separated from Program Decision | ✅ |
| Future implementation scope identified | ✅ |
| No premature production changes | ✅ |

---

## 12. Recommendations for Future Work

### Immediate (Test Repair Only)
1. **Fix `test_cli_dry_run_does_not_create_output_or_resume`** — Update to use `launcher_translate.py` or `ntpe_production_translate.py txt` as canonical CLI entrypoint, or remove as legacy test

### Requires Product Decision (Define Later)
2. **Define EPUB UI translation contract** — Product must decide: formal support in Translation Studio? If yes, extend TranslationWorker for EPUB (S6-03 P1 defect)
3. **Define resume persistence semantics** — Product must define: SESSION_ONLY / PROCESS_RESTART / APPLICATION_RESTART / FULL_PERSISTENCE
4. **Define literary quality gates** — Product must define measurable thresholds for: naturalness, cross-chapter consistency, reader-quality; integrate into pipeline as HARD/SOFT gates

### Out of Scope (Governance Compliant)
5. Root hygiene — Already compliant (no `ntpe_launcher.py` in root)
6. Artifact cleanup — Preserved per mandate
7. Historical test cleanup — Pre-existing, not S6/S7 responsibility

---

*End of Audit Report*

**Report Path**: `artifacts/NTPE_S7_02_CONTRACT_DEFINITION_AUDIT_REPORT.md`
**Audit Complete**: `S7_02_CONTRACT_DEFINITION_AUDIT_COMPLETE`