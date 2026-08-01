# RM-5.6 Schema Validation Report

**Stage**: RM-5.6 — Glossary Data Pipeline Validation  
**Date**: 2026-08-02  
**Component**: Schema Validation

---

## Schema Definition

### memory/glossary.json Root Structure

```json
{
  "summary": { ... },
  "terms": { ... }
}
```

### summary Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ntpe_module | string | ✅ | Module identifier |
| version | string | ✅ | Builder version |
| generated_at | string (ISO8601) | ✅ | Generation timestamp |
| source_file_count | integer | ✅ | Number of auto files processed |
| source_files | array[string] | ✅ | List of source filenames |
| term_total | integer | ✅ | Total unique terms |
| locked_count | integer | ✅ | Terms with locked=true |
| translated_count | integer | ✅ | Terms with non-empty translation |
| character_alias_count | integer | ✅ | Aliases in character_alias_index |
| character_collision_count | integer | ✅ | Collisions detected |
| category_counts | object | ✅ | Count per category |

### terms Object

Dictionary keyed by term string, value is TermEntry.

### TermEntry (12 fields)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| source | string | ✅ | == dictionary key |
| translation | string | ✅ | Can be empty |
| category | string | ✅ | Enum: abbreviation, organization, code, person_name, english_term, proper_english_term, unknown |
| total_count | integer | ✅ | ≥ 0 |
| books | object | ✅ | {book_name: count}, empty allowed |
| book_count | integer | ✅ | == len(books) |
| locked | boolean | ✅ | |
| status | string | ✅ | Enum: manual_locked, manual_unlocked, auto |
| aliases | array[string] | ✅ | Empty allowed |
| notes | array[string] | ✅ | Empty allowed |
| confidence | number | ✅ | 0.0 - 1.0 |
| created_by | string | ✅ | Builder version string |

---

## Validation Results

### Field Presence: ✅ PASS
All 12 fields present in all 7 terms.

### Type Correctness: ✅ PASS
All fields match declared types.

### Enum Validation: ✅ PASS
- category: All values valid
- status: All values valid

### Range Validation: ✅ PASS
- total_count ≥ 0: PASS
- book_count ≥ 0: PASS  
- confidence ∈ [0.0, 1.0]: PASS

### Encoding: ✅ PASS
- UTF-8 without BOM
- Chinese characters preserved (ensure_ascii=False)

### Duplicate Keys: ✅ PASS
No duplicate keys in terms object.

---

## Auto → Builder Field Mapping

| Auto Field | Builder Field | Transform |
|------------|---------------|-----------|
| source | source | Direct |
| translation | translation | Direct |
| count | total_count | Renamed |
| locked | locked | Direct |
| note | notes[] | Wrapped in array |
| (new) | category | Inferred by classify_term() |
| (new) | books | Aggregated per volume |
| (new) | book_count | len(books) |
| (new) | status | Derived from locked |
| (new) | aliases | [] |
| (new) | confidence | Computed |
| (new) | created_by | Builder version |

---

## Override Field Requirements

Override file uses same TermEntry schema. Builder applies:
- locked → true
- status → "manual_locked"  
- confidence → 1.0
- created_by → "NTPE Glossary Builder v1.1.1"

---

## Conclusion

Schema validation **PASSED** ✅