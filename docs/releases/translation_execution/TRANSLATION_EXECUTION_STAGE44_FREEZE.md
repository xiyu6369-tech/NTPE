# Translation Execution Governance — Stage 4.4 Freeze

## Scope

Stage 4.4 freezes the deterministic offline governance chain established by
Stages 4.1 through 4.3:

```text
BookPreparationResult
  -> TranslationExecutionPackage
  -> ExecutionAuthorizationDecision
  -> ExplicitHumanApprovalRequest
  -> ExecutionApprovalRecord
```

Stage 4.1 prepares an immutable, execution-free package. Stage 4.2 evaluates
that package using a fail-closed, default-denied authorization contract. Stage
4.3 accepts only an explicit caller-supplied human approval request with an
exact unit scope. Stage 4.4 adds the freeze metadata, validator, manifest,
evidence, documentation, tests, and standalone acceptance; it does not add an
execution path.

## Frozen schemas and activation gate

The frozen schemas are:

- Package: `ntpe.translation_execution_package` / `1.0`
- Authorization: `ntpe.translation_execution_authorization_decision` / `1.0`
- Approval: `ntpe.translation_execution_approval_record` / `1.0`

The Stage 4.4 activation gate is
`translation_execution_governance_frozen`. It identifies a validated
governance baseline only. It does not activate a provider, translation,
runtime submission, output replacement, or production integration.

## Package contract

`TranslationExecutionPackageBuilder` consumes the accepted
`BookPreparationResult` and preserves the source through a one-to-one
chunk-to-unit mapping. Reconstruction is exact, offsets are gap-free and
non-overlapping, coverage is complete, and all unit collections and findings
remain tuples. Initial units are `prepared`; attempt and provider request
counters are zero; no translation result is attached; and all six
authorization flags are false. Manual-review and blocked preparation states
fail closed. `EXECUTION_NOT_AUTHORIZED` remains part of the package boundary.

## Default-denied authorization

`TranslationExecutionAuthorizationEvaluator` never grants automatic
authorization. A prepared package is denied and held for explicit human
approval; a warning-bearing package additionally requires manual review and
warning acknowledgement. Human approval remains required, all six
authorization flags remain false, policy relaxation is rejected, and
tampered or already-executed packages fail closed.

## Explicit human approval

Approval is accepted only through a caller-supplied
`ExplicitHumanApprovalRequest`. The request must contain the fixed
`APPROVE_CONTROLLED_TRANSLATION_EXECUTION` token. Warning-bearing packages
also require `ACKNOWLEDGE_PACKAGE_WARNINGS`.

The supported approval types are `single_unit`, `selected_units`, and
`full_package`. Scope order, uniqueness, bounds, and completeness are checked
exactly; scope is never sorted, deduplicated, inferred, or expanded. Provider,
translation, and runtime-submission approval flags must all be explicitly
true for the requested controlled scope. Automatic retry, automatic fallback,
and output replacement remain prohibited and false.

The approval statement itself is not persisted. Only its exact UTF-8 SHA-256
fingerprint is stored in the immutable approval record.

## Fingerprint chain and immutable models

The canonical chain is:

```text
TranslationExecutionPackage.execution_package_fingerprint
  -> ExecutionAuthorizationDecision.package_fingerprint
  -> ExecutionApprovalRecord.package_fingerprint

ExecutionAuthorizationDecision.authorization_fingerprint
  -> ExecutionApprovalRecord.authorization_fingerprint
```

Package, unit, authorization decision, approval request, approval record, and
freeze result models are frozen dataclasses. Canonical JSON uses stable key
ordering and compact separators. Fingerprints use exact UTF-8 bytes and
lowercase 64-character SHA-256 hex. Tampering at any link is rejected without
modifying the package, decision, units, counters, or attached-result state.

## Determinism and compatibility

Three identical repetitions produced identical packages, units, unit IDs,
unit fingerprints, package fingerprints, authorization decisions and
findings, authorization fingerprints, approval records and findings, approved
scopes, approval fingerprints, and freeze metadata. Coverage includes
prepared and warning-bearing packages, CRLF, Unicode and multilingual source,
multiple chunks, all three approval types, warning acknowledgement, invalid
scope, package tampering, and policy-relaxation rejection.

The established public imports remain unchanged:

```python
from core.translation_execution_package import TranslationExecutionPackageBuilder
from core.translation_execution_authorization import TranslationExecutionAuthorizationEvaluator
from core.translation_execution_approval import TranslationExecutionApprover
```

The approval package adds only the five Stage 4.4 freeze exports. The frozen
inventory contains 34 unique public names and 16 sorted formal source files.
Stage 4.1 through Stage 4.3 protected source drift is zero.

## Security boundary and explicit non-capabilities

Freeze validation reads only the canonical freeze manifest and the 16 formal
Stage 4 source files. It does not read a novel source. The acceptance pipeline
uses an isolated input fixture and produces no output file.

Observed execution boundary:

```text
Provider Requests = 0
Network Requests = 0
Translation Executions = 0
Runtime Submissions = 0
Output Writes = 0
Retry Executions = 0
Fallback Executions = 0
Production Hooks Added = 0
```

This release does not enable provider access, perform translation, submit to a
runtime, replace production output, add retry or fallback behavior, or connect
the governance chain to a production hook. All global authorization fields in
the freeze metadata are false.

## Validation

The following checks passed:

```powershell
python -m pytest tests\unit\translation_execution_approval\test_freeze.py -q
python -m pytest tests\integration\translation_execution_governance_freeze_test.py -q
python verification\translation_execution\translation_execution_stage44_freeze_acceptance.py

python -m pytest tests\unit\translation_execution_approval -q
python -m pytest tests\integration\translation_execution_approval_authorization_test.py -q
python -m pytest tests\unit\translation_execution_authorization -q
python -m pytest tests\integration\translation_execution_authorization_package_test.py -q
python -m pytest tests\unit\translation_execution_package -q
python -m pytest tests\integration\translation_execution_package_preparation_test.py -q

python -m pytest tests\unit\book_preparation -q
python -m pytest tests\unit\book_chunking -q
python -m pytest tests\unit\book_segmentation -q
python -m pytest tests\unit\book_intake -q

python -m compileall core\translation_execution_package core\translation_execution_authorization core\translation_execution_approval -q
python ntpe_validate.py
git diff --check
```

Freeze unit: 9 passed. Freeze integration: 5 passed. Standalone acceptance:
PASS. Stage 4.3 current unit suite: 58 passed, comprising 49 legacy tests and
9 freeze tests; Stage 4.3 integration: 5 passed. Stage 4.2: 44 unit and 5
integration passed. Stage 4.1: 26 unit and 5 integration passed. Stage 3:
154 passed. Book Intake: 290 passed. `ntpe_validate.py`: ALL PASS.

No Commit, Push, or Tag was performed.
