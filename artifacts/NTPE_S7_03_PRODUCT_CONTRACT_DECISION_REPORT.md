# NTPE S7-03 — Product Contract Decision & Scope Lock Report

**Decision Date**: 2026-09-30
**Auditor**: Kilo (Automated)
**Scope**: Formal product contract decisions based on S7-02 audit results

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| HEAD | `96998ac3e99409ca9712aeeb454535107babeaee` ✓ **MATCHES S6 BASELINE** |
| Branch | `main` |
| Origin/main | `942650df6ac3183d9e566cceb1a9079332cdaaa1` |
| Working tree | 4 modified, 25 untracked (all pre-existing, no S6/S7 modifications) |

**Baseline Verdict**: `Actual HEAD = 96998ac` ✓ — No `S7_03_BLOCKED_BASELINE_INCONSISTENCY`

---

## 2. S7-02 Result

```
S7_02_CONTRACT_DEFINITION_INCOMPLETE
```

S7-02 identified four follow-up areas with candidate contracts. S7-03 now makes explicit product decisions to lock scope for future implementation.

---

## 3. Final Product Contracts

### Decision A — ntpe_launcher.py

| Attribute | Decision |
|-----------|----------|
| **CONTRACT** | `LEGACY_TEST_OUTDATED` |
| **PROGRAM_DECISION** | `NO_CHANGE_REQUIRED` |
| **TEST_DECISION** | `REPAIR_TEST` |
| **S7 Scope Classification** | `LEGACY_TEST_REPAIR` |

**Final Scope Lock**:
- Do NOT restore `ntpe_launcher.py` to repository root
- Do NOT create compatibility launcher wrapper
- Do NOT alter canonical CLI route (`ntpe_production_translate.py`, `launcher_translate.py`, `ntpe_translation_studio.py`, `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py`)
- Future test maintenance may repair/remove the legacy test independently (`LEGACY_TEST_REPAIR`)

**Rationale**: S7-02 applied Rule 4.3 (Current Product Evidence > Historical) and Rule 4.2 (Explicit Contract > Observed Behavior). No P1 product specification mandates `ntpe_launcher.py`; 5 canonical entrypoints exist; governance prohibits one-shot scripts in root.

---

### Decision B — EPUB UI

| Attribute | Decision |
|-----------|----------|
| **CONTRACT** | `DEFINED — EPUB officially supported as input format` |
| **PROGRAM_DECISION** | `MINIMAL_CHANGE_REQUIRED` (via future implementation task) |
| **TEST_DECISION** | `ADD_COVERAGE` / existing S6-03 coverage audit |
| **S7 Scope Classification** | `IMPLEMENTATION_REQUIRED` |

**Required Contract Semantics**:
- EPUB input accepted through Translation Studio UI
- EPUB validation performed via `EpubExtractionBoundary`
- Canonical EPUB extraction used (no bypass)
- Canonical translation runtime used (`translate_epub_translation_input`)
- EPUB output generated via `pack_epub_resource_aware`
- Execution state accurately represented in UI
- Failure state accurately represented in UI

**Architecture Constraint (LOCKED)**:
- MUST reuse: `Controller → Worker → translate_epub_translation_input → canonical EPUB runtime → pack_epub_resource_aware → EPUB output`
- MUST NOT create: second EPUB runtime, second EPUB translator, second EPUB packager, UI-only translation path
- MUST NOT modify: `TranslationRuntime`, `TranslationEngine`, `ProviderManager`, `NvidiaTranslationProvider`, `NvidiaClient`

**Architecture Dependency**: S7-02 identified Translation Studio worker lacks EPUB execution path (S6-03 P1 defect). Future task must extend `TranslationWorker` for EPUB support within canonical route.

**Rationale**: S7-02 applied Rule 4.4 (User-Visible Claim Rule) — modern UI (Translation Studio) explicitly states "EPUB 專案暫不支援直接啟動翻譯". Rule 4.3 (Current Product Evidence) — modern PySide6 UI is canonical, not legacy Tkinter launcher. Rule 4.5 (Canonical Architecture Rule) — must follow canonical route. Product decision: EPUB IS formally supported; implementation gap must be closed.

---

### Decision C — Resume Persistence

| Attribute | Decision |
|-----------|----------|
| **CONTRACT** | `PROCESS_RESTART` |
| **PROGRAM_DECISION** | `MINIMAL_CHANGE_REQUIRED` (via future persistence task) |
| **TEST_DECISION** | `ADD_COVERAGE` |
| **S7 Scope Classification** | `IMPLEMENTATION_REQUIRED` |

**Explicit Contract Definition**:

```
INCLUDES:
- Process termination and restart
- Chunk-level resume with source-hash verification
- Existing resume state file persistence
- Identity verification (source hash matching)
- Safe refusal on verification failure

DOES NOT REQUIRE:
- Application-wide session management
- Cross-machine synchronization
- Cloud persistence
- Account-based persistence
- Distributed resume state
- APPLICATION_RESTART (explicitly excluded from minimal contract)
- FULL_PERSISTENCE (explicitly excluded from minimal contract)
```

**Required Safety Semantics (MANDATORY for implementation)**:
- Source file changed → refuse unsafe resume
- Source hash mismatch → refuse unsafe resume
- Resume state corrupted → fail safely (explicit error, no silent resume)
- Resume state stale → fail safely
- Output/chunk identity inconsistent → refuse unsafe resume
- NO blind resume based solely on resume file existence

**Architecture Constraint (LOCKED)**:
- MUST NOT modify: `TranslationRuntime`, `TranslationEngine`, `ProviderManager`, `NvidiaTranslationProvider`, `NvidiaClient`
- MUST NOT modify: model, provider, prompt, fallback, retry policies
- Implementation limited to persistence layer design within existing runtime boundaries

**Rationale**: S7-02 applied Rule 4.7 (Minimal-Change Selection Rule). Evidence supports chunk-level resume with filesystem persistence (P4), but no P1-P3 evidence for APPLICATION_RESTART or FULL_PERSISTENCE. Rule 4.9 (Ambiguity Rule) — multiple candidates had similar evidence priority; PROCESS_RESTART is minimal explicit scope. Rule 4.8 (Quality-First) — safety semantics prioritized over convenience.

---

### Decision D — Translation Quality Gates

#### D.1 Runtime QA Gates (EXISTING — LOCKED)

| Gate | Status | Gate Type | Policy |
|------|--------|-----------|--------|
| Length validation (`min_length_ratio=0.18`) | `DEFINED` | `HARD_GATE` | `qa_fail_policy` enforced |
| Korean residue detection (`max_korean_chars=2`) | `DEFINED` | `HARD_GATE` | `qa_fail_policy` enforced |
| Traditional Chinese validation | `DEFINED` | `HARD_GATE` | `taiwan_traditional_normalization=True` |
| Locked-term validation | `DEFINED` | `HARD_GATE` | `strict_lock_terms=True` |
| Format/punctuation validation | `DEFINED` | `HARD_GATE` | `output_formatter_enabled=True` |
| Chapter completeness (EPUB) | `DEFINED` | `HARD_GATE` | Contract validation enforced |

**Program Decision**: `NO_CHANGE_REQUIRED` — Preserve existing gates; do not lower or delete.

#### D.2 Literary Quality Gates (UNDEFINED — LOCKED FOR NOW)

| Quality Aspect | Status | Gate Type | Notes |
|----------------|--------|-----------|-------|
| Naturalness | `UNDEFINED` | `OBSERVATIONAL` (PS-03 tooling) | No PASS/FAIL threshold |
| Literary quality | `UNDEFINED` | `OBSERVATIONAL` (PS-03 tooling) | No PASS/FAIL threshold |
| Reader-quality | `UNDEFINED` | `ASPIRATIONAL` | Core product goal, not contract |
| Cross-chapter consistency | `UNDEFINED` | `FEATURE-GATED SOFT` | `quality_context_scene_v72` off by default |
| Overall consistency | `UNDEFINED` | `OBSERVATIONAL` | PS-03 evaluation only |

**Program Decision**: `NO_CHANGE_REQUIRED` for now — Do NOT implement literary quality gates.

**Explicit Prohibitions (LOCKED)**:
- NO `literary_score >= 80` or any arbitrary threshold
- NO `naturalness >= 85` or any arbitrary threshold
- NO `reader_quality >= 90` or any arbitrary threshold
- NO ranking / quality tier / release score systems
- NO automatic PASS/FAIL for literary quality

**Future Authorization Path**: Requires separate `QUALITY-CONTRACT-DESIGN` task with:
1. Measurement method
2. Threshold definition
3. Acceptance semantics
4. Product decision authorization

**Rationale**: S7-02 applied Rule 4.8 (Quality-First). Machine-verifiable gates = HARD GATE. Literary quality = UNDEFINED aspiration. Rule 4.4 — no user-facing measurable quality guarantee exists. Rule 4.7 — minimal change: keep defined gates, defer undefined.

---

## 4. Candidate Selection Record (Per S7-02 Rule 4.12)

### ntpe_launcher.py

| Candidate | Evidence Priority | Selected | Reason |
|-----------|-------------------|----------|--------|
| CURRENT_CONTRACT_REQUIRES_ENTRYPOINT | P6 (Historical test) | ❌ | P6 cannot override P1-P3 |
| LEGACY_TEST_OUTDATED | P1-P3 (Product spec, governance, current behavior) | ✅ | Higher priority evidence; test pre-existing, OUT OF SCOPE |

### EPUB UI

| Candidate | Evidence Priority | Selected | Reason |
|-----------|-------------------|----------|--------|
| EPUB_UI_IS_FORMAL_PRODUCT_CONTRACT | P3 (UI labels), P4 (impl), P5 (tests) | ❌ | Contradicted by P3 negative claim ("暫不支援") |
| EPUB_UI_EXISTING_CAPABILITY_BUT_UNDEFINED | P3 (negative claim), P2 (governance), P1 (no spec) | ✅ | Modern UI is canonical; explicit negative claim; no product spec |

### Resume Persistence

| Candidate | Evidence Priority | Selected | Reason |
|-----------|-------------------|----------|--------|
| SESSION_ONLY | P4 (impl) | ❌ | Filesystem persistence implemented |
| PROCESS_RESTART | P4 (impl) | ✅ | Minimal explicit scope matching evidence |
| APPLICATION_RESTART | P4 (impl) | ❌ | Same mechanism as PROCESS_RESTART; no P1-P3 distinction |
| FULL_PERSISTENCE | None | ❌ | No evidence |
| UNDEFINED | P5 (tests - NEGATIVE), P1 (no spec) | — | Ambiguity Rule: multiple P4 candidates; minimal explicit chosen |

### Quality Gates

| Candidate | Evidence Priority | Selected | Reason |
|-----------|-------------------|----------|--------|
| Runtime QA gates as HARD_GATE | P1-P4 (explicit config, runtime enforcement) | ✅ | Explicit contract; machine-verifiable; enforced |
| Literary quality as HARD_GATE | P4 (PS-03 tooling) | ❌ | No measurement method + threshold + acceptance semantics |
| Literary quality as UNDEFINED/OBSERVATIONAL | P1 (no spec), P3 (aspirational claim) | ✅ | Quality-First Rule; no arbitrary promotion |

---

## 5. Scope Lock — Authorized Future Implementation Boundaries

### Scope 1 — EPUB UI Execution Repair

| Authorized | Not Authorized |
|------------|----------------|
| Extend `TranslationWorker` for EPUB via canonical route | New EPUB runtime/architecture |
| Connect Translation Studio UI to `translate_epub_translation_input` | Provider/model change |
| Implement EPUB validation/execution/output state in UI | Prompt/fallback/retry modification |
| Complete S6-03 contract coverage for UI EPUB path | Second translation path |

**Boundary**: Strictly `Controller → Worker → canonical EPUB runtime → pack_epub_resource_aware`

### Scope 2 — Resume Persistence Implementation

| Authorized | Not Authorized |
|------------|----------------|
| PROCESS_RESTART semantics implementation | FULL_PERSISTENCE |
| Resume state persistence layer | Distributed/cloud persistence |
| Identity verification (source hash) | Application session management |
| Stale/corrupt state safe handling | New provider/model/architecture |
| CLI/UI consistency for resume | Architecture rewrite |

**Boundary**: Strictly within existing `TranslationRuntime` checkpoint/resume mechanisms; no protected component modification.

### Scope 3 — Quality Contract Expansion

| Authorized | Not Authorized | Deferred |
|------------|----------------|----------|
| — | Literary quality HARD_GATE | Requires `QUALITY-CONTRACT-DESIGN` task first |
| — | Naturalness threshold | Requires product decision + measurement method |
| — | Reader-quality PASS/FAIL | Requires `QUALITY-CONTRACT-DESIGN` task first |
| — | Cross-chapter consistency gate | Feature-gated; off by default |
| Preserve existing runtime QA gates | Lower/remove existing gates | — |

**Boundary**: NO literary quality gate implementation until formal quality contract design is authorized.

---

## 6. Test Decision / Program Decision Matrix

| Area | TEST_DECISION | PROGRAM_DECISION |
|------|---------------|------------------|
| `ntpe_launcher.py` | `REPAIR_TEST` | `NO_CHANGE_REQUIRED` |
| EPUB UI | `ADD_COVERAGE` | `MINIMAL_CHANGE_REQUIRED` (future task) |
| Resume Persistence | `ADD_COVERAGE` | `MINIMAL_CHANGE_REQUIRED` (future task) |
| Existing Runtime QA Gates | `NO_CHANGE` | `NO_CHANGE_REQUIRED` |
| Literary Quality | `ADD_COVERAGE` (when contract defined) | `NO_CHANGE_REQUIRED` (for now) |

**Note on ARCHITECTURE_DEPENDENCY**: S7-02 classified EPUB UI and Resume as `ARCHITECTURE_DEPENDENCY` meaning "currently cannot implement directly." S7-03 product decisions reclassify future implementation tasks as `MINIMAL_CHANGE_REQUIRED` **IF AND ONLY IF** implementation stays within locked architecture boundaries. If implementation requires protected architecture modification: STOP → `ARCHITECTURE_DEPENDENCY` → do not implement.

---

## 7. Protected Architecture (PERMANENTLY FROZEN)

| Component | Status |
|-----------|--------|
| `TranslationRuntime` | FROZEN |
| `TranslationEngine` | FROZEN |
| `ProviderManager` | FROZEN |
| `NvidiaTranslationProvider` | FROZEN |
| `NvidiaClient` | FROZEN |
| Model: `meta/llama-3.2-90b-vision-instruct` | FROZEN (across all 9 config files) |
| Provider: `nvidia` | FROZEN |
| Prompt / Fallback / Retry | FROZEN |

**No exceptions** for EPUB, Resume, or Quality work. Any future task requiring modification must obtain formal architecture authorization.

---

## 8. Final Verdict

```
S7_03_PRODUCT_CONTRACTS_LOCKED
```

### Lock Confirmation

| Decision Area | Locked Contract | Authority |
|---------------|-----------------|-----------|
| ntpe_launcher.py | LEGACY_TEST_OUTDATED | S7-03 Product Decision |
| EPUB UI | DEFINED (officially supported) | S7-03 Product Decision |
| Resume Persistence | PROCESS_RESTART | S7-03 Product Decision |
| Runtime QA Gates | DEFINED (HARD_GATE) | S7-03 Product Decision |
| Literary Quality | UNDEFINED / OBSERVATIONAL | S7-03 Product Decision |

### Future Executor Constraints

After S7-03, no executor may:
- Re-litigate EPUB support status (DEFINED = supported)
- Propose APPLICATION_RESTART or FULL_PERSISTENCE for resume (LOCKED = PROCESS_RESTART)
- Invent literary quality thresholds (LOCKED = UNDEFINED)
- Modify protected architecture for any of the above
- Treat UNDEFINED as authorization for implementation

---

## 9. Completion Definition Status

| Requirement | Status |
|-------------|--------|
| S7-02 incomplete contracts addressed | ✅ |
| Explicit product decisions made | ✅ |
| Candidate alternatives rejected with reasons | ✅ |
| Formal contracts locked | ✅ |
| Future implementation boundaries locked | ✅ |
| Test/Program decisions separated | ✅ |
| Protected architecture unchanged | ✅ |
| No production modification | ✅ |
| Report produced | ✅ |

---

*End of Decision Report*

**Report Path**: `artifacts/NTPE_S7_03_PRODUCT_CONTRACT_DECISION_REPORT.md`
**Decision Complete**: `S7_03_PRODUCT_CONTRACTS_LOCKED`