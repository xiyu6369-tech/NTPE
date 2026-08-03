# RM-5.8.0 — Benchmark Metrics Definition

## Overview

This document defines all **Benchmark Metrics** for the Knowledge Layer Benchmark Framework. Metrics are computed by comparing Knowledge Extractor outputs against the Golden Dataset.

**Scope**: Metric definitions only. No computation implementation in this stage.

---

## Metric Categories

| Category | Purpose |
|----------|---------|
| **Accuracy** | How correct are the extractions? |
| **Extraction** | Completeness and purity of extraction |
| **Validation** | Schema and rule compliance |
| **Confidence** | Calibration of confidence scores |
| **Runtime** | Build and verification success |

---

## 1. Accuracy Metrics

### Precision
```
Precision = TP / (TP + FP)
```
- **TP (True Positive)**: Correctly extracted entity matching golden entity
- **FP (False Positive)**: Extracted entity not in golden dataset
- **Scope**: Per-extractor, macro-averaged across difficulty tiers

### Recall
```
Recall = TP / (TP + FN)
```
- **FN (False Negative)**: Golden entity not extracted
- **Scope**: Per-extractor, macro-averaged across difficulty tiers

### F1 Score
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```
- **Primary Metric**: F1 is the headline accuracy metric
- **Baseline Target**: ≥ 0.85 for Easy, ≥ 0.75 for Medium, ≥ 0.65 for Hard

---

## 2. Extraction Metrics

### Missing Rate
```
Missing_Rate = FN / (TP + FN) = 1 - Recall
```
- Measures completeness
- **Target**: ≤ 0.15 (Easy), ≤ 0.25 (Medium), ≤ 0.35 (Hard)

### Hallucination Rate
```
Hallucination_Rate = FP / (TP + FP) = 1 - Precision
```
- Measures fabrication/spurious extraction
- **Target**: ≤ 0.10 (Easy), ≤ 0.15 (Medium), ≤ 0.20 (Hard)

### Duplicate Rate
```
Duplicate_Rate = Duplicate_Entities / Total_Extracted_Entities
```
- Entities with same ID or semantically equivalent
- **Target**: 0.0 (zero tolerance)

---

## 3. Validation Metrics

### Schema Pass Rate
```
Schema_Pass_Rate = Valid_Entities / Total_Entities
```
- Entity conforms to extractor-specific JSON schema
- **Target**: 1.0 (100%)

### Business Rule Pass Rate
```
Business_Rule_Pass_Rate = Rule_Compliant_Entities / Total_Entities
```
- Domain-specific rules (e.g., character must have name, glossary must have translation)
- **Target**: ≥ 0.95

### Review Pass Rate
```
Review_Pass_Rate = Review_Approved_Entities / Total_Entities
```
- Passes human-review simulation rules (auto-review criteria)
- **Target**: ≥ 0.90

---

## 4. Confidence Metrics

### Confidence Calibration (ECE - Expected Calibration Error)
```
ECE = Σ (|accuracy(bin) - confidence(bin)| * |bin| / N)
```
- Bins: 10 equal-width bins [0.0-0.1, 0.1-0.2, ..., 0.9-1.0]
- **Target**: ECE ≤ 0.05

### False High Confidence Rate
```
False_High_Confidence = Count(confidence ≥ 0.8 AND incorrect) / Count(confidence ≥ 0.8)
```
- High confidence but wrong extraction
- **Target**: ≤ 0.05

### False Low Confidence Rate
```
False_Low_Confidence = Count(confidence < 0.5 AND correct) / Count(confidence < 0.5)
```
- Low confidence but correct extraction (overly conservative)
- **Target**: ≤ 0.10

---

## 5. Runtime Metrics

### Compilation Success
```
Compilation_Success = Successful_Compilations / Total_Packages
```
- Knowledge Package compiles without error
- **Target**: 1.0 (100%)

### Package Verification
```
Package_Verification = Verified_Packages / Total_Packages
```
- Package passes all verification checks (checksum, schema, completeness)
- **Target**: 1.0 (100%)

### Deterministic Rebuild
```
Deterministic_Rebuild = Identical_Outputs / Rebuild_Attempts
```
- Same input → identical Knowledge Package (byte-for-byte)
- **Target**: 1.0 (100%)

---

## Aggregation Rules

### Per-Extractor Score
```
Extractor_Score = weighted_average(
    F1 * 0.40 +
    (1 - Missing_Rate) * 0.15 +
    (1 - Hallucination_Rate) * 0.15 +
    Schema_Pass_Rate * 0.10 +
    Business_Rule_Pass_Rate * 0.10 +
    (1 - ECE) * 0.10
)
```

### Overall Score
```
Overall_Score = mean(Extractor_Scores)  # Equal weight across 5 extractors
```

---

## Metric Computation Requirements

| Requirement | Specification |
|-------------|---------------|
| **Precision/Recall Matching** | Exact ID match + semantic equivalence (configurable) |
| **Confidence Binning** | 10 equal-width bins |
| **Decimal Precision** | 4 decimal places for all metrics |
| **Aggregation** | Macro-average across difficulty tiers, then mean across extractors |
| **Baseline Storage** | JSON in `benchmarks/results/baseline/` |

---

## Acceptance Criteria for This Document

- [ ] All 5 metric categories defined
- [ ] Formulas provided for each metric
- [ ] Target thresholds specified
- [ ] Aggregation rules defined
- [ ] Computation requirements specified