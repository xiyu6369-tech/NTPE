# NTPE S7-12 Literary Calibration Design v1.1 Independent Re-Audit

**Audit Date**: 2026-09-30
**Auditor**: Kilo (Automated) — Independent of S7-11
**Scope**: Independent re-audit of `NTPE_S7_11_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_V1_1.md`
**Audit Type**: Evidence Verification → Methodology Consistency Review → Pilot Authorization Decision

---

## 1. Baseline

| Metric | Value |
|--------|-------|
| Baseline HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Actual HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Branch | `main` |
| Upstream | `origin/main` (tracking, not modified) |
| Origin | `https://github.com/xiyu6369-tech/NTPE.git` |

**Working Tree Status (pre-existing, preserved, untouched):**

```
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? (25+ pre-existing untracked artifacts + tests/contract/* + core/epub_translation/*)
```

No destructive git operation was run. Pre-existing changes fully preserved (S7-12 §57).

---

## 2. Input Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| S7-07 Contract | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md` | ✅ CONSUMED |
| S7-07 Report | `artifacts/NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1_REPORT.md` | ✅ CONSUMED |
| S7-08 Audit | `artifacts/NTPE_S7_08_LITERARY_QUALITY_EVIDENCE_CALIBRATION_AUDIT_REPORT.md` | ✅ CONSUMED |
| S7-09 Design v1.0 | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md` | ✅ CONSUMED |
| S7-09 Report | `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_REPORT.md` | ✅ CONSUMED |
| S7-10 Internal Audit | `artifacts/NTPE_S7_10_LITERARY_CALIBRATION_DESIGN_INTERNAL_AUDIT_REPORT.md` | ✅ CONSUMED |
| S7-11 Design v1.1 | `artifacts/NTPE_S7_11_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN_V1_1.md` | ✅ CONSUMED |
| S7-11 Revision Report | `artifacts/NTPE_S7_11_LITERARY_CALIBRATION_DESIGN_REVISION_REPORT.md` | ✅ CONSUMED |

S7-11 created **no** separate changelog artifact (explicitly stated in its report §3); revision deltas are embedded in the report + v1.1. No missing supporting artifact.

---

## 3. Independence Statement

S7-12 did **not** accept any S7-11 `RESOLVED` claim at face value. Each H01–H08 was re-opened, traced to the v1.1 text, and independently judged. S7-11 `Claim` columns are excluded from `Independent Evidence` in the closure matrix (§21). Where the v1.1 text only partially satisfies an S7-10 requirement, the finding is recorded as `PARTIALLY_CLOSED` rather than `CLOSED_VERIFIED`. Two internal ambiguities and one missing-data specificity gap were found that S7-11 did not self-report (§19, §20).

---

## 4. Audit Scope

Q1–Q16 from the mandate were answered by re-reading v1.1 in full (804 lines) against v1.0 (952 lines), S7-10 (558 lines), and the frozen production code. No calibration, pilot, human evaluation, translation, or provider execution occurred.

---

## 5. S7-10 Finding Re-Verification

S7-10 did not emit a literal `H01…H08` list; it emitted a 25-row findings matrix with 8+ HIGH items. S7-11 mapped these to H01–H08. S7-12 independently re-derived that mapping and confirmed it is faithful:

| S7-12 | S7-10 source | S7-10 Severity |
|-------|--------------|----------------|
| H01 Sample Size / Pilot | §5.3, matrix #1/#11 | HIGH |
| H02 Clustering / n_eff | §5.1, §5.4, matrix #2/#11 | HIGH |
| H03 Rubric Orthogonality | §5.6, matrix #3 | HIGH |
| H04 Ordinal Methods | §5.7, matrix #4 | HIGH |
| H05 Agreement Metrics | §5.9, matrix #6/#16 | HIGH |
| H06 Numerical Targets | §5.11, matrix #7/#17 | HIGH |
| H07 Weight Optimization | §5.13/#5.14, matrix #8/#18 | HIGH |
| H08 Reference Contamination | §5.21, matrix #9/#25 | HIGH |

All eight HIGH findings were re-audited. The S7-10 verdict (`S7_10_CALIBRATION_DESIGN_REQUIRES_REVISION`) is the correct comparison baseline; no standard was relaxed.

---

## 6. H01 Sample Size Audit

- **Claim**: 50 passages = PILOT_ONLY; formal sample size TBD pending power analysis.
- **Evidence**: v1.1 §7.1 table (`Pilot … 50 passages … PILOT_ONLY`); §7.1 explicit bullet list of what 50 *cannot* support; §30.2 pilot scope; §28 Sample Size Matrix row `Pilot | – | 50 | cluster-aware | – | PILOT_ONLY`; §26 registry row `Pilot passages | 50 | PILOT_ONLY`.
- **Verification**: Grepped every occurrence of `50` and of `PILOT_ONLY` in v1.1. **No** occurrence links 50 to calibration sufficiency or threshold validation. The only `50` outside pilot context is `≥50` in v1.0 corpus (superseded) and `≤0.05`/`1:1` unrelated numerics.
- **Result**: `CLOSED_VERIFIED`.
- **Residual Risk**: None blocking. Raw-N targets correctly removed (§5.2).

### H01 Power Framework Verification

v1.1 §7.2 enumerates: primary endpoint, expected effect size, α, power, expected ICC, average cluster size m̄, design effect DE, attrition. §4.3 gives `DE = 1 + (m̄−1)·ICC` and `n_eff = N_raw / DE`. §28 applies `×DE` per analysis. §7.3 shows illustrative correlation/κ/AUC calculations explicitly labelled "illustrative only … must be inflated by DE". The named quantities have real relationships, not just headings.

**Result**: framework present and cluster-aware. `CLOSED_VERIFIED`.

---

## 7. H02 Clustering / Effective N Audit

- **Claim**: hierarchy author→chapter→scene→passage; DE/n_eff; chapter-grouped + author-aware split.
- **Evidence**: v1.1 §4.1 hierarchy; §4.2 five cluster variables (`author_id`, `chapter_id`, `scene_id`, `character_ids[]`, `terminology_group_id`); §4.3 DE/n_eff with `n_eff` as "Primary planning quantity"; §4.4 mandatory reporting (`raw N`, cluster count author/chapter/scene, average cluster size, ICC, DE, effective N); §5.2 `≥3` authors; §6.1 complete-scene sampling unit; §6.2 split unit = chapter, within-chapter scenes never cross splits; §15 "Grouped by chapter and author"; §28 matrix.
- **Attack — what is the clustering unit?** author/chapter/scene (+character, terminology as DE inputs). **How is cluster assignment done?** Group assignment by chapter/author. **How is design effect represented?** §4.3 formula. **How is effective N computed?** `N_raw/DE`. **How does clustering affect power?** §7.2/§28 `×DE`. **How does clustering affect split?** chapter+author grouping; scenes kept whole.
- **Gap found**: S7-10 §5.4 explicitly required grouping by "author + **major character arcs**". v1.1 groups by chapter and author but does **not** group by character arc; §4.4's mandatory cluster-count list is `author/chapter/scene` and omits a character count. Character clustering is only partially absorbed (via author grouping and the aggregate ICC in DE).
- **Result**: `PARTIALLY_CLOSED`.
- **Residual Risk**: MEDIUM (see §20 R4) — character-voice carry-over across chapters is not explicitly excluded from split assignment. **Formally non-blocking for Pilot** (pilot is feasibility-only and does not use the calibration split). Must be resolved before Calibration execution.

### Effective N Verification

`raw N ≠ effective N` is explicit and consistent (§4.3, §4.4, §28). All five required future-report elements (raw N, cluster count, cluster size, dependency/ICC estimate, design effect, effective N) are required by §4.4. `PASS`.

---

## 8. H03 Rubric Orthogonality Audit

- **Claim**: overlap acknowledged; ordinal EFA (polychoric); no forced PCA; double-counting guard.
- **Evidence**: v1.1 §8.1 overlap table covering all four S7-10 pairs (Naturalness↔Fidelity, Voice↔Register, Coherence↔Fidelity, Overall↔all); §8.2 ordinal EFA, PCA "supplementary diagnostic" only, "no forced factor count", retain by parallel analysis/scree; §8.3 MERGE/REDEFINE/RETAIN WITH CAUTION; §8.4 covariance reporting + `|ρ|>0.70` flag + latent-factor/variance-inflation option.
- **Verification of factor analysis operational detail**: data type (ordinal) §8.2; correlation structure (polychoric) §8.2; extraction/retention (parallel analysis/scree) §8.2; rotation **not explicitly named** — minor; sample-size dependency (carried by §7 framework); missing data (§17); interpretation (diagnostic-only, no production claim) §8.2. v1.1 does not unconditionally treat raw Likert as continuous Pearson — it mandates polychoric.
- **Attack — double counting**: overlap matrix present (§8.1) + future diagnostic (`|ρ|>0.70` flag, covariance report) present (§8.4). Satisfies S7-10's "overlap matrix + future diagnostic" requirement.
- **Result**: `CLOSED_VERIFIED`.
- **Residual Risk**: LOW/INFO — rotation choice deferred to pilot; non-blocking.

---

## 9. H04 Ordinal Statistics Audit

- **Claim**: 7-pt Likert = ordinal; Pearson/standard ICC demoted.
- **Evidence**: v1.1 §9.1 explicit; §9.2 method-by-purpose (Spearman/Kendall primary; Pearson "only as labelled exploratory"); §9.3 continuous approximation policy tagging mean/SD/Pearson/linear ICC `ASSUMPTION-DEPENDENT` + sensitivity; §12.1 "Spearman ρ (primary); Kendall τ secondary; Pearson exploratory-only"; §27 Statistical Method Matrix (monotonic assumption).
- **Pearson audit**: grep of v1.1 shows `Pearson` appears only at lines 22, 256, 263, 335, 681 — every instance is "exploratory", "labelled exploratory", or within the prohibited-chain warning. No unconditioned primary/default Pearson.
- **Result**: `CLOSED_VERIFIED`.

---

## 10. H05 Agreement Metrics Audit

- **κw**: v1.1 §11.1 — quadratic default, 7 ordinal categories, missing-label policy §17, bootstrap CI ≥2000, minimum reporting set. §27 assigns κw as primary agreement method. **Complete.**
- **ICC**: §11.2 — family `ICC(2,k)` (two-way random, average measure), agreement primary / consistency sensitivity, polychoric-based ordinal ICC preferred with standard ICC tagged assumption-dependent, missing-data coverage, bootstrap CI, and a demotion rule to secondary if ordinal-inappropriate. **Complete.**
- **Bradley-Terry**: §11.3 — graph density/connectivity, ties modeled (BT-with-ties / Davidson), intransitivity test + rate, balance/order, sparse-graph regularization + component flagging, bootstrap/profile-likelihood CI. **Complete.**
- **H05 internal consistency**: κw serves agreement, ICC reliability, BT pairwise preference — three distinct data/decision roles (§9.2, §27). No "one metric for everything".
- **Result**: `CLOSED_VERIFIED`.
- **Residual Risk**: INFO — BT power/stopping not specified; delegated to §23 stopping criteria. Non-blocking.

---

## 11. H06 Numerical Target Audit

- **Claim**: every numeric target classified; none VALIDATED.
- **Verification**: §26 Numerical Target Registry classifies 50 (PILOT_ONLY), 3–5 (PRE-REGISTERED PILOT TARGET), κw≥0.60, ρ≥0.70, Context≥65%, Reviewer/Editor/ACE≥60%, ρ dim≥0.50, ρ agg≥0.65, AUC≥0.80, ECE≤0.05 (PRE-REGISTERED TARGET), 3:1 (UNSUPPORTED ASSUMPTION), 60/20/20 (PRE-REGISTERED TARGET). §26 closing: "No value is VALIDATED. No value may be described as a production threshold." §12.3, §19.2, §11.1 echo the classifications.
- **False-validation attack**: grep for `VALIDATED`/`validated` in v1.1 returns only negative statements ("none VALIDATED", "not validated", "≠ validated") and benign "Validation" split headings. **No target is promoted to VALIDATED.**
- **Traceability**: §26 provides origin/rationale ("Why") and upgrade path ("Upgrade Evidence") per row — satisfies S7-12 §22 (no bare "because S7-09 said so").
- **Result**: `CLOSED_VERIFIED`. **Numerical Target Registry: PASS**.

---

## 12. H07 Weight Optimization Audit

- **n_eff/params**: §13.1 — 6 parameters, `n_eff/params ≥ 10`, explicit remediation if violated. **Present.**
- **Nested CV boundary**: §13.2 diagram `Outer CV (grouped) → Inner CV λ/weight selection → Outer fold performance → Final holdout (once)`, plus prohibited pattern `5-fold CV → choose weights → report same CV`. §12.2 mirrors it. **Satisfies S7-12 §24 (inner tuning ≠ outer evaluation; holdout never tuned).**
- **Stability**: §13.3 — per-fold weights reported; `UNSTABLE` flag on range>0.15 / sign change / CV>0.30; "report all folds, not only the mean". **Present.**
- **Constraints**: §13.4 — `non-negative? sum-to-one? max/min per dimension?` explicitly `TBD — pre-calibration methodology choice`, "No silent hard-coding". S7-12 §26 explicitly *requires* that undefined constraints stay `TBD`. **Compliant.**
- **Promotion**: §13.5 — `optimal weight ≠ validated production weight`.
- **Result**: `CLOSED_VERIFIED`.
- **Residual Risk**: INFO — monotonicity constraints suggested "by theory" in S7-10 §5.13 are not included; correctly left TBD (S7-12 §26 permits this). Non-blocking.

---

## 13. H08 Reference Contamination Audit

- **Claim**: hard role separation; provenance matrix; metric-leakage guard.
- **Evidence**: v1.1 §16.1 role table with hard rule `reference creator ≠ primary evaluator`; §16.2 prohibited scenarios + `creator_id` vs `evaluator_id` disjointness enforcement; §16.3 dedup matrix (exact/normalized/near-simhash≥0.85/same-source/same-candidate/same-reference); §18 GOLD/SILVER/BRONZE × creator/review/calibration/validation/holdout matrix; §25 schema fields `creator_id`, `reviewer_ids[]`, `selection_independent_of_ps03`; §16.6 metric-leakage prohibition; §29 Bias/Leakage Matrix rates reference contamination and metric leakage CRITICAL with prevention columns.
- **Attack test (offline, synthetic, §29/§55)**: ran `tools/one_shots/s7_12_contract_attack_test.py`. Results: `creator==evaluator → CONFLICT` (detected); clean case → OK; chapter across calibration+holdout → `INVALID_SPLIT`; candidate across splits → `INVALID`; `80` threshold → `UNCALIBRATED`; κw → PRE-REGISTERED TARGET. **8/8 expected detections.** This validates the **contract/schema** only — it is not human evaluation and creates no production capability.
- **Result**: `CLOSED_VERIFIED`.
- **Residual Risk**: LOW — enforcement is specified at metadata/protocol level; runtime enforcement is future-task work. Non-blocking.

---

## 14. Leakage / Bias Audit

| Vector | v1.1 Control | Verdict |
|--------|--------------|---------|
| Same chapter across splits | §6.2 chapter-level group split | Covered |
| Same scene across splits | §6.1/§6.2 complete scenes, never cross | Covered |
| Same source / near-duplicate | §16.3 simhash ≥0.85 | Covered |
| Same candidate text | §16.3 cross-split removal | Covered |
| Same reference reused | §16.3 "track; forbid across splits" | Covered |
| Evaluator pool contamination | §16.1/§16.2 disjoint creator/evaluator | Covered |
| Metric leakage (PS-03 prefilter) | §16.6 + `selection_independent_of_ps03` | Covered |
| Learning effect / position bias | §16.5 balancing; §20 randomization; §29 | Covered |
| Overfitting | §13 nested CV | Covered |
| Target shopping | §22 pre-registered primary | Partial — see R2 |

**Result**: `PASS` with recorded residuals (R2, R4).

---

## 15. Pairwise Protocol Audit

Reviewed v1.1 §19 against S7-12 §33–§37.

| Protocol | Unit | Changed var | Unchanged vars | Random/Blind | Order | Primary outcome | Tie handling | Verdict |
|----------|------|-------------|----------------|--------------|-------|-----------------|--------------|---------|
| Best Attempt | attempt pair | attempt index | source, context | §16.4/§16.5 | balanced | ordered preference (1v2, 2v3) | via §11.3 BT | PASS |
| Context | ON/OFF pair | context availability | model, provider, prompt, source, temperature | §16.5 + detectability check §19.3 | balanced | directional (ON>OFF) | via §11.3 BT | PASS |
| Reviewer/Editor/ACE | baseline/processed | processing | model, provider, source | §16.5; FP baseline from independent holdout §19.3 | balanced | directional (processed>baseline) | via §11.3 BT | PASS |
| Segment Merge | merged vs full | merge strategy | source, segment logic | §19.3 randomization + human boundary rating | balanced | whole-output quality | via §11.3 BT | PASS (with R5) |

- **Best Attempt**: §19.3 controls HARD_GATE status; §16.4 hides attempt identity; hard-gate pass is not equated with literary winner. `PASS`.
- **Context**: only context changes; production remains unchanged. `PASS`.
- **Segment Recovery**: evaluation target is final merged output. **Gap (R5)**: the relationship `segment-level metric → final-output metric` is not defined. `PASS` with residual gap.
- **Reviewer/Editor/ACE**: baseline vs processed; production = not implemented (§33). `PASS`.

**Result**: `PASS` with residual R5 (LOW) and R6 (INFO, tie handling delegated to §11.3).

---

## 16. Split / Holdout Audit

- 60/20/20 is classified in §26 as `PRE-REGISTERED TARGET` ("Standard, unverified for clustered data", upgrade evidence "Dependency/power analysis") — **not** asserted as a universal truth.
- Split unit = chapter group; grouped by chapter and author; no chapter/scene/author crosses splits (§6.2, §15).
- Statistical-validity revision: holdout `≥100 raw` → `n_eff ≥ 100`; holdout chapters ≥10; evaluator coverage ≥3 (§15).
- **Contradiction check**: §15 assigns the 20% Validation set to "Hyperparameter selection", while §12.2/§13.2 place hyperparameter/λ selection in the nested-CV **inner** loop. The v1.1 nested-CV diagram never references the 20% validation set. → recorded as **R1 (MEDIUM ambiguity)**. Holdout is consistently single-use and never tuned, so this is redundancy/ambiguity, not holdout leakage.
- **Result**: split separation defined → `PASS` with recorded R1 (Calibration-blocking, not Pilot-blocking).

---

## 17. Pre-Registration Audit

- §21 lists required pre-registration fields (primary endpoint, primary metric, primary agreement method, sampling/split/exclusion/missing rules, threshold procedure, cost assumptions, stopping, promotion).
- §21.1 separates Confirmatory (may support promotion) vs Exploratory (cannot auto-promote).
- §22 prohibits post-hoc target selection and metric cherry-picking; §23 prohibits optional/result-dependent stopping.
- **Caveat (R2)**: §7.2 lists the primary endpoint as "Aggregate Spearman ρ **(or AUC)**". A disjunctive primary endpoint partially undercuts §22's no-cherry-picking rule. → recorded MEDIUM.
- **Result**: `PASS` with R2 (Calibration-blocking).

---

## 18. Missing / Outlier / Stopping Rule Audit

| Rule class | v1.1 | Verdict |
|------------|------|---------|
| Stopping | §23 concrete conditions (stable ±0.02/3 epochs; diverging; cost cap; agreement<0.40; optional stopping PROHIBITED) | **Defined** |
| Outlier | §17.2 policy stated (pre-register, outcome-blind, sensitivity) but concrete thresholds **not enumerated** | **Partial — R3** |
| Missing data | §17.1 lists 5 classes (`missing/abstain/invalid/inattentive/excluded`) and forbids silent deletion, but **per-class operational rules are asserted "predefined" without stating them** | **Partial — R3** |

**Result**: requirement "Missing/Outlier/Stopping rules defined" is `PARTIALLY_CLOSED` → residual **R3 (MEDIUM)**. Non-blocking for Pilot (pilot is feasibility), Calibration-blocking.

---

## 19. Internal Consistency Audit

Cross-checked S7-09 v1.0 ↔ S7-10 ↔ S7-11 v1.1.

| Check | Finding |
|-------|---------|
| Likert treated as ordinal consistently | v1.1 consistent; Pearson never primary. **PASS** |
| v1.0 `ICC(2,1)` vs v1.1 `ICC(2,k)` | Superseded correctly in v1.1; no v1.1 self-contradiction. **PASS** |
| One section ordinal, another Pearson-primary | None in v1.1. **PASS** |
| Holdout untouched everywhere | Consistent (§12.2, §13.2, §15). **PASS** |
| 50 = pilot everywhere | Consistent. **PASS** |
| Target = validated anywhere | None. **PASS** |
| Validation-set role vs nested-CV | **Ambiguity R1** (§15 vs §12.2/§13.2). |
| Primary endpoint singular | **Ambiguity R2** (§7.2 "ρ (or AUC)"). |

S7-09 v1.0 still contains Pearson-primary and `3:1` as fact, but v1.1 explicitly **supersedes** v1.0 and v1.0 is preserved as historical. No live contradiction.

**Result**: `PASS` with recorded non-blocking ambiguities R1, R2.

---

## 20. Residual Risks

| ID | Risk | Severity | Class | Blocking? |
|----|------|----------|-------|-----------|
| R1 | Validation-set "hyperparameter selection" (§15) overlaps nested-CV inner tuning (§12.2/§13.2); locus of λ/weight selection ambiguous | MEDIUM | Calibration interpretation | Not Pilot-blocking; **Calibration-blocking** |
| R2 | Primary endpoint stated disjunctively as "ρ (or AUC)" (§7.2) vs no-cherry-picking (§22) | MEDIUM | Pre-registration / analysis shopping | Not Pilot-blocking; **Calibration-blocking** |
| R3 | Missing-data per-class rules and outlier thresholds asserted "predefined" but not enumerated (§17) | MEDIUM | Data-handling integrity | Not Pilot-blocking; **Calibration-blocking** |
| R4 | Character-arc level not used as split grouping; §4.4 mandatory cluster-count list omits character (§4.2/§4.4/§6) | MEDIUM | Clustering completeness | Not Pilot-blocking |
| R5 | `segment-level metric → final-output metric` relationship undefined (§19) | LOW | Segment protocol | Non-blocking |
| R6 | Pairwise tie-handling not restated per protocol (delegated to §11.3) | INFO | Documentation | Non-blocking |
| R7 | SILVER excluded from holdout (§18) vs v1.0 promotion criterion "≥50 GOLD/SILVER" not restated in v1.1 | INFO | Terminology reconciliation | Non-blocking |

No CRITICAL. No HIGH residual. No false claims of validation.

---

## 21. Finding Closure Matrix

| Finding | S7-10 Severity | S7-11 Claim | Independent Evidence | S7-12 Result | Residual Risk | Blocking? |
|---------|----------------|-------------|----------------------|--------------|---------------|-----------|
| H01 Sample Size | HIGH | RESOLVED | v1.1 §7.1/§7.2/§7.3/§28/§30.2 — 50=PILOT_ONLY everywhere; power inputs + `×DE` | **CLOSED_VERIFIED** | None | No |
| H02 Clustering | HIGH | RESOLVED | §4.1–4.4, §6.1–6.2, §15 — hierarchy, DE/n_eff, chapter+author grouping; character-arc split grouping absent | **PARTIALLY_CLOSED** | MEDIUM (R4) | No (pilot); resolve before calibration |
| H03 Rubric | HIGH | RESOLVED | §8.1–8.4 — overlap table, ordinal EFA/polychoric, no forced factors, `|ρ|>0.70` guard | **CLOSED_VERIFIED** | LOW/INFO | No |
| H04 Ordinal | HIGH | RESOLVED | §9.1–9.3, §12.1, §27 — Likert ordinal; Pearson only exploratory/assumption-dependent | **CLOSED_VERIFIED** | None | No |
| H05 Agreement | HIGH | RESOLVED | §11.1 κw, §11.2 ICC(2,k), §11.3 BT (graph/ties/intransitivity/sparse/CI), §27 | **CLOSED_VERIFIED** | INFO | No |
| H06 Numerical Targets | HIGH | RESOLVED | §26 registry; grep confirms no VALIDATED target; §12.3/§19.2/§11.1 consistent | **CLOSED_VERIFIED** | None | No |
| H07 Weight Optimization | HIGH | RESOLVED | §13.1 n_eff/params≥10; §13.2 nested-CV boundary; §13.3 stability; §13.4 TBD constraints; §12.2 | **CLOSED_VERIFIED** | INFO | No |
| H08 Reference Contamination | HIGH | RESOLVED | §16.1–16.6, §18, §25, §29; offline attack test 8/8 (CONFLICT/INVALID_SPLIT/INVALID detected) | **CLOSED_VERIFIED** | LOW | No |

S7-11 `RESOLVED` claims were **not** used as independent evidence. H02 is withheld from `CLOSED_VERIFIED`.

**Secondary findings (S7-10 MEDIUM/LOW)**: split grouped (✅), leakage matrix (✅), pairwise split symmetric/asymmetric + controls (✅), SILVER/BRONZE matrix (✅), fatigue operational fields (✅ TBD-from-pilot), binary conflict rule (✅ §10.1), pre-registration (✅ §21), multiple testing (✅ §22), cost/value (✅ §24), missing/outlier/stopping (⚖️ partial → R3).

---

## 22. Pilot Authorization Decision

**`READY_FOR_PILOT`** (with recorded non-blocking residual risks).

`READY_FOR_PILOT` means only: the **study methodology** passed independent design audit and a pilot may be authorized as a **separate** task. It does **not** mean calibration validated, PS-03 validated, Naturalness validated, 80/65 validated, or production-gate ready (§68).

### Required Pilot Authorization Matrix (§61)

| Requirement | Status | Evidence | Blocking |
|-------------|--------|----------|----------|
| 50 = PILOT_ONLY | PASS | v1.1 §7.1/§26/§28/§30.2 | No |
| Sample-size framework | PASS | §7.2 inputs; §4.3 DE; §28 `×DE` | No |
| Cluster adjustment | PASS | §4.3 `DE=1+(m̄−1)ICC`; §6.1 | No |
| Effective N | PASS | §4.3/§4.4 `n_eff=N_raw/DE` | No |
| Rubric orthogonality | PASS | §8.1–8.4 | No |
| Ordinal analysis | PASS | §9/§12.1/§27 | No |
| Agreement specification | PASS | §11.1–11.3 | No |
| Target registry | PASS | §26 | No |
| Nested CV | PASS | §13.2/§12.2 | No |
| Weight stability | PASS | §13.3 | No |
| Reference separation | PASS | §16.1/§16.2/§18 | No |
| Leakage control | PASS | §16/§29 | No |
| Pairwise controls | PASS | §19/§16.4–16.5 | No |
| Pre-registration | PASS (R2) | §21/§22 | No |
| Missing data | PARTIAL (R3) | §17.1 classes, rules asserted not stated | No |
| Outlier rules | PARTIAL (R3) | §17.2 policy only | No |
| Stopping rules | PASS | §23 | No |

Conditions §45-1..18: no CRITICAL; no HIGH blocker; H01–H08 closed or non-blocking residual; 50=PILOT_ONLY; cluster-aware; effective N; overlap method; ordinal coherent; agreement specified; targets classified; leakage controlled; contamination blocked; splits defined; pairwise controls; pre-registration boundary; missing/outlier/stopping (partial, non-blocking); human study not executed; production boundary unchanged. **All satisfied or formally non-blocking.**

R1/R2/R3 must be resolved before **Calibration execution**, not before Pilot.

---

## 23. Production Boundary Verification

Independently verified in code (not merely quoted from artifacts):

| Boundary | Code Evidence | Status |
|----------|---------------|--------|
| Model `meta/llama-3.2-90b-vision-instruct` | `core/adapters/production_submission_adapter.py:20`; `ntpe_production_translate.py:102`; `lts/txt_translation_runtime.py:83`; `core/config.py:19` | FROZEN ✓ |
| Provider `nvidia` | `core/controlled_provider_routing/provider_profiles.py:28`; runtime defaults | FROZEN ✓ |
| Retry boundary | `core/translation_reliability/adaptive_retry_policy.py`: `max_attempts` default 5 (L195); `provider_switch_after_attempt` 3 (L202-203); switch on `http_503/http_429/retry_exhausted` (L137-141); chunk halving on `read_timeout/too_short/empty_output/hangul_residue` (L233-236) | PRESERVED ✓ |
| Context `quality_context_scene_v72=false` | `core/adapters/production_submission_adapter.py:38` default `False`; `lts/txt_translation_runtime.py:148`; `ui/translation_launcher/controller.py:65` | FROZEN OFF ✓ |
| PS-03 weights 30/20/20/15/10/5 | `ntpe_literary_evaluation.py:110,132,142,150,164,171` (`30.0, 20.0, 20.0, 15.0, 10.0, 5.0`) | FROZEN ✓ |
| Thresholds 80/65 | `ntpe_literary_evaluation.py:174` (`>=80 success`, `>=65 warning`) | FROZEN ✓ |
| Production files modified by S7-12 | none | NO ✓ |

---

## 24. Regression Tests

Command: `python -m pytest tests/ui/test_s6_02_acceptance.py tests/ui/test_s6_03_acceptance.py tests/ui/test_s6_04_acceptance.py tests/ui/test_s6_05_acceptance.py -q`

| Suite | Collected | Passed | Failed |
|-------|-----------|--------|--------|
| S6-02 TXT Acceptance | 6 | 6 | 0 |
| S6-03 EPUB Acceptance | 7 | 7 | 0 |
| S6-04 Validation Acceptance | 16 | 16 | 0 |
| S6-05 Dry-Run Acceptance | 8 | 8 | 0 |
| **Total** | **37** | **37** | **0** |

Before: 37/37 baseline. After: 37/37. No failure. No S7-12-caused, pre-existing, or environmental failures.

---

## 25. Human Evaluation Execution — 0

0 evaluators contacted, 0 human labels collected, 0 new references created.

## 26. Pilot Execution — 0

No pilot run. Authorization only is granted; execution is a separate task.

## 27. Calibration Execution — 0

No calibration executed; thresholds 80/65 and weights remain untouched/uncalibrated.

## 28. Real Translation — 0

No translation produced.

## 29. Provider / Network — 0

0 provider calls, 0 network calls, 0 external API calls.

## 30. Production Files Modified — NO

Only two new files were written: the report artifact and an offline one-shot contract test. No production code changed.

## 31. Root Hygiene

**PASS** — No root scratch files (`*.py`, `*.ps1`, `*.bat`, `*.txt`, `*.json`, `*.log`). Report in `artifacts/`; the one-shot validation tool in `tools/one_shots/`. Pre-existing working-tree changes preserved.

---

## 32. Final Verdict

```text
S7_12_REAUDIT_PASS_WITH_NONBLOCKING_RISKS
```

### Rationale

- No unresolved CRITICAL.
- No unresolved HIGH methodology blocker.
- H01, H03, H04, H05, H06, H07, H08 = `CLOSED_VERIFIED`; H02 = `PARTIALLY_CLOSED` with formally non-blocking residual MEDIUM.
- No numerical target falsely marked validated; registry complete.
- No material contradiction — two non-blocking internal ambiguities recorded (R1, R2).
- Pilot design operationally specified; production boundary independently verified unchanged.
- Residual MEDIUM risks R1–R4 must be resolved before **Calibration**, not before **Pilot**. R5–R7 are non-blocking.

`READY_FOR_PILOT` does **not** authorize calibration, promotion, threshold change, weight change, retry change, context enablement, or any production modification.

---

## 33. Artifacts Produced

| Artifact | Path |
|----------|------|
| Re-Audit Report | `artifacts/NTPE_S7_12_LITERARY_CALIBRATION_DESIGN_V1_1_INDEPENDENT_REAUDIT_REPORT.md` |
| Offline contract attack test | `tools/one_shots/s7_12_contract_attack_test.py` (design-contract validation only) |

**Commit: NO · Push: NO · Tag: NO**

---

*End of S7-12 Re-Audit Report*
