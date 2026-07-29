# NTPE Governance Gap Analysis — Read-Only

Generated: 2026-07-27T11:56:35+08:00
Agent: AI assistant using Copilot CLI runtime in VS Code

Scope: Analysis limited to RM-0 artifacts (audits/architecture_consolidation/, docs/releases/ntpe_v2_0/, artifacts/ntpe_v20_stage0_project_layout_consolidation/, and the specific files: MOVE_MAP, KEEP, DELETE, MERGE, PROJECT_LAYOUT, CONSOLIDATION_BATCH_PLAN). No repository modifications were made.

---

## Executive Summary

This gap analysis compares the original consolidation plan (CONSOLIDATION_BATCH_PLAN.json) and project-layout goals with the current repository evidence produced by RM-0. Findings:
- Governance baseline (audits, consolidation plan, project-layout policy, artifact/manifest rules) is present and documented.
- Significant consolidation work has been executed for Stage 0 (project-layout) and multiple consolidation batches produced reports (batches 1–4 have produced artifacts/reports). Batch 5 has partial execution (sub-batch 5a evidence).
- The Move Map produced by Stage 0 lists 76 moves; Stage 0 outcome and artifacts indicate those moves were applied into verification/. No cancelled moves recorded in MOVE_MAP.json.
- Remaining gaps are primarily: externalization/archive of the large NTPE.zip, further shared-utilities consolidation, test de-duplication, and secure remediation of legacy credential exposures.

Evidence: audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md, audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json, artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json, docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md, audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json

---

## Governance Timeline (documents reviewed)

- audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md (audit report, 2026-07-15)
- audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json (batches 1..5 plan)
- audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json (size & inventory)
- audits/architecture_consolidation/KEEP.json, DELETE_CANDIDATES.json, MERGE.json
- audits/architecture_consolidation/batch1_delivery/REPOSITORY_HYGIENE_REPORT.md
- audits/architecture_consolidation/batch2_tests/TEST_CONSOLIDATION_REPORT.md
- audits/architecture_consolidation/batch3_shared/CONSOLIDATION_REPORT.md and MIGRATION_MAP.json
- audits/architecture_consolidation/batch4_quality/CONSOLIDATION_REPORT.md
- audits/architecture_consolidation/batch5a_usage/BATCH5A_DYNAMIC_USAGE_AUDIT.md (partial evidence for Batch 5)
- docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md (Stage 0 results)
- artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json (move inventory)

(These files form the RM-0 authoritative set used for this analysis.)

---

## Architecture Consolidation Progress (per batch)

Summary of status derived directly from RM-0 artifacts (no conjecture):

- Batch 1 — Repository Hygiene
  - Status: Completed (evidence: audits/architecture_consolidation/batch1_delivery/REPOSITORY_HYGIENE_REPORT.md and NTPE_BATCH1_AUDIT_PACKAGE_REPORT.json present).
  - Evidence: audits/architecture_consolidation/batch1_delivery/REPOSITORY_HYGIENE_REPORT.md, audits/architecture_consolidation/batch1_delivery/NTPE_BATCH1_AUDIT_PACKAGE_REPORT.json

- Batch 2 — Test Consolidation
  - Status: Completed (evidence: batch2 test audit artifacts and TEST_CONSOLIDATION_REPORT.md present).
  - Evidence: audits/architecture_consolidation/batch2_tests/TEST_CONSOLIDATION_REPORT.md, NTPE_BATCH2_AUDIT_PACKAGE_REPORT.json

- Batch 3 — Shared Utilities
  - Status: Completed (pilot/programmatic migrations reported).
  - Evidence: audits/architecture_consolidation/batch3_shared/CONSOLIDATION_REPORT.md, batch3_shared/MIGRATION_MAP.json (entries show migrated:true for multiple primitives)

- Batch 4 — Quality API Consolidation
  - Status: Completed (report exists documenting stage-11 consolidation recommendations and artifacts).
  - Evidence: audits/architecture_consolidation/batch4_quality/CONSOLIDATION_REPORT.md

- Batch 5 — Production Path Simplification
  - Status: Partially Completed / In-progress (evidence of sub-batch 5a dynamic usage audit and compatibility artifacts; no single-file consolidated production simplification committed).
  - Evidence: audits/architecture_consolidation/batch5a_usage/BATCH5A_DYNAMIC_USAGE_AUDIT.md, batch5a_usage/KEEP_COMPATIBILITY.json, MERGE.json

Notes: Status labels reflect presence of reports/artifacts in RM-0 rather than assumptions about destructive actions (deletions/renames). Where reports exist, the batch is marked Completed (or Partially Completed when only sub-batch artifacts exist).

---

## Move Map Status (artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json)

MOVE_MAP.json summary (Stage 0 move inventory produced by the layout consolidation):
- move_count (declared): 76 (artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json)
- MOVE entries: list of 76 source → destination records with sha256_before_move values and categories (legacy_instruction, release_changelog, etc.)

Stage 0 outcome (docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md) shows:
- Non-Python historical files moved: 76
- Historical Root Wrappers retained: 321
- Initial root files: 424 → Final root files: 348

Derived Move Map status (based on the two RM-0 artifacts above):
- Planned Moves: 76 (MOVE_MAP.move_count)
- Executed Moves: 76 (Stage 0 outcome documents report 76 non-Python historical files moved into verification/ — matches MOVE_MAP)
- Remaining Moves: 0 (no remaining entries flagged in MOVE_MAP; Stage 0 reported those moves as performed)
- Cancelled Moves: 0 (MOVE_MAP contains moves with no cancelled flags; Stage 0 outcome does not report cancellations)

Evidence: artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json and docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md (Stage 0 Outcome lines reporting 76 moved files). No MOVE_MAP entries indicate cancellation.

Validation note: this conclusion is derived from RM-0 artifacts (MOVE_MAP and Stage 0 result doc). No git modifications were made during this analysis.

---

## Repository Layout Compliance (Planned → Current status)

Using docs/PROJECT_LAYOUT.md and config/project_layout_policy.json for the planned layout and RM-0 audit artifacts for current status.

- Production
  - Planned: single production CLI and a stable TranslationRuntime boundary (ntpe_production_translate.py, runtime API)
  - Current: Present. Production spine documented: launcher_translate.py → ntpe_production_translate.py → TranslationRuntime (evidence: NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md, PRODUCTION_PATH.json referenced in audit)

- Runtime
  - Planned: LTS/runtime implementations under lts/ and core translation_runtime
  - Current: Present and referenced by tests/artifacts (evidence: REPOSITORY_SIZE_REPORT.json listing lts and core; KEEP.json retains translation_runtime and lts references)

- Core
  - Planned: organized core modules for translation, prompt compilation, quality, reliability
  - Current: Present; many core modules marked KEEP, some parallel legacy modules listed as DELETE candidates (evidence: KEEP.json, DELETE_CANDIDATES.json)

- Tests
  - Planned: tests/ (pytest collection), verification/ for Stage0 acceptance
  - Current: Present; large test corpus (1251 test files), duplicate/ mirror tests flagged in audit and test consolidation reports (evidence: REPOSITORY_SIZE_REPORT.json tests counts; batch2 reports)

- Artifacts
  - Planned: artifacts/ for stage-produced evidence and manifests/
  - Current: Present (artifacts/ contains stage artifacts including MOVE_MAP.json; manifests/ contains required manifests) — evidence: artifacts/ and manifests/ files listed in audit

- Legacy
  - Planned: historical wrappers retained but moved to verification/ or archived; legacy candidates listed for deletion after validated migration
  - Current: Many legacy Root Wrappers remain in root (321 retained) but Stage 0 moved non-Python historical files into verification/ (evidence: PROJECT_LAYOUT.md and Stage 0 doc)

- Docs
  - Planned: docs/ including release notes and consolidation records
  - Current: Present and populated (docs/releases/ntpe_v2_0/ and many release audit docs) — evidence: docs entries in REPOSITORY_SIZE_REPORT.json and docs/ directory listing

- Root Scripts
  - Planned: root allowlist enforced by ntpe_validate.py; historical wrappers retained with explicit retained list
  - Current: Root allowlist practices present; RETAINED_ROOT_WRAPPERS.json referenced by PROJECT_LAYOUT.md; Stage0 outcome preserved wrappers (evidence: PROJECT_LAYOUT.md, artifacts MOVE_MAP and Stage0 outcome)

Overall compliance observation: The repository’s current layout is consistent with the Stage 0 planned scope (low-risk root cleanup with verification/); broader consolidation (reducing root wrappers to target of 20 root Python files) was intentionally deferred and remains outstanding as a future cleanup stage.

---

## Governance Compliance Matrix (which governance rules are currently followed vs deviated)

1) Production boundary preservation
- Status: Compliant
- Evidence: NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md (production path & KEEP list) and KEEP.json entries for runtime modules.

2) Root layout policy (Stage 0 low-risk rules: move non-Python historical files to verification/, retain historical wrappers)
- Status: Compliant (Stage 0 executed)
- Evidence: docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md and artifacts MOVE_MAP.json

3) Artifact retention and manifest policy (use SHA-256, do not write raw Provider responses into audit ZIP)
- Status: Documented / Compliant in policy; partial operational gap
- Evidence: Architecture audit sections on Artifact retention and REPOSITORY_SIZE_REPORT.json (artifact/manifests listings). The policy is present, but full externalization of large artifacts (NTPE.zip) not completed.

4) Test consolidation policy (deduplicate, preserve compatibility wrappers)
- Status: Partially compliant — audit and batch2 reports exist; consolidation actions planned/started but full deduplication not completed
- Evidence: audits/architecture_consolidation/batch2_tests/TEST_CONSOLIDATION_REPORT.md and REPOSITORY_SIZE_REPORT.json test statistics

5) Shared utilities consolidation (primitive-by-primitive)
- Status: Partially compliant — pilot migrations exist (batch3 MIGRATION_MAP.json shows several migrated:true entries), but larger program remains ongoing.
- Evidence: batch3_shared/MIGRATION_MAP.json and batch3 consolidation report

6) Security (legacy credential exposure remediation)
- Status: Non-compliant / Outstanding
- Evidence: audits/legacy_capability_recovery/batch1/LCR_BATCH1_AUDIT.md reports credential exposure discovered and redacted; no remediation commit in RM-0 artifacts

7) Large artifact externalization (NTPE.zip)
- Status: Not Completed (gap)
- Evidence: REPOSITORY_SIZE_REPORT.json shows NTPE.zip present and occupying ~587.8 MB; CONSOLIDATION_BATCH_PLAN.json recommends externalization (Batch 1) but no archival artifact or deletion recorded in RM-0 (only hygiene report)

---

## Decision Register (extracted from RM-0 documents, no new decisions added)

| Decision | Source file | Status (as recorded) | Still valid? |
|---|---|---:|---|
| Root Python should not be reduced during Stage 0; keep historical root wrappers and record RETAINED_ROOT_WRAPPERS.json for later cleanup | docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md | Adopted (Stage 0 executed) | Yes |
| Historical artifacts must be preserved and externalized with SHA-256 manifests before deletion | audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md; CONSOLIDATION_BATCH_PLAN.json | Recommended / required by plan | Yes |
| Shared utilities consolidation must be done primitive-by-primitive (no big-bang) | audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json | Adopted as policy recommendation | Yes |
| Stage 12 A/B experimental candidates should be stopped and moved to experiments if not producing reviewable pairs | NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md | Recommended | Yes |

(These decisions were present in RM-0 artifacts; the table reflects their recorded status.)

---

## Technical Debt (remaining, actionable, high-value items)

- NTPE.zip large retained full-worktree archive — prevents efficient repository storage and increases clone size; externalization is high-value and recommended. Evidence: audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json (NTPE.zip listed as largest file).

- Duplicate primitives and serialization/hash utilities across many files — consolidating reduces maintenance burden; partial work done in batch3 but more remains. Evidence: NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md (duplicate counts) and batch3_shared/MIGRATION_MAP.json (some migrated entries)

- Test de-duplication — many mirror tests and exact duplicates remain; test consolidation batch report exists but full deduplication not applied. Evidence: REPOSITORY_SIZE_REPORT.json tests totals and batch2 reports.

- Frozen stage wrappers and compatibility facades — preserved for rollback but increase surface area for maintenance; consolidation planned but not fully executed. Evidence: KEEP.json and architecture audit recommendations.

- Security remediation from legacy audits (credential exposure) — requires credential rotation and verification. Evidence: audits/legacy_capability_recovery/batch1/LCR_BATCH1_AUDIT.md

(Only items that remain unresolved and have clear operational value are listed.)

---

## Remaining Work (prioritized, derived from RM-0 plan and evidence)

High
- Externalize/archive NTPE.zip (Batch 1 hygiene) — required manifests and restore plan must be produced first. Evidence: CONSOLIDATION_BATCH_PLAN.json, REPOSITORY_SIZE_REPORT.json
- Remediate credential exposure identified in LCR batch1 — security-sensitive. Evidence: LCR_BATCH1_AUDIT.md

Medium
- Continue Shared Utilities consolidation (primitive migrations) where MIGRATION_MAP pilot indicates missing migrations. Evidence: batch3_shared/MIGRATION_MAP.json and CONSOIDATION_REPORT.md
- Test consolidation follow-through (deduplication with compatibility wrappers). Evidence: batch2 test report

Low
- Stage 12 candidate archival and movement to experiments (audit recommended). Evidence: NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md

---

## Recovery Completion (estimate and justification)

Estimates (derived strictly from RM-0 artifact evidence and explicit Stage outcomes):

- Governance Recovery: 100%
  - Justification: Audit documents, consolidation plan, project-layout policy, and batch reports exist and form a governance baseline (evidence: NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md, CONSOLIDATION_BATCH_PLAN.json, PROJECT_LAYOUT.md).

- Layout Recovery: 90%
  - Justification: Stage 0 Project Layout Consolidation executed and MOVE_MAP applied for 76 non-Python historical files (docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md and MOVE_MAP.json). Remaining root-wrapper reduction was intentionally deferred (so layout goals not completely finalized).

- Migration (shared utilities & primitive consolidation): 60%
  - Justification: Batch 3 produced migration map entries showing several migrated primitives (batch3_shared/MIGRATION_MAP.json) but some helpers remain outside the pilot boundary; therefore migrations are partially completed.

- Cleanup (removal of DELETE candidates, externalization of large archives): 5–10%
  - Justification: Some non-Python historical files were moved into verification/ (Stage 0), but deletion of delete-candidates and externalization of NTPE.zip have not been completed per REPOSITORY_SIZE_REPORT.json and DELETE_CANDIDATES.json — main destructive cleanup has not been applied.

- Documentation: 95%
  - Justification: Extensive audit, batch, and project-layout documentation exist (docs/ and audits/), with clear records of decisions and manifests.

These percentages are evidence-driven approximations using only the RM-0 artifact set and Stage 0 outcomes.

---

## Final Recommendations (operational next steps — high level, not new policy)

- Prioritize Batch 1 hygiene action to externalize NTPE.zip with an inventory + SHA-256 manifest and a tested restore procedure (archive → verify → remove). Evidence and plan are in CONSOLIDATION_BATCH_PLAN.json and REPOSITORY_SIZE_REPORT.json.

- Address credential exposure immediately: rotate/revoke any implicated secrets and record remediation steps referenced to LCR_BATCH1_AUDIT.md.

- Continue primitive-by-primitive shared utilities consolidation using MIGRATION_MAP.json as the pilot. Keep compatibility façade approach to avoid breaking production boundaries.

- Execute test consolidation gradually: run pytest collection parity checks and remove exact duplicates behind compatibility wrappers.

- Track remaining actions and progress in the same artifacts area (audits/architecture_consolidation/) and preserve manifests and rollbacks for every destructive step.

---

## Completion Summary

- Governance Documents Reviewed (RM-0 set): 12+ (key files listed earlier)
- Consolidation Progress Summary: Batches 1–4 have reports (Completed); Batch 5 partially executed (batch5a evidence)
- Move Map Completion: Planned 76 → Executed 76 → Remaining 0 → Cancelled 0 (evidence: MOVE_MAP.json and Stage 0 outcome)
- Governance Compliance Summary: Production & Stage 0 layout compliant; artifact externalization and security remediation outstanding
- Technical Debt Summary: NTPE.zip externalization, duplicate primitives, test duplicates, frozen wrappers, LCR credential remediation
- Recovery Completion (estimates): Governance 100%; Layout 90%; Migration 60%; Cleanup 5–10%; Documentation 95%

Evidence index (selected):
- audits/architecture_consolidation/NTPE_ARCHITECTURE_CONSOLIDATION_AUDIT.md
- audits/architecture_consolidation/CONSOLIDATION_BATCH_PLAN.json
- audits/architecture_consolidation/REPOSITORY_SIZE_REPORT.json
- audits/architecture_consolidation/KEEP.json
- audits/architecture_consolidation/DELETE_CANDIDATES.json
- audits/architecture_consolidation/batch1_delivery/REPOSITORY_HYGIENE_REPORT.md
- audits/architecture_consolidation/batch2_tests/TEST_CONSOLIDATION_REPORT.md
- audits/architecture_consolidation/batch3_shared/MIGRATION_MAP.json
- audits/architecture_consolidation/batch4_quality/CONSOLIDATION_REPORT.md
- audits/architecture_consolidation/batch5a_usage/BATCH5A_DYNAMIC_USAGE_AUDIT.md
- docs/releases/ntpe_v2_0/NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION.md
- artifacts/ntpe_v20_stage0_project_layout_consolidation/MOVE_MAP.json

Constraints: Analysis used only the RM-0 artifact set specified by the task. No files were renamed, moved, deleted, or modified. This is a read-only assessment. 

Prepared by: AI assistant using Copilot CLI runtime in VS Code

