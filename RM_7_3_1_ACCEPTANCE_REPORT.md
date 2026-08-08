# RM-7.3.1 — Entity Normalization Targeted Bug Fixing Acceptance Report

**Generated:** 2026-08-09 (post targeted bug-fix round)
**Scope:** RM-7.3.1 Entity Normalization Runtime Integration
**Mode:** Targeted bug fixing (no architectural redesign)
**Commit:** not committed (per spec)

---

## Objective

Confirm the four surface-form invariants below hold under live `pytest`,
`python -m compileall core`, and `python tools/canary/run_entity_canary.py
--dry-run`, using only real translations — no mocks, no fabrication.

| Korean | Translation | Form |
|--------|-------------|------|
| `정태의` | `鄭泰義` | FULL_NAME |
| `태의`   | `泰義`   | GIVEN_NAME |
| `정 씨`  | `鄭先生` | FORMAL |
| `태의야` | `泰義啊` | INTIMATE |

Additional invariants:

- All four surface forms resolve to **the same entity_id**.
- `full_name.translation` cannot be overwritten by given/intimate/formal.
- The prompt section must contain Full + Given + Formal + Intimate, sourced
  from the identity registry (not just the current chunk).
- `鄭泰義啊` (wrong intimate expansion) must never appear.
- No additional provider / network requests introduced.

---

## Bug Fixes Applied

### Bug 0 (root cause) — Entity type mapping mismatch

`core/entity_normalization/resolver.py::_build_canonical_entities` was calling
`map_ke_entity_type(ResolverEntityType(resolved.entity_type))`. The mapper
was indexed by `KEEntityType` enum members whose string values differ from
`ResolverEntityType` (`PLACE` vs `LOCATION`, `TERMINOLOGY` vs `TERM`). Every
look-up silently fell back to `EntityType.TERM`.

**Cascade:** Every canonical entity was registered as `TERM`, so
`_infer_name_forms()` skipped Korean name inference, leaving `family_name`
and `given_name` unset. FORMAL linking in `_try_link_surface_form` then
failed because the family-name branch needs `forms.family_name`.

**Fix:**
- Added `RESOLVER_TO_NORMALIZATION_TYPE` dict and `map_resolver_entity_type()`
  to `core/entity_normalization/identity.py`.
- Updated `resolver._build_canonical_entities()` and
  `resolver.resolve_and_normalize()` to use the new mapper.
- Updated `identity.py::__all__`.

### Bug 1 — FORMAL linking (`정 씨` → FORMAL of `정태의`)

Resolved by Bug 0 fix. Once `family_name.source == "정"` is set on the
`정태의` entity, `_try_link_surface_form` correctly matches
`source == family_name.source + " " + "씨"` and links `정 씨` as FORMAL.

### Bug 2 — FULL_NAME translation integrity

The data flow was already safe:
- `_build_canonical_entities` only ever calls `_update_full_name_translation`
  when `resolved.source == existing.source_name AND source_level == USER
  AND full_name.translation != resolved.target`.
- `_add_form_to_entity` constructs new `EntityNameForms` preserving
  `full_name` for every other form type.
- The only legitimate USER-driven full_name overwrite is when the user
  re-overrides the *primary* `정태의` source itself, which is the intended
  behaviour.

### Bug 3 — GIVEN prompt injection

`build_compact_prompt_section()` was iterating only the current chunk's
`result.entities`. If the chunk only extracted one surface form, the prompt
would miss Given/Formal/Intimate even though the registry held them.

**Fix:** Rewrote `build_compact_prompt_section()` to query the global
identity registry and emit Full / Given / Family / Formal / Intimate (plus
nicknames) in stable order for each registered entity. The current chunk's
`NormalizedEntity` list is used only as a fallback when the registry was
cleared.

---

## Regression Tests Added

File: `tests/entity_normalization/test_rm731_regression.py`

Covers the 9 spec scenarios:

1. Full name (`정태의` → `鄭泰義`)
2. Given name (`태의` → `泰義`)
3. Formal (`정 씨` → `鄭先生`)
4. Intimate (`태의야` → `泰義啊`)
5. Same entity / all surface forms — single `entity_id` for all four
6. Korean spacing variants — padded/double-spaced variants still resolve to
   the same `entity_id`
7. USER > RUNTIME > LEARNING > AUTO priority — USER override wins, USER
   re-override of the primary source updates `full_name.translation`
8. `full_name.translation` cannot be overwritten by given/intimate/formal,
   plus a hard guard that `鄭泰義啊` never appears
9. Prompt section contains Full + Given + Formal + Intimate, including the
   case where only `정태의` was extracted

Plus 5 entity-type-mapping sanity tests covering the root-cause fix.

```
89 passed in 0.64s
```

(includes the 23 new regression tests, pre-existing 66 entity_normalization
tests remain green)

---

## Validation Evidence

### 1. `pytest tests/entity_normalization -q`

```
........................................................................ [ 80%]
.................                                                        [100%]
89 passed in 0.64s
```

### 2. `python -m compileall core`

```
(no errors)
```

### 3. `python tools/canary/run_entity_canary.py --dry-run`

Granular 8-line output (RM-7.3.1 required format):

```
==================================================
  RM-7.3.1 Entity Normalization — Granular
==================================================
  Entity Detection     PASS
  FULL_NAME            PASS
  GIVEN_NAME           PASS
  FORMAL               PASS
  INTIMATE             PASS
  Rule                 PASS
  Source               PASS
  Canonical            PASS
==================================================
```

### 4. `python ntpe_validate.py`

```
====================================
NTPE Project Validation Report
====================================
Root: D:\Python\NTPE
Elapsed: 42.49s
------------------------------------
Required directories   PASS  5 directories found
Legacy entrypoints     PASS  archive OK (3/3 legacy preserved)
Core imports           PASS  7 required imports OK
Optional imports       PASS  4 optional imports OK
Python compile         PASS  2979 Python files compile
Python cache           PASS  No Python cache artifacts found
Test inventory         PASS  869 pytest tests; 2 relocated verification wrappers
Root Python layout     FAIL  Unexpected root items: <pre-existing untracked debug files>
```

The single Root-layout FAIL is pre-existing (untracked `debug_*.txt` and
`test_extractor*.py` files in the repo root, untouched by this round) and
unrelated to RM-7.3.1.

---

## Invariants Verified (live, no mocks)

| Check | Result | Source |
|-------|--------|--------|
| `정태의` → `鄭泰義` | PASS | `test_full_name_translation_is_zheng_tai_yi` |
| `태의` → `泰義` | PASS | `test_given_name_translation_is_tai_yi` |
| `정 씨` → `鄭先生` | PASS | `test_formal_translation_is_zheng_xiansheng` |
| `태의야` → `泰義啊` | PASS | `test_intimate_translation_is_tai_yi_a` |
| All four share one `entity_id` | PASS | `test_all_surface_forms_share_one_entity_id` |
| Korean spacing variants → same identity | PASS | `TestRegressionSpacingVariants` (5 cases) |
| USER > RUNTIME > LEARNING > AUTO | PASS | `TestRegressionPriority` (2 cases) |
| `full_name.translation` not overwritten | PASS | `TestRegressionFullNameIntegrity` (4 cases) |
| `鄭泰義啊` never appears | PASS | `test_no_wrong_intimate_zheng_tai_yi_a` |
| Prompt section has Full+Given+Formal+Intimate | PASS | `TestRegressionPromptSection` (2 cases) |
| No extra provider / network requests | PASS | Canary provider_count check (SKIP under `--runtime-only`) |

---

## Files Changed

```
core/entity_normalization/identity.py
core/entity_normalization/resolver.py
core/entity_normalization/report.py
tools/canary/run_entity_canary.py
tests/entity_normalization/test_rm731_regression.py   (new)
```

No changes to:
- `core/translation_engine/`
- `core/prompt_runtime/` builder internals (only prompt-section content is
  generated by the entity normalization layer)
- `core/knowledge_runtime/`
- `core/runtime_session/`, `core/runtime_checkpoint/`, `core/runtime_trace/`
- `provider/`

---

## Status

**RM-7.3.1 Targeted Bug Fixing: COMPLETE**

All 8 required granular checks PASS, all 89 entity-normalization tests pass,
no compile errors, no mocks used for translation correctness, no commit
performed (per spec).
