# NTPE S13-04 — QA Consolidation Decision

Baseline HEAD `e08c1dc`. Decision-support only; no implementation.
Evidence: `artifacts/NTPE_S13_04_QA_GUARD_AUDIT.md`, `artifacts/NTPE_S13_04_QA_GUARD_INVENTORY.md`.

## Decision

**Decision A — Bounded consolidation.**

Rationale: there is concrete, zero-caller evidence of dead QA code (no production caller
and no test caller) and two unused imports on canonical files. A minimal, deletion-only
consolidation is justified and carries no behaviour change. Duplicate-*detection*
unification is explicitly **deferred** because the overlap is format-specific
(EPUB `BasicTranslationQA` vs TXT `runtime_qa`) and merging it would change a CLOSED
output contract. No item qualifies as Decision C: QA is advisory and causes no erroneous
reader-facing behaviour.

## A.1 Current paths (to be consolidated / kept)

```text
KEEP (canonical, unchanged)
  core/translation_runtime/runtime_qa.py        analyze_runtime_quality, RuntimeQAPolicy
  lts/txt_translation_runtime.py:1388           analyze_translation_quality (compat wrapper)
  core/translation_engine/basic_qa.py           BasicTranslationQA (EPUB carries result)
  core/translation_quality_v5/*                 unified gate (advisory)
  core/translation_discipline/*                 discipline orchestration
  core/translation_naturalness/*                post-process (not a gate)

CONSOLIDATE / REMOVE (dead-only)
  core/validator.py                             Validator               (DEAD)
  core/translation_runtime/runtime_qa.py:287    should_soft_fail_naturalness   (DEAD)
  core/translation_runtime/runtime_qa.py:306    soft_fail_naturalness_report   (DEAD)
  lts/txt_translation_runtime.py:1742           has_retry_worthy_naturalness_issue (DEAD)
  lts/txt_translation_runtime.py:1418           qa_retry_delay_seconds         (DEAD)
  lts/txt_translation_runtime.py:32             unused import soft_fail_naturalness_report
  core/epub_translation/runtime/adapter.py:43   unused import RuntimeQAPolicy, analyze_runtime_quality

DOCUMENT / DECIDE (semantic mismatch, not a merge)
  lts/txt_translation_runtime.py:963-972        orchestrate_runtime_discipline(text=chunk); outcome.text discarded
  lts/txt_translation_runtime.py:128            qa_fail_policy (inert)
```

## A.2 Merged responsibility

```text
C1: no responsibility is merged; only unreachable symbols are removed.
    The single canonical TXT QA entry (analyze_translation_quality -> analyze_runtime_quality)
    and the single EPUB QA entry (BasicTranslationQA via the engine) are preserved as-is.
C2: no merge; a recorded decision is required on how the discipline call intends to behave
    (apply repair to the translation, or declare the invocation diagnostic-only).
```

## A.3 Files affected (proposed future task, not this audit)

```text
core/validator.py                                   (delete/archive)
core/translation_runtime/runtime_qa.py              (remove 2 dead functions)
lts/txt_translation_runtime.py                      (remove 2 dead functions + 1 unused import)
core/epub_translation/runtime/adapter.py            (remove 1 unused import)
**tests asserting removed symbols**                 (only if they assert the removed contract)
```

## A.4 Behavior preserved

- `analyze_runtime_quality` detection logic, thresholds, severities, issue codes: unchanged.
- `BasicTranslationQA` output and EPUB `qa_report` propagation: unchanged.
- `quality_v5` unified report and discipline metadata: unchanged.
- All CLOSED contracts (glossary precedence/hash, EPUB ordering/non-linear, offset, output
  existence gate, recovery eligibility, provider/runtime route): untouched — QA is
  advisory and not referenced by any of them.
- Removing dead symbols changes only code that is never executed.

## A.5 Public / internal API impact

- Removed symbols are not exported by `core/translation_runtime/__init__.py` (`__all__`
  excludes `soft_fail_naturalness_report`), are not importable from any production module,
  and have zero callers. No public API surface changes.
- `qa_fail_policy` and `build_qa_retry_user_prompt` are **not** removed by C1 (still
  referenced by CLI/UI options and legacy tests); C2 records them as inert/legacy for a
  separate decision.
- `core/validator.py` has zero importers; deleting it removes no importable contract in use.

## A.6 Test impact

- `tests/runtime/translation_runtime_provider_qa_test.py` unaffected (10 passed).
- `tests/lts_stage_04/test_translation_qa.py` already fails (2 obsolete QA-enforcement
  assertions). Per governance, these are **not** to be "fixed" by restoring enforcement;
  the future task may remove/archive only those obsolete assertions, never change
  production semantics to satisfy them.
- No canonical contract/e2e/reader_project assertion references the removed symbols.

## A.7 Rollback strategy

- Deletion-only change on zero-caller symbols; rollback is a single `git revert` of the
  future commit. No data, schema, or persisted-state migration is involved.

## A.8 Out of scope (explicitly deferred)

```text
DEFERRED D1: unify BasicTranslationQA <-> runtime_qa detection.
             Format-specific; would change EPUB output contract. Requires its own audit.
DEFERRED D2: legacy archive program for core/quality (Stage-15), engine/,
             core/translator.py, core/expansion/.
             Large surface; "REMOVE NOT AUTHORIZED" per S12-08. Separate workstream.
DEFERRED D3: TIC offline quality gate, knowledge_validation, SDK TranslationValidator.
             Not on the reader-first path.
```

## A.9 Governance compliance

```text
No second QA pipeline created            : yes
No CLOSED capability redefined           : yes
No canonical runtime modification (this audit) : yes (0 files changed)
No test modification (this audit)        : yes (0 files changed)
Audit-first, evidence-based              : yes
Artifacts limited to artifacts/          : yes
Scratch tools created                    : none
Provider / Network / Real Translation    : 0 / 0 / 0
```

## A.10 Recommendation

Proceed to a future, separately authorized **bounded** consolidation scoped to C1
(dead QA code + unused imports) with rollback = revert, and resolve C2 with a recorded
design decision (wire the discipline repair or mark it diagnostic). Do **not** fold in
D1-D3.

**Result: Decision A — Bounded consolidation (dead QA code only).**
