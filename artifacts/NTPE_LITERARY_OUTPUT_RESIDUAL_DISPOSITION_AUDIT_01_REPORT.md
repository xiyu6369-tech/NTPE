# NTPE Literary Output Residual Disposition Audit 01

**Task**: `NTPE-LITERARY-RESIDUAL-AUDIT-01`
**Date**: 2026-10-01
**Executor**: Kilo (Automated, read-only audit)
**Status**: `NTPE_LITERARY_OUTPUT_RESIDUAL_DISPOSITION_AUDIT_ACCEPTED`
**Mode**: Read-only. No Git mutation, no file modification of audited paths.

---

## 1. Repository State

| Metric | Value |
|--------|-------|
| Baseline HEAD | `5ce13bad604b86c1487c0739f5bae3006957eb43` |
| Actual HEAD | `5ce13bad604b86c1487c0739f5bae3006957eb43` |
| origin/main | `5ce13bad604b86c1487c0739f5bae3006957eb43` |
| Branch | `main` |
| Ahead / Behind / Divergence | 0 / 0 / 0 |
| HEAD == origin/main | YES |

---

## 2. Current Working Tree

`git status --short`:

```text
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_WORKING_TREE_RESIDUAL_CLEANUP_FINAL_REPORT.md
```

`git diff --stat`:

```text
 tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json |  2 +-
 tests/literary/outputs/PS-03/README.md                                | 13 -------------
 tests/literary/outputs/Regression_History.json                        | 18 +++++++++---------
 tests/literary/outputs/Regression_History.md                          |  2 +-
 4 files changed, 11 insertions(+), 24 deletions(-)
```

### 2.1 Fifth path disclosure (not a literary residual)

`artifacts/NTPE_WORKING_TREE_RESIDUAL_CLEANUP_FINAL_REPORT.md` (`??`) is **untracked** and
was created by the prior task `NTPE-WT-CLEANUP-01` (recorded in that report's own header;
mtime 2026-10-01 17:26, after HEAD commit time 17:17). It is a governance report artifact
under `artifacts/`, not a literary output, and its provenance is fully known. It is **not**
counted among the 4 literary residuals. This is **not** the §18 STOP condition "new residual
file appears" (it is not new and provenance is not unknown); §18 "unknown provenance" does not
apply. It is recorded here for transparency and excluded from the literary accounting.

---

## 3. Producer Evidence (shared root cause)

All three tracked *modified/regenerated* artifacts are outputs of `ntpe_literary_evaluation.py`:

- `ntpe_literary_evaluation.py:28-32` defines `REPORT_JSON`, `REPORT_MD`, `DIFF_MD`, `HISTORY_JSON`, `HISTORY_MD`.
- `evaluate_stage_outputs()` (`:257-286`) writes the per-stage report JSON/MD and calls `_update_history()`.
- `_update_history()` (`:323-347`) rewrites `Regression_History.json` and `Regression_History.md` from accumulated records.

The deleted README's cause is `ntpe_literary_regression.py:132-139`:

```python
output_base = base / "outputs" / stage_name
if output_base.exists() and options.overwrite:
    shutil.rmtree(output_base)
```

Running `regression --stage PS-03 --overwrite` deterministically `rmtree`s
`tests/literary/outputs/PS-03/`, deleting the tracked `README.md`. `_copy_reference_files()`
(`:125-129`) only copies `README.md` into *test-set* subdirectories, never the stage archive
README, so the deletion is never repaired.

Additional structural fact: `.gitignore:132` ignores `tests/literary/outputs/`. These files
remain tracked only because they were committed historically (e.g. `9b38d54`, 2026-07-07).

---

## 4. File 1 — `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json`

- **Exact path**: `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json`
- **Git state**: `M` (modified, unstaged)
- **Provenance**: Introduced with the PS-03 corpus evaluation engine (`9b38d54`),
  regenerated many times. Producer: `ntpe_literary_evaluation.py`.
- **Current diff summary**: Exactly one line changed —
  `"created_at": "2026-08-28T01:44:41"` → `"2026-10-01T12:55:19"`.
  All metrics, scores (`overall_score: 78.0`, status `warning`), and `raw` counters are unchanged.
- **HEAD version**: A valid `1.2-translation-engine-refactor-v1` PS-03-integration report with
  the same records/scores and the older timestamp.
- **Answers**: (1) HEAD = same report, older timestamp. (2) Worktree = same report, new timestamp.
  (3) Cause = regeneration side-effect setting `now_iso()`. (4) Yes, generated output.
  (5) No — S7 declared literary quality `OBSERVATIONAL_ONLY` (`NTPE_S7_07_LITERARY_QUALITY_CONTRACT_V1.md:136,142,156,161`;
  `NTPE_S7_02/03`). (6) Fully reproducible. (7) No references except the producer.
  (8) No meaningful information lost by leaving it.
- **Sensitive-data scan**: no human ratings, no external reference corpus, no S7 calibration
  results, no provider/real translation output. Contains only proxy metric scores and
  character-count `raw` values. `human evaluation = NONE`, `external corpus = NONE`.
- **Disposition**: **KEEP-UNCOMMITTED**
- **Rationale**: Pre-existing, non-canonical, harmless trivial-timestamp regeneration of a
  gitignored generated artifact. Not authoritative enough to commit (pure timestamp churn),
  not worth preserving as new Git history, but should not be discarded.

---

## 5. File 2 — `tests/literary/outputs/PS-03/README.md`

- **Exact path**: `tests/literary/outputs/PS-03/README.md`
- **Git state**: `D` (deleted in working tree, unstaged; still present in HEAD)
- **Provenance**: Introduced in `9b38d54` (2026-07-07). Only tracked file in the PS-03 output
  directory (`git ls-files`).
- **HEAD content** (13 lines): a "PS-03 Output Archive" note with two `launcher_translate.py`
  commands (`regression --stage PS-03 --profile literary`, `evaluate --stage PS-03`).
- **Deletion cause**: Deterministic `shutil.rmtree(output_base)` side-effect during a PS-03
  regression overwrite run (`ntpe_literary_regression.py:138-139`). Not an intentional
  deletion commit — no deletion commit exists in history.
- **Answers**: (1) Deleted by output-directory overwrite. (2) Yes, pre-existing (documented in
  S5/S6/S7 reports since `NTPE_REPOSITORY_COMMIT_BOUNDARY_AUDIT_01_REPORT.md`). (3) Not
  referenced by any test, doc, or runtime code (`git grep "PS-03/README"` matches only
  historical audit/report artifacts). (4) Superseded by the canonical, superior
  `tests/literary/README.md` (canonical corpus description + recommended commands). (5)
  Restoring would reintroduce instructions the regression workflow deletes again on the next
  overwrite run and that duplicate the superseding README. (6) Deletion loses no unique
  historical context — the exact content is preserved in HEAD and catalogued with a sha256 in
  `archive/historical/audits/architecture_consolidation/ARTIFACT_RETENTION_INVENTORY_003B.json`.
- **Disposition**: **KEEP-UNCOMMITTED**
- **Rationale**: The deletion is an accidental workflow side-effect (which argues against
  accepting it), but the file is non-canonical, unreferenced, fully superseded, and fully
  recoverable from HEAD — so restoring it yields no benefit and reintroduces obsolete content.
  Kept as a known pre-existing residual rather than committed or restored. Not `RESTORE-CANDIDATE`
  (restore reintroduces superseded, self-deleting instructions); not `REMOVE-CANDIDATE`
  (deletion is not to be committed in this phase).

---

## 6. File 3 — `tests/literary/outputs/Regression_History.json`

- **Exact path**: `tests/literary/outputs/Regression_History.json`
- **Git state**: `M` (modified, unstaged)
- **Provenance**: Generated accumulator produced by `_update_history()`
  (`ntpe_literary_evaluation.py:323-347`); introduced with the PS-03 engine (`9b38d54`),
  rewritten by every evaluation run.
- **Current diff summary**: The `PS-03` record is moved (re-sorted) to a new
  `created_at: 2026-09-26T03:21:15` position, and the `PS-02-integration` and
  `PS-03-integration` `created_at` timestamps update to `2026-10-01T12:55`. Record count
  unchanged at 54 (HEAD also 54).
- **Answers**: (1) Producer = `ntpe_literary_evaluation.py`. (2) Schema = `{records:[{stage,
  created_at,status,overall_score,report_md}]}`. (3) Timestamps only, plus re-sort.
  (4) No stage references to S7 methodology. (5) Does not duplicately contain canonical
  committed evidence; it is bookkeeping indexed by stage. (6) Generated. (7) Values
  reproducible by re-running evaluations. (8) The worktree delta adds no record beyond HEAD —
  no unique historical evidence in the change itself. 53/54 referenced report paths exist; it
  remains the aggregating index for historical stage results.
- **Disposition**: **KEEP-UNCOMMITTED**
- **Rationale**: Generated, reproducible regression bookkeeping with no references beyond its
  producer. The worktree change is trivial (timestamp churn / re-sort) and adds no information
  over HEAD. It is not promoted to `REMOVE-CANDIDATE` because it functions as the sole
  historical aggregator for stage results and could carry unique historical evidence for
  stages whose directories no longer exist; Quality-First rule prefers preservation. Not
  committed (no authoritative new content).

---

## 7. File 4 — `tests/literary/outputs/Regression_History.md`

- **Exact path**: `tests/literary/outputs/Regression_History.md`
- **Git state**: `M` (modified, unstaged)
- **Provenance**: Rendered view written alongside the JSON by `_update_history()`
  (`ntpe_literary_evaluation.py:344-347`); same origin.
- **Current diff summary**: The single `| PS-03 | 0.0 | failed | ... |` table row is moved to
  its re-sorted position. No score/status values change. File has no trailing newline.
- **Answers**: (1) Producer = `ntpe_literary_evaluation.py`. (2) Markdown table of the JSON
  records. (3) Row reorder only. (4) No S7 references. (5) Mirrors committed content
  (duplicate of the JSON view). (6) Generated. (7) Reproducible. (8) No unique historical
  evidence lost.
- **Disposition**: **KEEP-UNCOMMITTED**
- **Rationale**: Pure generated rendering of File 3 with identical disposition and reasoning.

---

## 8. Cross-Reference Audit

| Path | References found | Classification |
|------|------------------|----------------|
| `Literary_Quality_Report.json` | Producer constant only (`ntpe_literary_evaluation.py:28`); data entries in gitignored `tests/literary/outputs/` | Producer output; no dead external reference |
| `tests/literary/outputs/PS-03/README.md` | Only historical audit/report artifacts + `ARTIFACT_RETENTION_INVENTORY_003B.json` catalog entry | Historical reference; no runtime/test/doc dependency |
| `Regression_History.json` | Producer constant (`ntpe_literary_evaluation.py:31`); historical audit artifacts | Producer output |
| `Regression_History.md` | Producer constant (`ntpe_literary_evaluation.py:32`); historical audit artifacts | Producer output |

No runtime dependency. No test dependency. No live documentation reference. No dead
code reference. All references are producer-internal or historical governance artifacts.

---

## 9. Duplicate / Canonical Role

- Canonical S7 literary-quality evidence lives in `artifacts/NTPE_S7_07_*`,
  `NTPE_S7_08_*`, `NTPE_S7_12_*` … `NTPE_S7_15_*`, and the S5/S6 closure reports. These
  declare the PS-03 evaluation **OBSERVATIONAL_ONLY** tooling, not a production gate.
- The four residuals are **not** canonical evidence and do **not** supersede any S7 evidence.
  Conversely, S7 evidence does not supersede them; they are simply non-canonical observational
  test artifacts.
- No duplicate is being mistaken for canonical evidence, and no unique historical datum is
  being discarded.

---

## 10. Accounting

```text
4 literary files total

KEEP-UNCOMMITTED    = 4
COMMIT-CANDIDATE    = 0
RESTORE-CANDIDATE   = 0
ARCHIVE-CANDIDATE   = 0
REMOVE-CANDIDATE    = 0

UNKNOWN             = 0
```

Sum = 4. ✓

---

## 11. Final State

```text
S5/S6/S7 History:    INTACT
Remote:              SYNCED (HEAD == origin/main == 5ce13ba)
Files Modified By Audit: NONE (audited paths untouched)
Delete:              NO
Restore:             NO
Archive/Move:        NO
Stage:               NO
Commit:              NO
Push:                NO
Tag:                 NO
Root Hygiene:        PASS (report written under artifacts/)
```

The fifth untracked path (`artifacts/NTPE_WORKING_TREE_RESIDUAL_CLEANUP_FINAL_REPORT.md`) is a
prior-task governance artifact, disclosed and excluded from the literary accounting.

---

## 12. STOP-Condition Review

| Condition | Triggered |
|-----------|-----------|
| New residual file appears | No (untracked path is a known prior-task report, not a literary residual) |
| Unknown provenance | No |
| Human evaluation data discovered | No |
| External reference corpus discovered | No |
| Real translation output unexpectedly discovered | No (only proxy scores/char counts) |
| Canonical evidence would be lost | No |
| Dirty file required by production/test | No |
| S5/S6/S7 history affected | No |
| Remote divergence | No |

---

**Result**: `NTPE_LITERARY_OUTPUT_RESIDUAL_DISPOSITION_AUDIT_ACCEPTED`
