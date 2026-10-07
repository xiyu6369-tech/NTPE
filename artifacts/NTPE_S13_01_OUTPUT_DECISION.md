# NTPE S13-01 — Output Portability & Stale Artifact Decision

Companion to `artifacts/NTPE_S13_01_OUTPUT_PORTABILITY_AUDIT.md`. Decision-support only;
no implementation.

## 1. Decision

**Decision A — keep the current behavior and formally record absolute-path portability as
a DEFERRED limitation, and record the persisted `available` flag as QUALITY DEBT.**

Rationale (evidence-backed):

- Absolute output paths are a **deliberate contract**, not an accident
  (`NTPE_S9_05_COMPLETION_OUTPUT_UX_REPORT.md`: "Output stays Project-owned … No
  CWD-relative path is reintroduced").
- Relocation produces a **truthful, non-destructive** failure state (`結果檔案不存在`),
  never corruption or a fake control.
- The persisted `available` flag is already re-gated by live `is_file()` at derivation
  (`core/reader_project/state.py:71-75`), render
  (`ui/translation_studio/project_view_model.py:69-74`) and action
  (`project_page.py:645-654`), so it cannot cause a reader-facing false positive.
- No current product requirement states that relocating `NTPE_HOME` or the source file
  must preserve output usability. Changing persistence semantics needs a product decision.
- S12-08 already ranked output portability as the top remaining reader-facing **residual**,
  not a blocker; there is no new evidence upgrading it to a correctness gap.

**No production change is recommended for S13-01.** This audit does not implement anything.

## 2. Minimal repair boundary (documented only; NOT implemented)

Provided for a future, explicitly-scoped task **if** the product decides relocation
support is required. This is the smallest boundary consistent with the canonical design;
it introduces no second pipeline and no schema redesign.

```text
Current contract
  OutputRecord.artifact_path / output_dir : absolute persisted references
  TXT output dir : <NTPE_HOME>/output/<project_id>   (project-owned)
  EPUB output dir: <source.parent>/output/epub_translation/<safe id> (source-adjacent)

Failure scenario
  NTPE_HOME (or the source file) is relocated. project.json loads from the new home, but
  the persisted absolute references still point at the old location:
    - UI: status demoted; note 結果檔案不存在 (truthful; already correct)
    - TXT re-run: _txt_output_dir reuses the stale absolute output.output_dir, so output is
      (re)created at the old location instead of the new home.

User-visible impact
  Result cannot be opened/revealed after relocation; a resumed TXT run may write to the old
  location if it is still writable. No corruption; no silent success.

Minimal repair boundary (choose one, product-gated)
  Option 1 (derive-on-read, recommended if supported):
    - Add ONE resolver that, when the persisted absolute path is missing, recomputes the
      expected location from project identity:
        TXT  : store.home / "output" / project_id
        EPUB : epub_output_dir(source.parent, identifier-from-metadata)
      and uses it only for display/open/resume-dir selection.
    - Owner: presentation + a single resolver; no new pipeline; no schema change if the
      recomputed value is not persisted.
  Option 2 (store relative):
    - Persist output paths relative to the store home (schema add).
    - REJECTED as over-scope: requires schema change and touches Recovery.

Persistence impact
  Option 1: none (no new persisted field). Option 2: schema change (out of scope).

Backward-compatibility impact
  Option 1: none — absolute paths remain valid at the original location; resolver only
  activates on missing files.

Recovery impact
  None. Recovery eligibility already keys on source identity + runtime artifact + glossary
  hash (`check_recovery_eligibility`); do not change it.

Test impact
  New regression: relocate the home dir; assert truthful missing state (already) and, if
  Option 1 is adopted, assert the resolver recomputes the expected output path without
  mutating project.json.

Rollback strategy
  Delete the resolver and restore render/action to read the persisted absolute path;
  no data migration to undo (Option 1 adds no persisted state).
```

## 3. `available` stale flag

Recommended (future, optional, low priority): treat `OutputRecord.available` as a
**cache-only** field and never read it as truth (already effectively the case). Removing
the write, or documenting it as advisory, is MAINTENANCE / QUALITY DEBT — **not**
authorized here, and not required for correctness.

## 4. Next-phase recommendation

- Output portability: **do not schedule implementation** unless/until the product decides
  home/source relocation must preserve output usability; then use Option 1 above.
- The re-ranked S13 backlog (from `NTPE_S12_08_PROGRAM_AUDIT.md` §21) remains:
  1. Output portability / stale-artifact refresh (this audit → Decision A: defer)
  2. E2E test-infrastructure reliability
  3. Glossary bounded enhancement (EPUB prompt parity + CSV)
  4. QA guard consolidation
  5. Legacy / orphan archive (split `translation_release` first)
  6. S7 literary calibration (external-blocked)

## 5. Explicit non-goals

No production code, tests, schema, Recovery, Glossary, EPUB spine/TOC/offset, or legacy
changes in this task. Provider / network / real translation = 0.

## 6. Result

```text
Decision : A (keep current behavior; absolute-path portability = DEFERRED;
             persisted available = QUALITY DEBT, fully mitigated)
Blockers : NONE
FINAL    : PASS (audit + decision complete; no implementation)
```
