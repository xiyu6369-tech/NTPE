# RM-5 Design Principles

**Version**: RM-5.0  
**Purpose**: Governing design rules for all RM-5.x stages. Every proposed change must be justified against these principles.

---

## Principle 1 — Translation Quality First

> Any modification must measurably improve readability, consistency, or naturalness of translated output.

**Requirements:**
- Every change must identify which quality dimension it targets: readability, character consistency, terminology precision, narrative flow, or tone preservation.
- "Adding a feature" is not sufficient justification — the feature must demonstrably improve output quality.
- No refactoring without a quality-driven rationale.

**Anti-patterns:**
- Adding abstraction layers "for future use"
- Performance-only changes that don't affect output quality
- Infrastructure changes without a quality link

**Measurement:**
- Regression tests must pass against RM-4 baseline output
- New quality benchmarks must show improvement

---

## Principle 2 — Architecture Simplicity

> Avoid duplication, wrapper explosion, and dead pipeline code.

**Requirements:**
- One pipeline, one owner — no duplicated logic paths.
- No wrappers around wrappers (single delegation chain max).
- Remove or archive any pipeline path that is no longer invoked by production runtime.

**Anti-patterns:**
- Creating "V2" modules while "V1" remains active
- Adding adapter layers that don't change behavior
- Maintaining parallel pipelines (legacy + new)

**Enforcement:**
- Pipeline audit in RM-5.1 will identify all active paths.
- Dead paths will be archived, not deleted.

---

## Principle 3 — Frozen Compatibility

> RM-4 Freeze must never be broken.

**Absolute constraints:**
- No modification to any Python file in `core/`, `lts/`, `tools/`, `tests/`.
- No renaming, no moving, no deleting of any frozen file.
- All existing tests must continue to pass without modification.

**What IS allowed during RM-5.0:**
- Creating new documentation in `docs/governance/rm5/`.
- Creating new test directories under `tests/` (for future RM-5.x tests).
- Adding new configuration files (not modifying existing ones).

**What IS NOT allowed:**
- Creating new wrapper modules that override frozen behavior.
- Installing new Python packages that change frozen module behavior.
- Any runtime behavior modification whatsoever.

---

## Principle 4 — Evidence Driven

> Every optimization decision must be backed by regression results, benchmark data, and quality reports.

**Required evidence types:**
1. **Regression Evidence**: Before/after diff of representative sample translations.
2. **Benchmark Data**: Quantitative metrics (speed, token usage, success rate).
3. **Quality Report**: Manual review scores on readability, consistency, naturalness.

**Minimum evidence bar per stage:**

| Stage | Regression | Benchmark | Quality Report |
|---|---|---|---|
| RM-5.0 | N/A (Baseline) | N/A | N/A |
| RM-5.1 | Required | Optional | Required |
| RM-5.2 | Required | Required | Required |
| RM-5.3 | Required | Required | Required |
| RM-5.4 | Required | Required | Required |

**Decision gates:**
- Quality went down? → Reject.
- Quality unchanged + regressions? → Reject.
- Quality improved + regressions pass? → Accept.

---

## Principle 5 — Incremental Delivery

> Each RM-5.x stage must be self-contained, verifiable, and deployable independently.

**Stage structure:**
1. Goal statement (linked to one or more Design Principles)
2. Implementation (code/configuration changes)
3. Evidence (regression, benchmark, quality report)
4. Validation (tests pass, ntpe_validate.py all pass)
5. Report

**No stage may span more than one pipeline domain.**
Example: Context optimization + Memory optimization → must be separate stages.

---

## Design Principle Summary

| # | Principle | Decision Rule |
|---|---|---|
| 1 | Translation Quality First | Quality improvement must be demonstrable |
| 2 | Architecture Simplicity | No duplication, no dead code, no wrapper bloat |
| 3 | Frozen Compatibility | RM-4 Freeze is absolute |
| 4 | Evidence Driven | Must provide regression + benchmark + quality data |
| 5 | Incremental Delivery | One pipeline improvement per stage |

---

**This document is the single source of truth for RM-5 design decisions.**
All RM-5.x uptake stage proposals must reference this document.