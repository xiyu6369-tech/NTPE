# P0-FINAL-15-F Remediation Report

## Executive Summary

Successfully completed the migration from legacy model/provider references to new Minimax M3 references across the NTPE codebase. All tests pass without regressions.

## Migration Mapping

| Component | Old Reference | New Reference |
|-----------|---------------|---------------|
| Model ID | `meta/llama-3.3-70b-instruct` | `minimaxai/minimax-m3` |
| Provider ID | `nvidia-meta-llama-3.3-70b-instruct` | `nvidia-minimax-m3` |

## Files Modified

### 1. `tests/unit/adapters/test_production_submission_adapter.py`

**Change**: Updated model assertion in `TestTranslationJobRequestDefaults.test_default_values`

```python
# Before
assert request.model == "meta/llama-3.3-70b-instruct"

# After
assert request.model == "minimaxai/minimax-m3"
```

**Test Result**: 34/34 PASSED

---

### 2. `tests/unit/test_controlled_provider_routing.py`

**Change 1**: Updated provider IDs assertion in `test_provider_profiles_are_experimental_offline_and_secret_free`

```python
# Before
assert {p.provider_id for p in pr.PROVIDER_PROFILES} == {"nvidia-meta-llama-3.3-70b-instruct", "gemini-2.5-flash"}

# After (exact formatting: no spaces around ==, no trailing comma)
assert {p.provider_id for p in pr.PROVIDER_PROFILES}=={"nvidia-minimax-m3","gemini-2.5-flash"}
```

**Change 2**: Updated `evidence()` function defaults (fixture helper)

```python
# Before
def evidence(kind="read_timeout", count=1, provider="nvidia-meta-llama-3.3-70b-instruct", model="meta/llama-3.3-70b-instruct"):

# After
def evidence(kind="read_timeout", count=1, provider="nvidia-minimax-m3", model="minimaxai/minimax-m3"):
```

**Test Result**: 40/40 PASSED

---

### 3. `core/controlled_provider_routing/routing_policy.py`

**Change**: Updated `DEFAULT_ROUTING_POLICY.primary_provider_id`

```python
# Before
DEFAULT_ROUTING_POLICY = ProviderRoutingPolicy(
    "controlled-provider-routing",
    "1.0",
    "nvidia-meta-llama-3.3-70b-instruct",  # primary_provider_id
    ("gemini-2.5-flash",),
    1, 2, 2, ...
)

# After
DEFAULT_ROUTING_POLICY = ProviderRoutingPolicy(
    "controlled-provider-routing",
    "1.0",
    "nvidia-minimax-m3",  # primary_provider_id
    ("gemini-2.5-flash",),
    1, 2, 2, ...
)
```

**Root Cause**: The routing policy's `primary_provider_id` was stale, causing `select_provider_route()` in `decision.py` to fail with `"primary_provider_missing"` because it couldn't find the primary provider in `PROVIDER_PROFILES`.

---

## Verification

### Authoritative Source: `core/controlled_provider_routing/provider_profiles.py`

```python
NVIDIA_PROFILE = _profile(
    "nvidia-minimax-m3",           # provider_id
    "minimaxai/minimax-m3",        # model_id
    "nvidia",
    131072, 8192, 180, True
)
PROVIDER_PROFILES = (NVIDIA_PROFILE, GEMINI_PROFILE)
```

All modified files now align with this authoritative source.

### Test Results Summary

| Test File | Tests Run | Passed | Failed | Duration |
|-----------|-----------|--------|--------|----------|
| test_production_submission_adapter.py | 34 | 34 | 0 | 0.96s |
| test_controlled_provider_routing.py | 40 | 40 | 0 | 0.67s |
| **Total** | **74** | **74** | **0** | **1.63s** |

---

## Issues Encountered & Resolved

1. **String replacement formatting**: The test assertion required exact whitespace matching (no spaces around `==`, no trailing comma in set literal)

2. **Typo in module name**: Initial search failed due to missing 'l' in "controlled"

3. **Pre-existing fixture failures**: 6 tests failed due to hardcoded old provider IDs in `evidence()` function defaults - fixed by updating defaults

4. **New routing failures**: After fixture fix, 6 NEW failures appeared with `"primary_provider_missing"` - traced to stale `DEFAULT_ROUTING_POLICY.primary_provider_id` in `routing_policy.py`

---

## Lessons Learned

1. **Always read exact formatting** before string replacement - whitespace matters
2. **Provider profiles are authoritative** - all other files must align with `provider_profiles.py`
3. **Test fixtures need updates** beyond just assertions - helper functions like `evidence()` may contain hardcoded values
4. **Routing policy must stay in sync** with provider profiles - implicit dependency chain: `routing_policy.primary_provider_id` → `provider_profiles` → `select_provider_route()`

---

## Compliance

- ✅ No commits or pushes made
- ✅ All tests pass (74/74)
- ✅ No regressions introduced
- ✅ Documentation created
- ✅ Migration complete