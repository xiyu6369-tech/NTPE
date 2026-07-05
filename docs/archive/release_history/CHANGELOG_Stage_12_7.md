# NTPE 1.0 Beta — Stage-12.7 REST Middleware / Auth Hooks

## Added

- `external_api/rest_middleware.py`
  - `RestMiddlewareContext`
  - `RestMiddlewareChain`
  - before middleware hook support
  - after middleware hook support

- `external_api/rest_auth.py`
  - `RestAuthContext`
  - `RestAuthResult`
  - `RestAuthHooks`
  - required-header auth helper
  - opt-in auth evaluation

- `tests/beta_stage_12_7/`
  - REST middleware/auth test launcher
  - middleware/auth compatibility tests
  - translation validation launcher

## Updated

- `external_api/rest_api.py`
  - added auth hook evaluation before REST dispatch
  - added before/after middleware chain
  - added middleware/auth manifest metadata

- `external_api/__init__.py`
  - exported Stage-12.7 middleware and auth public symbols

## Compatibility

- Existing REST behavior remains unchanged when no auth hooks or middleware are registered.
- REST Layer still delegates to the frozen Runtime API surface.
- No direct dependency on Runtime internals, Workflow internals, or Platform Services internals was introduced.

## Validation

```text
Stage-12.7 REST Middleware / Auth Hooks: PASS
Translation Validation Stage-12.7: PASS
Stage-12.6 REST Resource API: PASS
```

## Commit

```bash
git add external_api/rest_middleware.py external_api/rest_auth.py external_api/rest_api.py external_api/__init__.py tests/beta_stage_12_7 README_NTPE_1_0_Beta_Stage_12_7.txt CHANGELOG_Stage_12_7.md Translation_Validation_Report_Stage_12_7.md
git commit -m "Stage-12.7 REST Middleware and Auth Hooks"
git push
git tag beta-stage-12.7-rest-middleware-auth-hooks
git push origin beta-stage-12.7-rest-middleware-auth-hooks
```
