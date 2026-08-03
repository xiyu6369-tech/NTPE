# RM-5.8.0 — Scorecard Specification

## Overview

This document defines the **Scorecard Format** for the Knowledge Benchmark Framework. Every benchmark run produces a standardized scorecard enabling comparison across runs, versions, and configurations.

---

## Scorecard Structure

```markdown
# Knowledge Benchmark Scorecard

**Run ID**: `bench_20260804_001`
**Timestamp**: `2026-08-04T10:30:00Z`
**Golden Dataset Version**: `v1.0.0`
**Benchmark Version**: `RM-5.8.0`
**Configuration**: `prompt_v2.1_fewshot_5_model_gpt-4o`

---

## Extractor Scores

### Character
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Precision | 0.9123 | ≥ 0.85 | ✅ PASS |
| Recall | 0.8876 | ≥ 0.85 | ✅ PASS |
| F1 | 0.8998 | ≥ 0.85 | ✅ PASS |
| Missing Rate | 0.1124 | ≤ 0.15 | ✅ PASS |
| Hallucination Rate | 0.0877 | ≤ 0.10 | ✅ PASS |
| Duplicate Rate | 0.0000 | 0.00 | ✅ PASS |
| Schema Pass Rate | 1.0000 | 1.00 | ✅ PASS |
| Business Rule Pass Rate | 0.9782 | ≥ 0.95 | ✅ PASS |
| Review Pass Rate | 0.9456 | ≥ 0.90 | ✅ PASS |
| ECE | 0.0321 | ≤ 0.05 | ✅ PASS |
| False High Confidence | 0.0234 | ≤ 0.05 | ✅ PASS |
| False Low Confidence | 0.0567 | ≤ 0.10 | ✅ PASS |
| **Extractor Score** | **0.9134** | — | — |

### Glossary
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Precision | 0.9345 | ≥ 0.85 | ✅ PASS |
| Recall | 0.9012 | ≥ 0.85 | ✅ PASS |
| F1 | 0.9175 | ≥ 0.85 | ✅ PASS |
| Missing Rate | 0.0988 | ≤ 0.15 | ✅ PASS |
| Hallucination Rate | 0.0655 | ≤ 0.10 | ✅ PASS |
| Duplicate Rate | 0.0000 | 0.00 | ✅ PASS |
| Schema Pass Rate | 1.0000 | 1.00 | ✅ PASS |
| Business Rule Pass Rate | 0.9891 | ≥ 0.95 | ✅ PASS |
| Review Pass Rate | 0.9623 | ≥ 0.90 | ✅ PASS |
| ECE | 0.0287 | ≤ 0.05 | ✅ PASS |
| False High Confidence | 0.0189 | ≤ 0.05 | ✅ PASS |
| False Low Confidence | 0.0432 | ≤ 0.10 | ✅ PASS |
| **Extractor Score** | **0.9287** | — | — |

### Scene
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Precision | 0.8765 | ≥ 0.85 | ✅ PASS |
| Recall | 0.8432 | ≥ 0.75 | ✅ PASS |
| F1 | 0.8595 | ≥ 0.75 | ✅ PASS |
| Missing Rate | 0.1568 | ≤ 0.25 | ✅ PASS |
| Hallucination Rate | 0.1235 | ≤ 0.15 | ✅ PASS |
| Duplicate Rate | 0.0000 | 0.00 | ✅ PASS |
| Schema Pass Rate | 1.0000 | 1.00 | ✅ PASS |
| Business Rule Pass Rate | 0.9567 | ≥ 0.95 | ✅ PASS |
| Review Pass Rate | 0.9123 | ≥ 0.90 | ✅ PASS |
| ECE | 0.0412 | ≤ 0.05 | ✅ PASS |
| False High Confidence | 0.0345 | ≤ 0.05 | ✅ PASS |
| False Low Confidence | 0.0789 | ≤ 0.10 | ✅ PASS |
| **Extractor Score** | **0.8723** | — | — |

### Narrative
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Precision | 0.8543 | ≥ 0.85 | ✅ PASS |
| Recall | 0.8217 | ≥ 0.75 | ✅ PASS |
| F1 | 0.8377 | ≥ 0.75 | ✅ PASS |
| Missing Rate | 0.1783 | ≤ 0.25 | ✅ PASS |
| Hallucination Rate | 0.1457 | ≤ 0.15 | ✅ PASS |
| Duplicate Rate | 0.0000 | 0.00 | ✅ PASS |
| Schema Pass Rate | 1.0000 | 1.00 | ✅ PASS |
| Business Rule Pass Rate | 0.9432 | ≥ 0.95 | ❌ FAIL |
| Review Pass Rate | 0.8987 | ≥ 0.90 | ❌ FAIL |
| ECE | 0.0456 | ≤ 0.05 | ✅ PASS |
| False High Confidence | 0.0389 | ≤ 0.05 | ✅ PASS |
| False Low Confidence | 0.0821 | ≤ 0.10 | ✅ PASS |
| **Extractor Score** | **0.8412** | — | — |

### Style
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Precision | 0.8234 | ≥ 0.85 | ❌ FAIL |
| Recall | 0.7987 | ≥ 0.75 | ✅ PASS |
| F1 | 0.8109 | ≥ 0.75 | ✅ PASS |
| Missing Rate | 0.2013 | ≤ 0.25 | ✅ PASS |
| Hallucination Rate | 0.1766 | ≤ 0.15 | ❌ FAIL |
| Duplicate Rate | 0.0000 | 0.00 | ✅ PASS |
| Schema Pass Rate | 1.0000 | 1.00 | ✅ PASS |
| Business Rule Pass Rate | 0.9345 | ≥ 0.95 | ❌ FAIL |
| Review Pass Rate | 0.8876 | ≥ 0.90 | ❌ FAIL |
| ECE | 0.0489 | ≤ 0.05 | ✅ PASS |
| False High Confidence | 0.0412 | ≤ 0.05 | ✅ PASS |
| False Low Confidence | 0.0912 | ≤ 0.10 | ✅ PASS |
| **Extractor Score** | **0.8045** | — | — |

---

## Overall Score

| Metric | Value |
|--------|-------|
| Character | 0.9134 |
| Glossary | 0.9287 |
| Scene | 0.8723 |
| Narrative | 0.8412 |
| Style | 0.8045 |
| **Overall Score** | **0.8720** |

---

## Grade

| Overall Score | Grade |
|---------------|-------|
| ≥ 0.95 | A+ |
| ≥ 0.90 | A |
| ≥ 0.80 | B |
| ≥ 0.70 | C |
| < 0.70 | F |

**Result: B**

---

## Regression Check

| Extractor | Baseline F1 | Current F1 | Delta | Status |
|-----------|-------------|------------|-------|--------|
| Character | 0.9050 | 0.8998 | -0.0052 | ✅ PASS |
| Glossary | 0.9200 | 0.9175 | -0.0025 | ✅ PASS |
| Scene | 0.8650 | 0.8595 | -0.0055 | ✅ PASS |
| Narrative | 0.8450 | 0.8377 | -0.0073 | ✅ PASS |
| Style | 0.8150 | 0.8109 | -0.0041 | ✅ PASS |

**Regression Threshold**: F1 drop > 0.02 (2 percentage points)
**Result**: NO REGRESSION DETECTED

---

## Summary

- **Total Entities Tested**: 1,250
- **Total Extractions**: 1,187
- **Pass Rate (Extractor Score ≥ 0.85)**: 3/5 (60%)
- **Critical Failures**: Style (Precision, Hallucination, Business Rule, Review)
- **Recommendation**: Investigate Style extractor prompt and few-shot examples