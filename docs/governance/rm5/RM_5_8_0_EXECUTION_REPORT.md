# RM-5.8.0 — Benchmark Execution Report Template

## Overview

This document defines the **Execution Report Template** for benchmark runs. Every benchmark execution produces a standardized report capturing all relevant metadata, results, and regression analysis.

---

## Report Structure

```markdown
# Knowledge Benchmark Execution Report

## Run Metadata
| Field | Value |
|-------|-------|
| **Run ID** | `bench_20260804_001` |
| **Timestamp (UTC)** | `2026-08-04T10:30:00Z` |
| **Duration** | `00:12:34` |
| **Trigger** | `prompt_update: character_extractor_v2.1` |
| **Operator** | `ci-bot` / `manual: username` |

## Environment
| Component | Version |
|-----------|---------|
| **Benchmark Framework** | `RM-5.8.0` |
| **Golden Dataset** | `v1.0.0` |
| **Knowledge Runtime** | `v5.7.6` |
| **Python** | `3.11.9` |
| **Platform** | `Windows-10-10.0.19045` |

## Configuration
| Parameter | Value |
|-----------|-------|
| **Prompt Package** | `prompt_v2.1_fewshot_5` |
| **Model** | `gpt-4o-2024-08-06` |
| **Temperature** | `0.3` |
| **Top-p** | `0.9` |
| **Max Tokens** | `4096` |
| **Few-shot Count** | `5` |
| **Seed** | `42` |

## Golden Dataset Summary
| Extractor | Easy | Medium | Hard | Total |
|-----------|------|--------|------|-------|
| Character | 10 | 10 | 5 | 25 |
| Glossary | 10 | 10 | 5 | 25 |
| Scene | 10 | 10 | 5 | 25 |
| Narrative | 10 | 10 | 5 | 25 |
| Style | 10 | 10 | 5 | 25 |
| **Total** | **50** | **50** | **25** | **125** |
```
## Extraction Summary
| Extractor | Input Cases | Successful | Failed | Success Rate |
|-----------|-------------|------------|--------|--------------|
| Character | 25 | 25 | 0 | 100% |
| Glossary | 25 | 25 | 0 | 100% |
| Scene | 25 | 24 | 1 | 96% |
| Narrative | 25 | 25 | 0 | 100% |
| Style | 25 | 23 | 2 | 92% |
| **Total** | **125** | **122** | **3** | **97.6%** |

## Metric Results (Per Extractor)

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
## Overall Results
| Metric | Value |
|--------|-------|
| Character Score | 0.9134 |
| Glossary Score | 0.9287 |
| Scene Score | 0.8723 |
| Narrative Score | 0.8412 |
| Style Score | 0.8045 |
| **Overall Score** | **0.8720** |
| **Grade** | **B** |

## Regression Analysis
| Extractor | Baseline F1 | Current F1 | Delta | Threshold | Status |
|-----------|-------------|------------|-------|-----------|--------|
| Character | 0.9050 | 0.8998 | -0.0052 | 0.02 | ✅ PASS |
| Glossary | 0.9200 | 0.9175 | -0.0025 | 0.02 | ✅ PASS |
| Scene | 0.8650 | 0.8595 | -0.0055 | 0.02 | ✅ PASS |
| Narrative | 0.8450 | 0.8377 | -0.0073 | 0.02 | ✅ PASS |
| Style | 0.8150 | 0.8109 | -0.0041 | 0.02 | ✅ PASS |
| **Overall** | **0.8700** | **0.8720** | **+0.0020** | 0.015 | ✅ PASS |

**Regression Detected**: NO

## Failed Cases Detail

### Scene - Hard Case 003
- **Benchmark ID**: `scene_hard_003`
- **Error**: Extraction timeout (> 60s)
- **Input Length**: 3,421 chars
- **Action**: Investigate prompt efficiency for complex scenes

### Style - Medium Case 007
- **Benchmark ID**: `style_medium_007`
- **Error**: Schema validation failed - missing `rhythm` field
- **Action**: Check extractor output schema compliance

### Style - Hard Case 002
- **Benchmark ID**: `style_hard_002`
- **Error**: Model refused (content policy)
- **Action**: Review prompt for policy compliance

## Artifacts Produced
| Artifact | Path |
|----------|------|
| Scorecard | `benchmarks/results/current/scorecard.md` |
| Raw Metrics (JSON) | `benchmarks/results/current/metrics.json` |
| Extraction Outputs | `benchmarks/results/current/extractions/` |
| Regression Report | `benchmarks/results/current/regression.json` |
| Run Log | `benchmarks/results/current/run.log` |

## Recommendations
1. **Style Extractor**: Precision below target (0.8234 vs 0.85). Review few-shot examples for style detection.
2. **Style Extractor**: Hallucination rate high (0.1766 vs 0.15). Add negative examples to few-shot.
3. **Narrative Extractor**: Business rule pass rate below target. Review rule definitions.
4. **Scene Hard Cases**: Timeout on complex inputs. Consider input chunking or prompt optimization.

## Sign-off
| Role | Name | Status |
|------|------|--------|
| **Executed By** | ci-bot | ✅ |
| **Reviewed By** | — | ⏳ |
| **Approved By** | — | ⏳ |
---

## JSON Report Schema (for automation)

```json
{
  "run_id": "bench_20260804_001",
  "timestamp": "2026-08-04T10:30:00Z",
  "duration_seconds": 754,
  "trigger": "prompt_update: character_extractor_v2.1",
  "environment": {
    "benchmark_version": "RM-5.8.0",
    "golden_dataset_version": "v1.0.0",
    "runtime_version": "v5.7.6",
    "python_version": "3.11.9",
    "platform": "Windows-10-10.0.19045"
  },
  "configuration": {
    "prompt_package": "prompt_v2.1_fewshot_5",
    "model": "gpt-4o-2024-08-06",
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 4096,
    "few_shot_count": 5,
    "seed": 42
  },
  "golden_summary": {
    "character": {"easy": 10, "medium": 10, "hard": 5},
    "glossary": {"easy": 10, "medium": 10, "hard": 5},
    "scene": {"easy": 10, "medium": 10, "hard": 5},
    "narrative": {"easy": 10, "medium": 10, "hard": 5},
    "style": {"easy": 10, "medium": 10, "hard": 5}
  },
  "extraction_summary": {
    "character": {"input": 25, "success": 25, "failed": 0},
    "glossary": {"input": 25, "success": 25, "failed": 0},
    "scene": {"input": 25, "success": 24, "failed": 1},
    "narrative": {"input": 25, "success": 25, "failed": 0},
    "style": {"input": 25, "success": 23, "failed": 2}
  },
  "metrics": {
    "character": {"precision": 0.9123, "recall": 0.8876, "f1": 0.8998, "extractor_score": 0.9134},
    "glossary": {"precision": 0.9345, "recall": 0.9012, "f1": 0.9175, "extractor_score": 0.9287},
    "scene": {"precision": 0.8765, "recall": 0.8432, "f1": 0.8595, "extractor_score": 0.8723},
    "narrative": {"precision": 0.8543, "recall": 0.8217, "f1": 0.8377, "extractor_score": 0.8412},
    "style": {"precision": 0.8234, "recall": 0.7987, "f1": 0.8109, "extractor_score": 0.8045}
  },
  "overall": {
    "score": 0.8720,
    "grade": "B"
  },
  "regression": {
    "detected": false,
    "details": [
      {"extractor": "character", "baseline_f1": 0.9050, "current_f1": 0.8998, "delta": -0.0052},
      {"extractor": "glossary", "baseline_f1": 0.9200, "current_f1": 0.9175, "delta": -0.0025},
      {"extractor": "scene", "baseline_f1": 0.8650, "current_f1": 0.8595, "delta": -0.0055},
      {"extractor": "narrative", "baseline_f1": 0.8450, "current_f1": 0.8377, "delta": -0.0073},
      {"extractor": "style", "baseline_f1": 0.8150, "current_f1": 0.8109, "delta": -0.0041}
    ]
  },
  "failures": [
    {"extractor": "scene", "case": "scene_hard_003", "error": "timeout"},
    {"extractor": "style", "case": "style_medium_007", "error": "schema_validation"},
    {"extractor": "style", "case": "style_hard_002", "error": "model_refusal"}
  ],
  "artifacts": {
    "scorecard": "benchmarks/results/current/scorecard.md",
    "metrics_json": "benchmarks/results/current/metrics.json",
    "extractions_dir": "benchmarks/results/current/extractions/",
    "regression_json": "benchmarks/results/current/regression.json",
    "run_log": "benchmarks/results/current/run.log"
  },
  "recommendations": [
    "Style Extractor: Precision below target. Review few-shot examples.",
    "Style Extractor: Hallucination rate high. Add negative examples.",
    "Narrative Extractor: Business rule pass rate below target. Review rules.",
    "Scene Hard Cases: Timeout on complex inputs. Consider chunking."
  ]
}
```

---

## Acceptance Criteria for This Document

- [ ] Report template covers all required sections
- [ ] Markdown format for human readability
- [ ] JSON schema for automation/parsing
- [ ] All metric categories represented
- [ ] Regression analysis section included
- [ ] Failed cases detail section included
- [ ] Artifacts listing included
- [ ] Recommendations section included