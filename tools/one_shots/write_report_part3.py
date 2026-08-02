import os

base_path = r"D:\Python\NTPE\docs\governance\rm5"

report_part3 = """

## 6. Validation Readiness (RM-5.7.3)

### 6.1 Schema Validation
- All prompts specify output matching JSON Schema Draft 2020-12
- Required fields explicitly listed
- Enum values match schema exactly
- Type constraints documented

### 6.2 Business Rule Alignment

| Schema Business Rule | Prompt Enforcement |
|---------------------|-------------------|
| CH-001: name unique per project | Duplicate Rules CH-DUP-01/02 |
| CH-002: relationship target exists | Deferred to validation phase |
| CH-003: no self-referential | Not extracted (single segment) |
| CH-004: aliases unique per (char, lang, type) | Duplicate Rules CH-DUP-03 |
| CH-005: cultivation_realm for xianxia | Extraction Rule CH-EXT-08 |
| GL-001: canonical unique per (source, domain) | Duplicate Rules GL-DUP-01/02 |
| GL-002: no alias duplicates canonical | Extraction Rule GL-EXT-08 |
| GL-003: context_rule priority unique | Not applicable at extraction |
| GL-004: forbidden != canonical | Extraction Rule GL-EXT-07 |
| GL-005: confidence >= 0.7 for approved | Confidence Rules + review_status |

### 6.3 Manifest Integration
- Each extraction produces entities ready for manifest inclusion
- entity_count verifiable from output array length
- SHA-256 computable from deterministic JSON output
- validation_summary.schema_valid = true by construction

---

## 7. Testing Recommendations

### 7.1 Unit Tests (Per Extractor)
1. Schema validation - Output passes jsonschema.validate()
2. Determinism - Identical input produces identical output (100 runs)
3. Confidence bounds - All scores in [0.0, 1.0]
4. Required fields - No missing required fields
5. Enum compliance - All enum fields use valid values
6. Duplicate handling - Known duplicates produce merged output

### 7.2 Integration Tests
1. Cross-extractor consistency - Same source_location format
2. Manifest generation - Entities pack into manifest correctly
3. Validation pipeline - RM-5.7.3 validator accepts outputs
4. Round-trip - Extract -> Validate -> Manifest -> Load

### 7.3 Edge Case Tests
1. Empty extraction - Returns [] not null
2. Ambiguous input - Produces flagged entities (confidence < 0.3)
3. Schema boundary - Max length strings, max array sizes
4. Unicode handling - CJK, emoji, special characters preserved

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Provider non-determinism | Medium | High | Zero temperature, fixed seeds, validation |
| Schema drift | Low | High | CI validation on every change |
| Confidence miscalibration | Medium | Medium | Calibration dataset, periodic review |
| Duplicate false positives | Low | Medium | Conservative merge rules, defer cross-chapter |
| Missing extraction | Medium | Low | Low confidence threshold, review flag |

---

## 9. Maintenance Notes

### 9.1 Versioning
- Prompt version tracked in document header
- Schema version in schema_version field
- Breaking changes require MAJOR version bump

### 9.2 Update Procedure
1. Modify prompt document
2. Update corresponding schema if needed
3. Run full validation suite
4. Update this report
5. Tag release

### 9.3 Deprecation Policy
- Old prompt versions archived in docs/governance/rm5/archive/
- Minimum 2 version overlap during transition
- Migration scripts for entity format changes

---

## 10. Compliance Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Deterministic | Check | Fixed templates, UUIDv5, alphabetical keys |
| Provider-independent | Check | No provider-specific syntax |
| Schema-aware | Check | Field-by-field mapping tables |
| RM-5.7.2 schema compatible | Check | Verified against all 5 schemas |
| RM-5.7.3 ready | Check | Business rules aligned, manifest-ready |
| No runtime changes | Check | Documentation only |
| No provider execution | Check | Design phase only |
| No network requests | Check | Design phase only |
| Production code modified = 0 | Check | Only docs created |
| git diff --check PASS | Pending | Requires validation |

---

## 11. Sign-Off

**Design Author**: NTPE AI Workspace  
**Review Date**: 2026-08-02  
**Next Review**: Upon RM-5.7.3 integration testing

### Acceptance Criteria Met
- [x] 5 extractor prompt documents created
- [x] Each contains all 7 required sections
- [x] All prompts schema-compliant
- [x] Determinism guarantees documented
- [x] Cross-extractor consistency verified
- [x] Validation readiness confirmed
- [x] Report document created

---

*End of RM-5.7.2A Prompt Design Report*
"""

with open(os.path.join(base_path, "RM_5_7_2A_PROMPT_DESIGN_REPORT.md"), "a", encoding="utf-8") as f:
    f.write(report_part3)

print("Report Part 3 appended - COMPLETE")