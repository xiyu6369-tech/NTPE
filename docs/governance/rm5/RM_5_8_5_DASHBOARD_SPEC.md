# RM-5.8.5 — Dashboard Specification

## Overview

This document defines the format and content of the Knowledge Benchmark Dashboard.

The dashboard provides an at-a-glance quality report that answers: "What is the current quality of the Knowledge Extraction Layer?"

---

## Output Files

```
benchmarks/results/dashboard/
├── dashboard.md        # Human-readable markdown
└── dashboard.json      # Machine-readable JSON
```

---

## Dashboard Sections

### 1. Overall Score

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | float | Aggregate benchmark score (0.0–1.0) |
| `overall_grade` | string | Letter grade: A+, A, B, C, F |

### 2. Extractor Scores

Per-extractor breakdown:

| Column | Description |
|--------|-------------|
| Extractor | Display name (Character, Glossary, Scene, Narrative, Style) |
| Score | Weighted extractor score |
| Grade | Letter grade |
| F1 | F1 score |
| Precision | Precision score |
| Recall | Recall score |
| ECE | Expected Calibration Error |

### 3. Regression Check

| Column | Description |
|--------|-------------|
| Extractor | Extractor name |
| Baseline F1 | Baseline F1 score |
| Current F1 | Current F1 score |
| Delta | Change from baseline |
| Status | PASS or FAIL |

### 4. Trend

Per-extractor trend direction:
- **Improving** — score increasing over runs
- **Stable** — score unchanged
- **Regression** — score decreasing
- **Insufficient Data** — not enough runs

### 5. Suggestions

Actionable improvement items ranked by priority.

### 6. Metadata

- Framework version
- Golden dataset version
- Timestamp
- Runtime environment

---

## JSON Schema

```json
{
  "overall_score": 0.0,
  "overall_grade": "F",
  "extractors": [
    {
      "extractor": "character",
      "display_name": "Character",
      "score": 0.0,
      "grade": "F",
      "precision": 0.0,
      "recall": 0.0,
      "f1": 0.0,
      "ece": 0.0,
      "missing_rate": 0.0,
      "hallucination_rate": 0.0,
      "schema_pass_rate": 0.0,
      "cases": {
        "total": 0,
        "passed": 0
      }
    }
  ],
  "regression_status": "PASS",
  "regression_details": [],
  "trend": {},
  "suggestions": [],
  "metadata": {},
  "generated_at": "ISO-8601 timestamp"
}
```

---

## Markdown Template

```markdown
# NTPE Knowledge Benchmark Dashboard

**Generated**: `YYYY-MM-DDTHH:MM:SS+00:00`

---

## Overall Score

**Score**: XX.XX%
**Grade**: **X**

---

## Per-Extractor Scores

| Extractor | Score | Grade | F1 | Precision | Recall | ECE |
|-----------|-------|-------|----|-----------|--------|-----|
| Character | XXXX | X | XXXX | XXXX | XXXX | XXXX |
| Glossary  | XXXX | X | XXXX | XXXX | XXXX | XXXX |
...

---

## Regression Check

**Status**: PASS

| Extractor | Baseline F1 | Current F1 | Delta | Status |
|-----------|-------------|------------|-------|--------|
...

---

## Trend

- **character**: Improving
...

---

## Suggestions

1. ...
2. ...

---

## Metadata

- **version**: RM-5.8.5
- **golden_dataset**: v1.0.0
- **timestamp**: ...

---

*Generated: ...*
*NTPE Knowledge Benchmark Runner (RM-5.8.5)*
```

---

## Generation

The dashboard is generated from:
1. `overall_scorecard.json` (from `benchmarks/results/current/`)
2. Regression check results
3. Analysis engine output
4. Trend history from `benchmarks/results/history/`

**Command**:
```bash
python -m tools.knowledge_benchmark.cli --dashboard
```

---

## History Preservation

Dashboard outputs are **not** archived to history (they are derived). The source `overall_scorecard.json` and `analysis_report.json` are archived instead. Dashboard can be regenerated from history at any time.

---

## Governance Rules

1. **Dashboard is read-only** — not a source of truth, derived from scorecards
2. **Regeneratable** — any benchmark run can have a dashboard generated
3. **Human-readable first** — `dashboard.md` is the primary output
4. **Machine-readable second** — `dashboard.json` for CI/CD integration
5. **No modification of source data** — dashboard generation is pure read

---

## Version

RM-5.8.5 — Knowledge Benchmark Dashboard Specification