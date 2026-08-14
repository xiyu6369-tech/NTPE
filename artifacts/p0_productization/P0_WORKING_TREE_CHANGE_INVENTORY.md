# P0 Working-Tree Change Inventory

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b  
**Branch**: main (HEAD == origin/main ��)

---

## Classification Summary

| Category | Count |
|----------|-------|
| P0_TARGET | 0 |
| PRE_EXISTING_MODIFICATION | 18 |
| PRE_EXISTING_UNTRACKED | 22 |
| PROTECTED | 0 |
| UNKNOWN | 0 |

---

## A. P0_TARGET

**No files currently classified as P0_TARGET.**  
P0 implementation has not been authorized. This category is reserved for files that will be created/modified during P0 Productization implementation.

---

## B. PRE_EXISTING_MODIFICATION (18 files)

These are tracked files with modifications in the working tree. They existed before this Stage 0 preflight and are NOT part of P0 scope.

### Deleted Files (4)
| File | Status | Notes |
|------|--------|-------|
| RM_6_4_0_ACCEPTANCE_REPORT.md | Deleted | Legacy acceptance report |
| RM_7_3_1_ACCEPTANCE_REPORT.md | Deleted | Legacy acceptance report |
| scripts/check_prod_imports.py | Deleted | One-shot validation script |
| tools/one_shots/fix_char_rules.py | Deleted | One-shot tool |
| tools/one_shots/fix_narrative.py | Deleted | One-shot tool |

### Modified Files (13)
| File | Status | Notes |
|------|--------|-------|
| artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json | Modified | Canary artifact (CRLF warning) |
| artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json | Modified | Canary artifact (CRLF warning) |
| docs/governance/rm6/RM_6_4_3_CANARY_REPORT.md | Modified | Canary report (CRLF warning) |
| tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json | Modified | Test output (CRLF warning) |
| tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json | Modified | Test output (CRLF warning) |
| tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json | Modified | Test output (CRLF warning) |
| tests/literary/outputs/Regression_History.json | Modified | Test output (CRLF warning) |
| tests/literary/outputs/Regression_History.md | Modified | Test output (CRLF warning) |
| tests/unit/prompt_runtime/test_builder.py | Modified | Unit test |
| tests/unit/prompt_runtime/test_models.py | Modified | Unit test |
| tests/unit/prompt_runtime/test_sections.py | Modified | Unit test |
| tools/canary/run_canary.py | Modified | Canary runner |

---

## C. PRE_EXISTING_UNTRACKED (22 files)

These are untracked files in the working tree. They existed before this Stage 0 preflight and are NOT part of P0 scope.

### RM-7 Entity Canary Artifacts (7)
| File | Type |
|------|------|
| artifacts/rm7_entity_canary/RM_7_3_1_CANARY_REPORT.md | Report |
| artifacts/rm7_entity_canary/consistency_report.json | Data |
| artifacts/rm7_entity_canary/entity_resolution.json | Data |
| artifacts/rm7_entity_canary/legacy/novel_sample_live_progress.json | Artifact |
| artifacts/rm7_entity_canary/normalized_prompt.json | Data |
| artifacts/rm7_entity_canary/runtime/novel_sample_live_progress.json | Artifact |
| artifacts/rm7_entity_canary/translation_request.json | Data |

### RM-8.5 Audit Artifacts (5)
| File | Type |
|------|------|
| artifacts/rm8_5_audit/RM_8_5_CONSISTENCY_AUDIT_REPORT.md | Report |
| artifacts/rm8_5_audit/RM_8_5_LEGACY_CURRENT_CONTRACT_RECONCILIATION_INVENTORY.md | Report |
| artifacts/rm8_5_audit/RM_8_5_PHASE2_REQUIREMENTS_ARCHITECTURE_INVENTORY.md | Report |
| artifacts/rm8_5_audit/RM_8_5_Phase_1_Re-Implementation_Report.md | Report |
| artifacts/rm8_5_audit/RM_8_5_REQUIREMENTS_ARCHITECTURE_INVENTORY.md | Report |

### New Core Implementation (2)
| File | Type |
|------|------|
| core/translation_runtime/boundary_detector.py | Source |
| tests/unit/translation_runtime/test_boundary_detector.py | Test |

### RM-8 Governance Documents (7)
| File | Type |
|------|------|
| docs/governance/rm8/RM_8_2_IMPLEMENTATION_SPECIFICATION.md | Spec |
| docs/governance/rm8/RM_8_2_PREFLIGHT_REPORT.md | Report |
| docs/governance/rm8/RM_8_2_PRE_IMPLEMENTATION_AUDIT.md | Report |
| docs/governance/rm8/RM_8_2_SPEC_REVIEW_AUDIT.md | Report |
| docs/governance/rm8/RM_8_3_IMPLEMENTATION_SPECIFICATION.md | Spec |
| docs/governance/rm8/RM_8_3_PREFLIGHT_REPORT.md | Report |
| docs/governance/rm8/RM_8_5_IMPLEMENTATION_SPECIFICATION.md | Spec |
| docs/governance/rm8/RM_8_5_SPEC_CONSISTENCY_AUDIT.md | Report |

### Knowledge Directory (1)
| File | Type |
|------|------|
| knowledge/learning/candidates.json | Data |
| knowledge/learning/characters.json | Data |

---

## D. PROTECTED (0 files)

No files explicitly marked as PROTECTED in this inventory.  
Protection status will be determined during contract verification phases.

---

## E. UNKNOWN (0 files)

All files have been classified. No UNKNOWN entries.

---

## Notes

1. **CRLF Warnings**: Multiple modified files show CRLF/LF line ending warnings. These are likely git config related and not semantic changes.
2. **Test Output Modifications**: Several test output files under `tests/literary/outputs/` are modified - these appear to be test result artifacts, not source code.
3. **Canary Artifacts**: Files under `artifacts/rm6_canary/` and `artifacts/rm7_entity_canary/` are canary/test run outputs.
4. **Governance Documents**: The RM-8 governance documents are pre-existing specification work, not P0 implementation.
5. **One-shot Tools Deleted**: Three files in `tools/one_shots/` and `scripts/` were deleted - these align with the root policy prohibition on one-shot tools in root directory.

---

## Next Steps

Proceed to runtime contract verification (Section 5 of Stage 0 spec).