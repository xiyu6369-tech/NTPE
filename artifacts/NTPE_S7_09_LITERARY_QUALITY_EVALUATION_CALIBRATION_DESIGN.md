# NTPE S7-09 Literary Quality Evaluation & Calibration Design

**Design Date**: 2026-09-30
**Author**: Kilo (Automated)
**Scope**: Evaluation & Calibration Framework Design per S7-09 mandate
**Status**: DESIGN — No implementation, no calibration execution

---

## 1. Purpose

This document defines a complete, auditable framework for acquiring, evaluating, and calibrating literary quality metrics for NTPE translation output. It bridges the gap between current `OBSERVATIONAL_ONLY` status (S7-08 verdict) and potential future `PRODUCTION_CONTRACT` promotion.

**Core Principle**: Every production quality gate must trace to deterministic, repository-verifiable evidence with human evaluation correlation. No arbitrary thresholds.

---

## 2. Frozen Baseline

| Metric | Value |
|--------|-------|
| HEAD | `5b41e3d55b5d07f6e8d1fec2ea10fd83d22aedf5` |
| Branch | `main` |
| Model | `meta/llama-3.2-90b-vision-instruct` (FROZEN) |
| Provider | `nvidia` (FROZEN) |
| Retry Boundary | LOCKED (max 5 attempts, provider switch after 3, chunk halving for quality failures) |
| Context Feature | `quality_context_scene_v72=false` (FROZEN OFF) |
| S7-07 Contract | `QUALITY_CONTRACT_V1` — 14 deterministic production gates defined |
| S7-08 Verdict | `S7_08_LITERARY_QUALITY_REMAINS_OBSERVATIONAL_ONLY` |

---

## 3. Current Quality Contract State (from S7-07)

### Production Gates (LOCKED — No Change)
| Dimension | Gate Type | Threshold | Status |
|-----------|-----------|-----------|--------|
| Empty Output | HARD_GATE | Zero tolerance | PRODUCTION |
| Length Ratio | HARD_GATE | 0.35 / 0.18 (LTS) | PRODUCTION |
| Paragraph Omission | HARD_GATE | Corroborated ratio < 0.5 | PRODUCTION |
| Sentence Omission | HARD_GATE | Ratio < 0.5 | PRODUCTION |
| Duplicate Paragraphs | HARD_GATE | max_duplicate_paragraphs=0 | PRODUCTION |
| Duplicate Lines | HARD_GATE | max_duplicate_lines=1 | PRODUCTION |
| Locked Terms Missing | HARD_GATE | Zero missing | PRODUCTION |
| Forbidden Variants | HARD_GATE | Zero wrong variants | PRODUCTION |
| Full-name Over-expansion | HARD_GATE | Zero over-expansion | PRODUCTION |
| Simplified Chinese | HARD_GATE | Zero tolerance | PRODUCTION |
| Dialogue Quote Format | LOCAL_REPAIR | Convert to `「」` | PRODUCTION |
| Paragraph Count | HARD_GATE | Ratio ≥ 0.5 (corroborated) | PRODUCTION |
| Sentence Count | HARD_GATE | Ratio ≥ 0.5 | PRODUCTION |
| Character Consistency | HARD_GATE | Via locked terms + memory | PRODUCTION |

### Non-Production Areas (S7-08 Verdict)
| Area | Status | Evidence |
|------|--------|----------|
| Literary Naturalness | `OBSERVATIONAL_ONLY` | PS-03 proxy (20pts), no calibration |
| PS-03 Heuristic Dimensions | `OBSERVATIONAL_ONLY` | 4 proxy dims, no human correlation |
| PS-03 Aggregate (100pt) | `OBSERVATIONAL_ONLY` | Arbitrary weights, uncalibrated |
| Thresholds 80/65 | `UNCALIBRATED` | Arbitrary constants |
| Best Attempt Selection | `NOT_IMPLEMENTED` | 0 call sites, no attempt labels |
| Segment Recovery Merge | `NOT_IMPLEMENTED` | No merge strategy, no quality evidence |
| Context Continuity | `FEATURE_GATED_OFF` | Default `false`, no benchmark |
| Literary Reviewer/Editor | `NOT_IMPLEMENTED` | Zero repository evidence |
| ACE | `TEST_ONLY` | Test scaffolding only |

---

## 4. Evidence Gap Summary (from S7-08)

| Gap | Current | Required for Promotion |
|-----|---------|------------------------|
| Human evaluation dataset | NONE | Representative corpus with human labels |
| Reference translation corpus | NONE | Professionally translated gold standard |
| PS-03 weight calibration | NONE | Empirical justification for 30/20/20/15/10/5 |
| Threshold calibration (80/65) | NONE | ROC analysis on labeled data |
| Human-metric correlation | NONE | Controlled evaluation study |
| False positive/negative rates | UNKNOWN | Labeled failure cases |
| Best attempt quality labels | NONE | Blind pairwise attempt comparisons |
| Segment merge quality evidence | NONE | End-to-end recovery evaluation |
| Context continuity benefit | NONE | Blinded A/B with quality labels |

---

## 5. Evaluation Objectives

The calibration framework must enable **evidence-based promotion decisions** for each non-production area:

1. **Literary Naturalness** → Can PS-03 natural_chinese_proxy (or replacement) reliably predict human naturalness judgments?
2. **PS-03 Heuristic Dimensions** → Do subject/pronoun, character voice proxies correlate with human judgment?
3. **PS-03 Aggregate** → Does 100-point weighted sum meaningfully rank translation quality?
4. **Thresholds 80/65** → Do these values optimally discriminate human ACCEPT/REJECT?
5. **Best Attempt Selection** → Does metric-based ranking match human preference across attempts?
6. **Segment Recovery Merge** → Does segment-level quality selection + merge preserve global quality?
7. **Context Continuity** → Does `quality_context_scene_v72=true` improve human-rated quality?
8. **Reviewer/Editor/ACE** → Do these improve human-preferred quality without increasing false positives?

**Promotion Rule**: Only areas passing independent holdout validation with acceptable FP/FN rates may enter `CONTRACT_PROMOTION` task.

---

## 6. Evaluation Unit

### Primary Unit: **Scene-Level Passage (Multi-Paragraph Context Window)**

**Rationale**:
- Terminology/character consistency requires multi-paragraph context
- Naturalness assessment needs passage-level flow
- Global coherence requires scene boundaries
- Matches EPUB chapter structure and LTS chunking

### Secondary Units (Dimension-Specific)

| Dimension | Evaluation Unit | Justification |
|-----------|-----------------|---------------|
| Terminology/Character | Multi-paragraph / scene | Cross-paragraph consistency |
| Naturalness | Paragraph / passage | Local flow assessment |
| Fidelity | Sentence / paragraph | Omission/accuracy check |
| Coherence | Scene / chapter | Narrative continuity |
| Format/Punctuation | Full output | Deterministic check |

---

## 7. Corpus Design

### 7.1 Source Corpus Requirements

| Requirement | Specification |
|-------------|---------------|
| **Language** | Korean (source) → Traditional Chinese (target) |
| **Genre** | Web novel / light novel (matching NTPE production) |
| **Source Diversity** | ≥3 sub-genres (romance, fantasy, modern, historical) |
| **Scene Types** | Dialogue-heavy, narration-heavy, action, introspection, exposition |
| **Dialogue Density** | Stratified: 0-20%, 20-50%, 50-80% |
| **Character Count** | 500-3000 chars per passage (typical LTS chunk) |
| **Sentence Complexity** | Simple, compound, complex, fragmented |
| **Register/Tone** | Formal, casual, archaic, poetic, technical |
| **Terminology Density** | Low (<5 locked terms), Medium (5-15), High (>15) |

### 7.2 Minimum Corpus Size (Preliminary)

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Passages** | 500-1000 | Statistical power for correlation (α=0.05, β=0.2, ρ=0.3) |
| **Chapters** | ≥50 | Chapter-level diversity |
| **Scenes** | ≥200 | Scene-level diversity |
| **Characters** | ≥10 | Character voice diversity |

**Note**: Final sample size **TBD — Requires statistical power analysis** after pilot study.

### 7.3 Source Corpus Provenance

| Source Type | Status | Notes |
|-------------|--------|-------|
| Licensed Korean web novels | TARGET | Requires licensing |
| Public domain Korean literature | FALLBACK | May not match genre |
| Synthetic/authored test passages | SUPPLEMENT | For controlled failure modes |

---

## 8. Sampling Strategy

### Stratified Sampling Protocol

1. **Strata**: Genre × Dialogue Density × Scene Type × Terminology Density
2. **Sampling**: Random within strata
3. **Chapter-Level Sampling**: No passage splitting across chapters
4. **Scene-Level Sampling**: Complete scenes only
5. **Minimum per Stratum**: 10 passages
6. **Holdout Separation**: By chapter (no chapter in both calibration and holdout)

### Leakage Prevention

| Risk | Prevention |
|------|------------|
| Same chapter in calibration/holdout | Chapter-level split only |
| Near-duplicate passages | Deduplication (simhash ≥0.85) |
| Same translation candidate in both sets | Candidate-level deduplication |
| Same reference in both sets | Reference-level deduplication |

---

## 9. Translation Candidate Design

### Candidate Provenance Schema

| Field | Required | Example |
|-------|----------|---------|
| `candidate_id` | Yes | `cand_001234` |
| `source_span_id` | Yes | `src_ch03_sc02` |
| `model` | Yes | `meta/llama-3.2-90b-vision-instruct` |
| `provider` | Yes | `nvidia` |
| `prompt_version` | Yes | `v5.3.1-literary` |
| `runtime_version` | Yes | `TE-v5.3.1` |
| `attempt_number` | Yes | `1` (1-based) |
| `temperature` | Yes | `0.15` |
| `max_tokens` | Yes | `4000` |
| `timestamp` | Yes | ISO 8601 |
| `configuration_hash` | Yes | SHA256 of full config |

### Candidate Quality Diversity Requirements

| Quality Tier | Proportion | Generation Method |
|--------------|------------|-------------------|
| **Clearly Good** | 25% | Production model, attempt 1, high quality source |
| **Acceptable** | 35% | Production model, various attempts |
| **Borderline** | 25% | Controlled prompts, temperature variation, shorter context |
| **Clearly Poor** | 15% | Known failure injections (omission, hallucination, wrong terms) |

### Failure Mode Coverage (Minimum)

| Failure Mode | Candidates | Notes |
|--------------|------------|-------|
| Literal/awkward wording | ≥20 | Over-literal Korean→Chinese |
| Semantic omission | ≥20 | Missing paragraphs/sentences |
| Hallucinated detail | ≥20 | Added detail not in source |
| Wrong terminology | ≥20 | Locked term violations |
| Wrong character identity | ≥15 | Pronoun/name confusion |
| Style/register mismatch | ≥15 | Inappropriate tone |
| Dialogue unnaturalness | ≥15 | Missing `「」`, wrong particles |
| Repetition | ≥10 | Duplicate lines/paragraphs |
| Formatting errors | ≥10 | Simplified Chinese, wrong punctuation |
| Context discontinuity | ≥15 | Pronoun drift, scene breaks |

---

## 10. Reference Translation Policy

### 10.1 Reference Classification

| Classification | Definition | Eligible for Calibration |
|----------------|------------|--------------------------|
| **GOLD_REFERENCE** | Professional human translation, independently reviewed, approved | YES |
| **SILVER_REFERENCE** | Human-edited machine translation, independently reviewed | YES (with caveat) |
| **BRONZE_REFERENCE** | Single human translation, no independent review | CALIBRATION ONLY |
| **MACHINE_OUTPUT** | Raw model output | NO |
| **DEVELOPER_FIXTURE** | Developer-written expected output | NO |
| **SYNTHETIC** | Programmatically generated | NO |

### 10.2 Gold Reference Requirements

| Requirement | Specification |
|-------------|---------------|
| **Translator Qualification** | Professional literary translator, ≥3 years KO→ZH-TW novel experience |
| **Review Process** | Minimum 2 independent reviews + adjudication |
| **Source Equivalence** | Complete passage, no omissions |
| **Literary Consistency** | Consistent voice, register, terminology across passage |
| **Terminology Policy** | Documented locked term handling |
| **Character Consistency** | Consistent pronouns, honorifics, speech patterns |
| **Formatting Policy** | Traditional Chinese, `「」` dialogue, standard punctuation |
| **Revision Provenance** | Full revision history tracked |
| **Approval** | Signed off by lead reviewer |

### 10.3 Silver Reference Requirements

| Requirement | Specification |
|-------------|---------------|
| **Base** | Machine translation (production model) |
| **Editing** | Professional editor revises for literary quality |
| **Review** | 1 independent review + approval |
| **Provenance** | Clear annotation of machine vs human segments |

---

## 11. Human Evaluation Rubric

### 11.1 Primary Dimensions (7-Point Likert: 1=Very Poor, 7=Excellent)

| Dimension | Definition | Anchors |
|-----------|------------|---------|
| **Naturalness** | Reads as natural Traditional Chinese novel prose; no translationese | 1: Machine-like, 4: Acceptable, 7: Publication-ready |
| **Fidelity** | Faithfully conveys source meaning; no omissions/additions | 1: Major omissions/hallucinations, 4: Minor issues, 7: Perfect |
| **Character Voice** | Distinct, consistent speech patterns per character | 1: Indistinguishable/confused, 4: Mostly consistent, 7: Distinct & vivid |
| **Register/Tone** | Appropriate formality, era, emotion for context | 1: Jarring mismatch, 4: Mostly appropriate, 7: Perfectly attuned |
| **Coherence** | Sentence/paragraph/scene flow logically; pronoun resolution | 1: Disjointed, 4: Mostly smooth, 7: Seamless |
| **Terminology Consistency** | Locked terms, names, honorifics stable | 1: Inconsistent, 4: Minor slips, 7: Perfect |
| **Overall Literary Quality** | Holistic judgment: would publish as novel | 1: Unacceptable, 4: Acceptable with edits, 7: Publication-ready |

### 11.2 Binary Acceptance Label

| Label | Definition |
|-------|------------|
| **ACCEPT** | Overall ≥5 AND no dimension <3 |
| **REJECT** | Overall <3 OR any dimension ≤2 |

### 11.3 Failure Mode Tags (Multi-label)

| Tag | Trigger |
|-----|---------|
| `OMISSION` | Missing source content |
| `HALLUCINATION` | Added content not in source |
| `WRONG_TERM` | Locked term violation |
| `WRONG_CHARACTER` | Character identity confusion |
| `UNNATURAL` | Translationese, awkward phrasing |
| `REGISTER_MISMATCH` | Wrong tone/register |
| `INCOHERENT` | Logical flow broken |
| `FORMAT_ERROR` | Simplified Chinese, wrong punctuation |

---

## 12. Human Evaluation Protocol

### 12.1 Evaluator Qualification (TBD — Requires Pilot Study)

| Criterion | Proposed Minimum |
|-----------|------------------|
| **Language** | Native Traditional Chinese speaker |
| **Literary Exposure** | ≥50 Korean novels read in translation |
| **Translation Experience** | ≥2 years KO→ZH-TW or equivalent editing |
| **Blind Test Pass** | ≥80% agreement with gold standard on calibration set |

### 12.2 Evaluation Procedure

1. **Blind Presentation**: Evaluator sees source + candidate only; no model/attempt metadata
2. **Randomized Order**: Candidates randomized per evaluator
3. **Context Exposure**: Full source passage + candidate translation
3. **Scoring**: 7 dimensions on 1-7 Likert + binary ACCEPT/REJECT + failure tags
4. **Time Budget**: 8-12 minutes per passage
5. **Fatigue Control**: Max 10 passages/session; mandatory breaks
6. **Re-evaluation**: 10% passages re-evaluated after 1 week (intra-rater reliability)

### 12.3 Training & Calibration

| Phase | Activity |
|-------|----------|
| **Orientation** | Read rubric, review 5 annotated examples |
| **Calibration Set** | Score 10 passages with known gold labels; feedback |
| **Qualification** | Must achieve ≥0.7 weighted kappa vs gold on calibration set |
| **Ongoing** | 5% hidden calibration passages per session |

---

## 13. Blind Evaluation Rules

### Strict Blindness Requirements

| Prohibited Information | Enforcement |
|------------------------|-------------|
| Model identity | Never shown |
| Provider | Never shown |
| Attempt number | Never shown |
| Developer "good/bad" label | Never shown |
| PS-03 metric scores | Never shown |
| "Gold" / "Reference" label | Never shown (unless in explicit reference condition) |

### Evaluation Conditions

| Condition | Purpose |
|-----------|---------|
| **SOURCE + CANDIDATE** | Primary — naturalistic evaluation |
| **SOURCE + CANDIDATE + REFERENCE** | Secondary — comparative (reference labeled "Alternative Translation") |
| **CANDIDATE A vs CANDIDATE B** | Pairwise — preference only |

---

## 14. Pairwise Evaluation Design

### 14.1 When Required

- Best Attempt Selection validation
- Segment Recovery Merge validation
- Context Continuity (ON vs OFF) validation
- Reviewer/Editor/ACE validation

### 14.2 Protocol

1. **Blind Pairwise**: Evaluator sees source + two candidates (A, B), randomized order
2. **Preference**: Select A, B, or TIE (if genuinely equal)
3. **Confidence**: Rate confidence 1-5
4. **Reasoning**: Brief free-text (optional)
5. **Order Balancing**: Each pair presented in both orders across evaluators

### 14.3 Tie/Abstention Handling

| Outcome | Handling |
|---------|----------|
| **TIE** | Record as 0.5 preference; excluded from win-rate |
| **ABSTAIN** | "Cannot judge" — excluded; triggers re-evaluation |

---

## 15. Inter-Rater Agreement Methodology

### Primary Metric: **Weighted Cohen's Kappa (κw)**

| Agreement Level | κw Range | Interpretation |
|-----------------|----------|----------------|
| **Excellent** | ≥0.80 | Ready for calibration |
| **Good** | 0.60-0.79 | Acceptable with caveats |
| **Moderate** | 0.40-0.59 | Needs rubric revision |
| **Poor** | <0.40 | Insufficient reliability |

### Secondary Metrics (Per Dimension)

| Data Type | Metric |
|-----------|--------|
| Ordinal (1-7) | Weighted κ, ICC(2,1) |
| Binary (ACCEPT/REJECT) | Cohen's κ |
| Multi-label (Failure Tags) | Label-wise κ, Hamming accuracy |
| Pairwise | Win-rate agreement, Bradley-Terry model |

### Disagreement Handling

| Level | Action |
|-------|--------|
| **Minor** (adjacent scores) | Accept mean |
| **Major** (≥2 point gap) | Third adjudicator review |
| **Systematic** (rater consistently high/low) | Calibration session; potential exclusion |

---

## 16. PS-03 Calibration Methodology

### 16.1 Dimension-Level Calibration

For each of 6 PS-03 dimensions:

| Step | Method |
|------|--------|
| **1. Metric Extraction** | Run PS-03 on all candidates |
| **2. Human Label Alignment** | Match PS-03 dimension score to human dimension score |
| **3. Correlation** | Spearman ρ (ordinal) + Pearson r (continuous) |
| **4. Calibration Curve** | Isotonic regression / Platt scaling |
| **5. Threshold Sweep** | ROC analysis for binary ACCEPT/REJECT |

### 16.2 Aggregate Calibration

| Step | Method |
|------|--------|
| **1. Weight Optimization** | Constrained optimization: maximize human correlation |
| **2. Weight Bounds** | [0, 1] per dimension; sum = 100 |
| **3. Regularization** | L2 penalty to prevent overfitting |
| **4. Cross-Validation** | 5-fold CV on calibration set |
| **5. Holdout Validation** | Final weights evaluated on holdout |

### 16.4 Calibration Metrics

| Metric | Target |
|--------|--------|
| **Spearman ρ (dimension)** | ≥0.50 per dimension |
| **Spearman ρ (aggregate)** | ≥0.65 |
| **AUC (binary ACCEPT/REJECT)** | ≥0.80 |
| **Calibration Error (ECE)** | ≤0.05 |

---

## 17. Threshold Calibration Design

### 17.1 Current Frozen Thresholds (Do Not Change)

| Threshold | Value | Status |
|-----------|-------|--------|
| Success | ≥80 | FROZEN |
| Warning | ≥65 | FROZEN |
| Failed | <65 | FROZEN |

### 17.2 Future Threshold Derivation

| Step | Method |
|------|--------|
| **1. Candidate Thresholds** | Sweep 0-100 in 1-point increments |
| **2. Cost Matrix** | FP cost = 3× FN cost (production retry cost > quality miss) |
| **3. Youden Index** | Maximize (Sensitivity + Specificity - 1) |
| **4. Cost-Sensitive** | Minimize expected cost |
| **5. Holdout Validation** | Report threshold performance on holdout |

### 17.3 Threshold Reporting

| Report | Content |
|--------|---------|
| **ROC Curve** | TPR vs FPR across thresholds |
| **PR Curve** | Precision vs Recall |
| **Confusion Matrix** | At optimal threshold |
| **Cost Curve** | Expected cost vs threshold |
| **Stability** | Threshold variance across CV folds |

---

## 18. Validation / Holdout Split Design

### Split Strategy

| Set | Proportion | Purpose | Leakage Prevention |
|-----|------------|---------|-------------------|
| **Calibration** | 60% | Weight optimization, threshold sweep | Chapter-level split |
| **Validation** | 20% | Hyperparameter selection, early stopping | Chapter-level split |
| **Holdout** | 20% | Final unbiased evaluation | Chapter-level split |

### Novel-Level Constraints

- **No chapter overlap** between sets
- **No scene overlap** between sets
- **No source passage overlap** (simhash <0.85)
- **No candidate overlap** (exact text deduplication)

### Statistical Validity

| Requirement | Minimum |
|-------------|---------|
| Holdout passages | ≥100 |
| Holdout chapters | ≥10 |
| Holdout scenes | ≥40 |
| Evaluator coverage | Each passage ≥3 evaluators |

---

## 19. Leakage Prevention

| Vector | Prevention |
|--------|------------|
| Same chapter in multiple splits | Chapter-level assignment only |
| Same scene in multiple splits | Scene-boundary respecting split |
| Near-duplicate passages | Simhash deduplication (threshold 0.85) |
| Same candidate text | Exact text deduplication across splits |
| Same reference translation | Reference ID tracking |
| Evaluator contamination | Evaluator never sees same passage twice (except intra-rater 10%) |

---

## 20. False Positive / False Negative Analysis

### Definitions

| Error Type | Metric Says | Human Says | Production Impact |
|------------|-------------|------------|-------------------|
| **False Positive (Type I)** | PASS / ACCEPT | REJECT / Poor | Bad output ships; user sees poor quality |
| **False Negative (Type II)** | FAIL / REJECT | ACCEPT / Good | Unnecessary retry; cost, latency, potential degradation |

### Analysis Protocol

| Analysis | Method |
|----------|---------|
| **FP Rate** | FP / (FP + TN) at operating threshold |
| **FN Rate** | FN / (FN + TP) at operating threshold |
| **Error Categorization** | By failure tag (OMISSION, HALLUCINATION, etc.) |
| **Cost Analysis** | Expected cost = FP_rate × FP_cost + FN_rate × FN_cost |
| **Per-Dimension** | FP/FN per PS-03 dimension |

### Operating Cost Ratio

| Error | Relative Cost | Rationale |
|-------|---------------|-----------|
| **False Positive** | 3.0 | Bad output reaches user; reputational damage |
| **False Negative** | 1.0 | Unnecessary retry; compute cost + latency |

**Threshold Selection**: Minimize `(3 × FP_rate) + (1 × FN_rate)`

---

## 21. Best Attempt Evaluation Design

### 21.1 Evidence Requirements

| Evidence | Specification |
|----------|---------------|
| **Multiple Attempts** | ≥3 attempts per source passage |
| **Blind Human Comparison** | Pairwise: Attempt A vs Attempt B |
| **Attempt-Level Metrics** | PS-03, human scores per attempt |
| **Hard-Gate Status** | Per attempt: PASS/FAIL on HARD_GATES |
| **Cross-Attempt Ranking** | Metric rank vs Human preference |

### 21.2 Validation Protocol

1. Generate ≥3 attempts per passage (temperature variation, chunk size)
2. Blind pairwise evaluation: Attempt i vs Attempt j
3. Compute **metric rank correlation** with **human preference**
4. Analyze **failure cases**: When metric prefers worse attempt
5. Define **minimum quality floor** for attempt eligibility

### 21.4 Success Criteria

| Metric | Target |
|------|--------|
| **Rank Correlation** (Spearman ρ) | ≥0.70 |
| **Preference Agreement** (metric top = human top) | ≥80% |
| **Hard-Gate Filter** | No human-ACCEPT attempt with HARD_GATE fail |

---

## 22. Segment Recovery Evaluation Design

### 22.1 Evidence Requirements

| Evidence | Specification |
|----------|---------------|
| **Segment-Level Quality** | Human + metric scores per segment |
| **Boundary Fidelity** | No content loss/duplication at boundaries |
| **Ordering** | Correct segment order in merge |
| **Duplicate Prevention** | No repeated content across segments |
| **Local Coherence** | Segment-internal flow |
| **Global Continuity** | Cross-segment pronoun/term consistency |
| **Human Acceptance** | Full merged output evaluation |

### 22.2 Validation Protocol

1. **Segment Generation**: Split source passages per `segment_recovery.py` logic
2. **Segment Translation**: Translate each segment independently
3. **Merge Strategies Test**:
   - Simple concatenation
   - Overlap deduplication
   - Context-aware merge (using previous segment tail)
4. **Blind Evaluation**: Merged output vs full-passage translation
5. **Boundary Analysis**: Automated check for content loss/duplication

### 22.3 Success Criteria

| Metric | Target |
|------|--------|
| **Merged vs Full Human Score** | Δ ≤ 2 points (7-pt scale) |
| **Boundary Error Rate** | ≤2% segments with loss/duplication |
| **Global Coherence Score** | ≥5/7 |

---

## 23. Context Continuity Evaluation Design

### 23.1 Evidence Requirements

| Evidence | Specification |
|----------|---------------|
| **Context OFF** | Translation without `quality_context_scene_v72` |
| **Context ON** | Translation with `quality_context_scene_v72=true` |
| **Blind A/B** | Evaluator sees source + two candidates (randomized) |
| **Dimensions** | Character consistency, terminology, scene continuity, voice |
| **Hard-Gate Impact** | HARD_GATE pass rate difference |

### 23.2 Validation Protocol

1. **Candidate Generation**: Same source, same model, Context OFF vs ON
2. **Blind Pairwise**: Evaluator prefers A or B (randomized order)
3. **Dimension Scores**: Full rubric on both
4. **Hard-Gate Comparison**: Pass rate on locked terms, omissions, etc.

### 23.3 Success Criteria

| Metric | Target |
|------|--------|
| **Human Preference (ON)** | ≥65% win rate |
| **Character Consistency Δ** | ≥+0.5 points |
| **Terminology Consistency Δ** | ≥+0.5 points |
| **HARD_GATE Pass Rate Δ** | ≥+5% |

---

## 24. Reviewer / Editor / ACE Evaluation Design

### 24.1 Evidence Requirements

| Component | Comparison | Key Question |
|-----------|------------|--------------|
| **ACE** | Baseline vs ACE-processed | Does adaptive context improve human quality? |
| **Literary Reviewer** | Baseline vs Reviewer-output | Does review flag improve human acceptance? |
| **Literary Editor** | Baseline vs Edited-output | Does editing improve human acceptance? |

### 24.2 Validation Protocol

1. **Baseline**: Production model output
2. **Processed**: Apply ACE/Reviewer/Editor
3. **Blind Pairwise**: Baseline vs Processed (randomized)
4. **Full Rubric**: Both conditions scored
5. **Failure Analysis**: Does component introduce new errors?

### 24.3 Success Criteria

| Metric | Target |
|------|--------|
| **Human Preference (Processed)** | ≥60% win rate |
| **No Regression** | FP rate ≤ baseline FP rate |
| **Net Quality Gain** | Mean human score Δ ≥ +0.3 |

---

## 25. Cost / Value Assessment Framework

### 25.1 Cost Dimensions

| Cost Category | Factors |
|---------------|---------|
| **Evaluation Cost** | Evaluator hours × rate × passages × raters |
| **Calibration Cost** | Engineering + statistician time |
| **Operational Cost** | Runtime overhead if gate enabled |
| **False Positive Cost** | User-visible bad output; reputational |
| **False Negative Cost** | Retry compute + latency |
| **Maintenance** | Rubric updates, evaluator retraining, model drift monitoring |

### 25.2 Value Dimensions

| Value | Measurement |
|-------|-------------|
| **Quality Gain** | Human score Δ vs baseline |
| **User Retention** | Proxy: quality correlation with user metrics |
| **Brand Protection** | FP rate reduction × user exposure |
| **Operational Efficiency** | FN rate reduction × retry cost |

### 25.3 Promotion Decision Rule

| Condition | Action |
|-----------|--------|
| **Net Value > Cost AND FP/FN acceptable** | PROMOTION_READY |
| **Quality Gain BUT Cost > Value** | OBSERVATIONAL_ONLY |
| **Unstable / Low Agreement** | CALIBRATION_REQUIRED |
| **Human Disagreement High** | MANUAL_REVIEW_REQUIRED |
| **No Evidence of Benefit** | NOT_WORTH_PROMOTING |

---

## 26. Dataset Schema

### 26.1 Core Tables

#### `sources`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | string | Yes | Unique passage identifier |
| `source_text` | text | Yes | Korean source passage |
| `source_language` | string | Yes | `ko` |
| `source_unit` | enum | Yes | `paragraph` \| `scene` \| `chapter` |
| `genre` | string | Yes | Sub-genre |
| `dialogue_density` | float | Yes | 0.0-1.0 |
| `scene_type` | enum | Yes | `dialogue` \| `narration` \| `action` \| `introspection` \| `exposition` |
| `char_count` | int | Yes | Korean characters |
| `sentence_count` | int | Yes | |
| `paragraph_count` | int | Yes | |
| `terminology_density` | enum | Yes | `low` \| `medium` \| `high` |
| `chapter_id` | string | Yes | For leakage prevention |
| `scene_id` | string | Yes | For leakage prevention |
| `license` | string | Yes | Provenance |

#### `candidates`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | string | Yes | Unique |
| `source_id` | string | Yes | FK → sources |
| `candidate_text` | text | Yes | Traditional Chinese translation |
| `model` | string | Yes | `meta/llama-3.2-90b-vision-instruct` |
| `provider` | string | Yes | `nvidia` |
| `prompt_version` | string | Yes | |
| `runtime_version` | string | Yes | |
| `attempt_number` | int | Yes | 1-based |
| `temperature` | float | Yes | |
| `max_tokens` | int | Yes | |
| `configuration_hash` | string | Yes | SHA256 |
| `timestamp` | datetime | Yes | ISO 8601 |

#### `references`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reference_id` | string | Yes | Unique |
| `source_id` | string | Yes | FK → sources |
| `reference_text` | text | Yes | Traditional Chinese |
| `reference_class` | enum | Yes | `GOLD` \| `SILVER` \| `BRONZE` |
| `translator_id` | string | Yes | Pseudonymous |
| `reviewer_ids` | array[string] | Yes | Pseudonymous |
| `approval_date` | datetime | Yes | |
| `revision_count` | int | Yes | |
| `terminology_policy` | string | Yes | Policy document reference |

#### `evaluations`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evaluation_id` | string | Yes | Unique |
| `candidate_id` | string | Yes | FK → candidates |
| `evaluator_id` | string | Yes | Pseudonymous |
| `evaluation_method` | enum | Yes | `absolute` \| `pairwise` \| `pairwise_with_reference` |
| `naturalness` | int | Yes | 1-7 |
| `fidelity` | int | Yes | 1-7 |
| `character_voice` | int | Yes | 1-7 |
| `register_tone` | int | Yes | 1-7 |
| `coherence` | int | Yes | 1-7 |
| `terminology` | int | Yes | 1-7 |
| `overall` | int | Yes | 1-7 |
| `acceptance` | enum | Yes | `ACCEPT` \| `REJECT` |
| `failure_tags` | array[string] | No | Multi-label |
| `pairwise_preference` | enum | Conditional | `A` \| `B` \| `TIE` (for pairwise) |
| `confidence` | int | Yes | 1-5 |
| `duration_seconds` | int | Yes | |
| `timestamp` | datetime | Yes | ISO 8601 |
| `session_id` | string | Yes | For fatigue tracking |

#### `ps03_measurements`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | string | Yes | FK → candidates |
| `plot_fidelity_proxy` | float | Yes | 0-30 |
| `locked_names_terms` | float | Yes | 0-20 |
| `natural_chinese_proxy` | float | Yes | 0-20 |
| `subject_pronoun_proxy` | float | Yes | 0-15 |
| `character_voice_dialogue_proxy` | float | Yes | 0-10 |
| `format_punctuation` | float | Yes | 0-5 |
| `aggregate_score` | float | Yes | 0-100 |
| `ps03_version` | string | Yes | e.g., `1.2` |

---

## 27. Versioning & Reproducibility

### Versioning Requirements

| Artifact | Versioning |
|----------|------------|
| **Dataset** | Semantic version (v1.0.0, v1.1.0, etc.) |
| **Schema** | Semantic version; breaking changes = major |
| **Rubric** | Semantic version; anchors/rules = minor |
| **Evaluator Protocol** | Semantic version |
| **Metric Code** | Git commit SHA + semantic version |
| **Splits** | Fixed random seed + split hash |

### Reproducibility Package

| Component | Requirement |
|-----------|-------------|
| **Dataset Snapshot** | Immutable archive (hash-verified) |
| **Metric Code** | Git commit SHA |
| **Configuration** | Full YAML/JSON config |
| **Random Seeds** | All seeds documented |
| **Split Assignment** | Deterministic assignment log |
| **Analysis Code** | Notebook/script with pinned dependencies |
| **Environment** | `requirements.txt` / `pyproject.toml` with hashes |

---

## 28. Pilot Study Design

### 28.1 Pilot Objectives

| Objective | Success Criterion |
|-----------|-------------------|
| Rubric clarity | ≥90% evaluators rate instructions "clear" |
| Inter-rater reliability | Weighted κ ≥0.60 on calibration set |
| Label distribution | No dimension with >80% in single category |
| Time burden | ≤12 min/passage; ≤10 passages/session |
| Evaluator fatigue | No significant score drift within session |
| PS-03 correlation | Preliminary ρ ≥0.30 on ≥50 passages |

### 28.2 Pilot Scope

| Scope | Target |
|-------|---------|
| **Passages** | 50 (stratified) |
| **Evaluators** | 3-5 qualified |
| **Candidates per passage** | 2-3 (baseline + 1-2 variants) |
| **Duration** | 2-3 weeks |

### 28.3 Pilot Outputs

| Output | Decision |
|-----------|----------|
| Revised rubric | YES/NO |
| Revised sampling | YES/NO |
| Revised evaluator protocol | YES/NO |
| Calibration design revision | YES/NO |
| Go/No-Go for full calibration | GO / NO-GO |

---

## 29. Stopping Criteria

### Calibration Phase

| Condition | Action |
|-----------|--------|
| **Stable validation** (metrics ±0.02 over 3 epochs) | STOP — proceed to holdout |
| **Diverging validation** (metric degrading) | STOP — revise methodology |
| **Cost > Budget** (pre-defined cap) | STOP — scope reduction |
| **Agreement < 0.40** after rubric revision | STOP — abandon metric |

### Promotion Phase

| Condition | Action |
|-----------|--------|
| **Holdout AUC ≥0.80** AND FP/FN acceptable | PROMOTION_READY |
| **Holdout AUC <0.70** after full calibration | REMAIN OBSERVATIONAL |
| **FP/FN cost > Budget** | REMAIN OBSERVATIONAL |
| **Agreement < 0.60** on holdout | MANUAL_REVIEW_REQUIRED |

---

## 30. Promotion Criteria

A non-production area may enter `CONTRACT_PROMOTION` task **only if ALL** hold:

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | **Valid Definition** | Dimension clearly defined; anchors unambiguous |
| 2 | **Reliable Measurement** | PS-03 metric computable deterministically |
| 3 | **Human Evaluation Evidence** | ≥3 evaluators, κw ≥0.60 on calibration |
| 4 | **Reference Evidence** | ≥50 GOLD/SILVER reference passages |
| 5 | **Reproducible Methodology** | Full reproducibility package |
| 6 | **Calibration Evidence** | ρ ≥0.50 per dimension; ρ ≥0.65 aggregate |
| 7 | **Holdout Validation** | AUC ≥0.80; FP/FN within cost budget |
| 8 | **Error Analysis** | FP/FN categorized; root causes identified |
| 9 | **Stability** | Metric stable across genre/scene strata |
| 10 | **Production Suitability** | Net value > cost; FP/FN acceptable per policy |

**Missing ANY criterion → DO NOT PROMOTE**

---

## 31. Non-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Execute calibration | Separate task |
| Recruit evaluators | Separate task |
| Build reference corpus | Separate task |
| Modify PS-03 code | Only after promotion |
| Implement Best Attempt | Only after promotion |
| Implement Segment Merge | Only after promotion |
| Enable Context Continuity | Only after promotion |
| Implement Reviewer/Editor/ACE | Only after promotion |
| Change 80/65 thresholds | Only after calibration |
| Change PS-03 weights | Only after calibration |
| Real translation execution | Prohibited |
| Provider calls | Prohibited |

---

## 32. Explicitly Deferred Items

| Item | Deferred To |
|------|-------------|
| Actual dataset construction | `DATASET_CONSTRUCTION` task |
| Evaluator recruitment/training | `EVALUATOR_RECRUITMENT` task |
| Pilot study execution | `PILOT_STUDY` task |
| Full calibration execution | `CALIBRATION_EXECUTION` task |
| Contract promotion implementation | `CONTRACT_PROMOTION` task per area |
| Best Attempt Selector implementation | `QUALITY-RUNTIME-REPAIR` task |
| Segment Merge implementation | `QUALITY-RUNTIME-REPAIR` task |
| Context Continuity enablement | `FEATURE_GATE_DECISION` task |
| Reviewer/Editor/ACE implementation | Separate architecture task |

---

## 33. Production Boundary Verification

| Boundary | Status | Verification |
|----------|--------|--------------|
| Model Frozen | ✅ | `meta/llama-3.2-90b-vision-instruct` |
| Provider Frozen | ✅ | `nvidia` |
| Retry Boundary | ✅ LOCKED | Max 5, provider switch after 3, chunk halving |
| Context Feature | ✅ OFF | `quality_context_scene_v72=false` |
| PS-03 Weights | ✅ FROZEN | 30/20/20/15/10/5 |
| PS-03 Thresholds | ✅ FROZEN | 80/65 |
| Production Gates | ✅ PRESERVED | 14 deterministic gates |
| Real Translation | ✅ 0 | No provider calls |
| Network Execution | ✅ 0 | No API calls |

---

*End of Design Document*

**Design Path**: `artifacts/NTPE_S7_09_LITERARY_QUALITY_EVALUATION_CALIBRATION_DESIGN.md`
**Status**: `DESIGN_COMPLETE`