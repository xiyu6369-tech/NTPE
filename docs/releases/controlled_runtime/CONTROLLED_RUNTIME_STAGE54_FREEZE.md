# Controlled Runtime Preparation — Stage 5.4 Freeze

## Scope

Stage 5.4 freezes the offline preparation chain introduced by Stages 5.1–5.3:

1. an explicitly approved execution scope becomes an immutable Controlled Runtime Submission Package;
2. the submission maps one-to-one into an Offline Runtime Adapter Request;
3. a caller explicitly selects one adapter unit for an immutable single-unit execution plan;
4. the Freeze API validates source hashes, schemas, public APIs, policies, invariants, and offline boundaries.

The activation gate is `controlled_runtime_preparation_frozen`.

## Submission Package Contract

The frozen submission schema is
`ntpe.controlled_runtime_submission_package / 1.0`, using
`deterministic_controlled_runtime_submission_v1` and the
`controlled_runtime_submission_prepared` gate.

Only explicitly approved units are mapped. Units are not expanded, merged,
resegmented, removed, or reordered. Submission coverage remains `1.0` inside
the selected units, while approval coverage describes the selected character
count relative to the original package. Runtime execution is false and
provider/translation counters remain zero.

## Offline Runtime Adapter Contract

The frozen adapter request schema is
`ntpe.controlled_runtime_adapter_request / 1.0`, using
`deterministic_offline_runtime_adapter_v1` and the
`controlled_runtime_adapter_prepared` gate.

Submission units map one-to-one and retain text, offsets, section references,
scope, authorization flags, and all upstream fingerprints. Provider and
translation execution capabilities are false. Retry, fallback, output
replacement, output/resume/cache writes, and production hooks are unsupported.
The capability boundary cannot be relaxed through dependency injection.

## Single-unit Execution Plan Contract

The frozen plan schema is
`ntpe.controlled_runtime_execution_plan / 1.0`, using
`deterministic_single_unit_execution_plan_v1` and the
`controlled_runtime_execution_plan_prepared` gate.

The caller must explicitly select exactly one adapter index. There is no
automatic selection and no multi-unit planning. Execution is sequential, with
one planned provider request, zero retries, and zero fallbacks. Step status is
`planned_not_executed`; all counters remain zero and no translation result is
attached.

## Authorization, Capability, and Enablement

These are separate concepts:

- an approved package may carry runtime/provider/translation authorization;
- the offline adapter has no runtime/provider/translation execution capability;
- the execution plan keeps runtime/provider/translation enablement false.

Authorization never implies enablement. An approval record does not permit
immediate runtime execution, and a prepared plan does not permit a provider
call.

## Fingerprint Chain

Canonical UTF-8 JSON with sorted keys and compact separators binds:

`Execution Package → Authorization Decision → Approval Record → Runtime
Submission Package → Runtime Adapter Request → Adapter Preparation Result →
Controlled Runtime Execution Plan`.

Each layer revalidates its input and fails closed on content, scope, state,
policy, capability, or fingerprint drift.

## Immutability and Determinism

Formal models are frozen dataclasses and collection fields are tuples.
Serialization is deterministic and does not contain timestamps, UUIDs,
absolute paths, hostnames, usernames, Git hashes, or approval statements.
Repeated construction from identical inputs produces identical models,
findings, status/actions, and fingerprints.

## Security and Privacy Boundaries

Stage 5 is offline preparation only. It does not create provider payloads or
translation prompts, invoke runtime/provider/network/translation services,
schedule work, or write output/resume/cache data. Novel content is not stored
in the freeze manifest or evidence.

## Explicit Non-capabilities

- runtime execution
- provider requests
- network requests
- translation execution
- prompt construction
- scheduler dispatch
- output, resume, or cache writes
- retry or fallback execution
- output replacement
- production hooks or production integration

## Validation

Run:

```powershell
python -m pytest tests\unit\controlled_runtime_execution_plan\test_freeze.py -q
python -m pytest tests\integration\controlled_runtime_preparation_freeze_test.py -q
python verification\controlled_runtime\controlled_runtime_stage54_freeze_acceptance.py
python -m compileall core\controlled_runtime_submission core\controlled_runtime_adapter core\controlled_runtime_execution_plan -q
python ntpe_validate.py
git diff --check
```

The freeze manifest contains the canonical 16-file source hash inventory and
the complete public API and invariant inventories.

## Release State

Commit, push, and tag have not been performed. Runtime, provider, translation,
output, resume, cache, retry, fallback, and production integration remain
disabled and unexecuted.
