# NTPE S10-03 F3 Repair — Runtime Artifact Ownership Enforcement

Baseline HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Branch: `main`
Tag: `s9-complete`

Status: REPAIR COMPLETE (no commit / push / tag)

Authoritative contract: `artifacts/NTPE_S9_06_RECOVERY_SOURCE_INTEGRITY_CONTRACT.md` (§3 eligibility predicate, §6 runtime artifact contract, §10 output/runtime separation).

---

## 1. What F3 Was

S10-03's first F3 pass enforced project/source binding when evidence was
*present*, but treated absent evidence as non-blocking (`project_binding_unverified`
→ allow). The S9-06 contract §6 requires ownership to be **provable**:
missing/incomplete evidence is a BLOCK condition.

---

## 2. Fix

`core/reader_project/recovery.py`:

- `validate_project_binding`: the runtime artifact must record the `output_dir`
  it was produced in; that directory must equal the artifact's own location and,
  when the project records an `output_dir`, must match it too. No recorded
  evidence → BLOCK (`missing_project_binding`).
- `validate_source_binding`: the runtime artifact must record `input`; it must
  resolve to the project source. No recorded evidence → BLOCK
  (`missing_source_binding`).

Matrix now:

| Runtime Artifact | Ownership Evidence | Result |
|---|---|---|
| valid | project + source match | ELIGIBLE |
| valid | wrong project (output_dir mismatch) | BLOCK (`artifact`) |
| valid | wrong source (input mismatch) | BLOCK (`artifact`) |
| valid | missing `output_dir` | BLOCK (`missing_project_binding`) |
| valid | missing `input` | BLOCK (`missing_source_binding`) |
| valid | only failed chunks (insufficient) | BLOCK (`artifact`) |
| missing / corrupt | — | BLOCK (`artifact`) |

No new artifact metadata, registry, persistence, or schema. Evidence comes from
fields both real resume writers already emit:
`lts/txt_translation_runtime.py:1965-1966` and
`core/epub_translation/runtime/adapter.py` (`input`, `output_dir`).

---

## 3. Output Independence Preserved

`check_recovery_eligibility` only reads runtime ownership; it does not infer
availability from the output artifact, nor the reverse. The output column in
`ProjectCardModel` is derived independently (`output.artifact_path` + `is_file()`).

---

## 4. last_error Preserved

`check_recovery_eligibility` is pure and never writes `StateRecord.last_error`.
Recovery-blocked-by-ownership does not clear existing errors.

---

## 5. UI Behavior

`build_card_model` sets `recovery_eligible = False` and a non-empty
`recovery_blocked_by`/`recovery_blocked_reason`; `_on_resume` returns before
starting a runner when `get_recovery_blocked_reason` is non-empty. No actionable
Resume control is exposed for unverifiable artifacts.

---

## 6. Tests

New/updated:
- `tests/reader_project/test_recovery.py`
  - `test_valid_runtime_artifact_allows_recovery`
  - `test_unverified_runtime_artifact_blocks_recovery` (core regression case)
  - `test_missing_project_binding_blocks_recovery`
  - `test_missing_source_binding_blocks_recovery`
  - `test_incomplete_runtime_evidence_blocks_recovery`
  - `test_wrong_project_artifact_blocks_recovery`
  - `test_wrong_source_artifact_blocks_recovery`
  - helpers now write the ownership evidence real artifacts contain.
- `tests/e2e/test_s9_07_txt_reader_flow.py`,
  `tests/e2e/test_s9_07_failure_recovery.py`,
  `tests/e2e/test_s10_03_epub_recovery_e2e.py`: eligible recovery fixtures now
  carry `input`/`output_dir` (as the runtime does). Recovery E2E adds the
  unverifiable-artifact expectation implicitly via the strict rule.

Semantics preserved: wrong-project/wrong-source/changed-source/missing-source/
missing-artifact blocking; Normal Translation ≠ Recovery.

---

## 7. Validation Evidence (single runs)

```
tests/e2e                                  45 passed
tests/reader_project                       68 passed
combined regression                        527 passed, 1 skipped
```

F2 preserved: the URN-identifier journey and
`test_e2e_identifier_yields_filesystem_safe_output_dir` pass.

---

## 8. Boundaries

- Frozen runtime untouched (TXT/EPUB writers unchanged).
- No schema change (ReaderProject v1).
- No second persistence / artifact registry.
- Provider = 0, Network = 0, Real translation = 0.
- Glossary untouched. Root hygiene PASS.
