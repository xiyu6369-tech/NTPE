# Book Intake Stage 2.8 Freeze

## Release status

Stage 2.8 implementation and Book Intake-scoped validation are complete. Final freeze
acceptance is **PASS** after the Stage 2.8.1 root-layout baseline compatibility fix.
No production activation,
commit, push, or tag has been performed.

## Scope: Stages 2.1–2.8

The frozen Book Intake layer covers source reading, encoding detection, safe decoding,
corruption detection, source-language detection, intake orchestration, book-scale
preflight analysis, canonical manifest generation, and Stage 2.8 freeze validation.
Stage 2.8 adds validation and release metadata only; it does not add intake behavior or
alter Stage 2.1–2.7 analysis policies.

## Pipeline architecture

```text
SourceFileReader
  -> EncodingDetector
  -> decode_source
  -> TextCorruptionDetector
  -> SourceLanguageDetector
  -> BookIntakeProcessor
  -> BookPreflightAnalyzer
  -> BookIntakeManifestBuilder
```

The pipeline is offline and deterministic. The intake processor reads only the caller's
specified source. Preflight and manifest construction consume immutable in-memory
results and do not reread the source.

## Frozen public API

The authoritative ordered inventory contains 42 exports in
`core.book_intake.__all__`. It includes all Stage 2.1–2.7 public types and functions,
the Stage 2.7.1 `EncodingDetector` compatibility export, and these Stage 2.8 APIs:

- `BookIntakeFreezeMetadata`
- `BookIntakeFreezeValidationError`
- `get_book_intake_freeze_metadata`
- `validate_book_intake_freeze`

The full ordered inventory is stored in
`manifests/book_intake_stage28_freeze_manifest.json`.

## Frozen schemas

Book Intake Manifest:

- schema name: `ntpe.book_intake_manifest`
- schema version: `1.0`
- top-level fields: `schema_name`, `schema_version`, `source`, `encoding`,
  `language`, `corruption`, `preflight`, `workload`, `status`, `action`,
  `content_fingerprint`, and `manifest_fingerprint`
- section models: source, encoding, language, corruption, preflight, and workload
- section models and manifest model remain frozen dataclasses
- canonical JSON uses sorted keys, compact separators, UTF-8, and no ASCII escaping
- the manifest fingerprint excludes itself and includes the content fingerprint

## Frozen status/action contract

| Status | Action |
|---|---|
| `ready` | `proceed` |
| `ready_with_warnings` | `proceed_with_warning` |
| `manual_review_required` | `manual_review` |
| `blocked` | `reject` |

The current Stage 2.6 preflight model uses the same four status names. Corruption
blocking has priority. Unknown and mixed languages require manual review unless an
existing corruption result already blocks intake.

## Finding policy

The frozen preflight codes are:

`EMPTY_CONTENT`, `VERY_SHORT_BOOK`, `LARGE_BOOK`, `VERY_LARGE_BOOK`,
`EXTREME_BOOK_SIZE`, `EXCESSIVE_LINE_LENGTH`, `SINGLE_LINE_BOOK`,
`LOW_PARAGRAPH_STRUCTURE`, `HIGH_BLANK_LINE_RATIO`, `HIGH_CHUNK_WORKLOAD`,
`EXTREME_CHUNK_WORKLOAD`, `INTAKE_BLOCKED`, `INTAKE_MANUAL_REVIEW`, and
`INTAKE_WARNING`.

Only the highest applicable size-family and workload-family threshold is emitted.
Finding order remains content, size, line/paragraph, workload, then aggregate intake.

## Determinism guarantees

The same fixtures are executed three times. Encoding, decoded text, corruption and
language results, intake decision, preflight statistics/findings, manifest dictionary,
canonical JSON, content fingerprint, and manifest fingerprint remain equal. Fixtures
cover Korean, Traditional Chinese, Japanese, English, mixed and unknown language,
empty analyzer/manifest input, short content, long single-line content, high blank-line
ratio, and simulated large workload.

Freeze metadata contains no timestamp, date, UUID, host, user, absolute path, commit
hash, random value, or environment-dependent field.

## Security and privacy boundaries

- provider requests: 0
- network requests: 0
- translation executions: 0
- production hooks added: 0
- runtime integration added: 0
- launcher integration added: 0
- production source-file writes: 0
- production manifest-file writes: 0
- novel reads by freeze validation: 0

Tests may create temporary source fixtures. No full novel content is stored in the
freeze manifest or evidence.

## Explicit non-capabilities

This freeze does not authorize production integration, translation runtime integration,
provider execution, launcher integration, automatic translation, GUI integration, or
production deployment.

## Activation gate

The gate name is `book_intake_layer_frozen`. It means the Book Intake API and schema
are ready for a later integration stage. It does not grant any production or execution
authorization.

## Integration validation scope correction

Broad integration command:

```powershell
python -m pytest tests\integration -q -k "book_intake"
```

Result:

Blocked during collection by an unrelated existing launcher integration module that
raises `SystemExit` before pytest applies the `-k` filter. The preceding launcher
check reports `Prompt includes novel quality FAIL`.

Book Intake implication:

None.

Remediation:

Validation scope changed to explicit Book Intake integration test paths. The only
matching file is `tests/integration/book_intake_freeze_test.py`, which passes. No
unrelated production or test files were modified. Six prompt/literary output diffs
briefly produced by the broad collection attempt were precisely restored and are not
part of Stage 2.8.

## Repository validator status

The Stage 2.8 standalone acceptance was relocated to
`verification/book_intake/book_intake_stage28_freeze_acceptance.py` to comply with
the root Python layout policy. The first repository validation then reported four
pre-existing tracked root items:

- `.clineignore`
- `.clinerules`
- `.editorconfig`
- `.ai`

Stage 2.8.1 classified this as `repository_layout_baseline_gap` and added only those
three files and the `.ai` directory to the explicit project layout allowlists. It did
not add wildcard acceptance for dotfiles or root directories. Unknown root files,
directories, and Python scripts remain rejected.

No repository tooling metadata was deleted or ignored. After the precise baseline fix,
`ntpe_validate.py` reports Root Python layout PASS and ALL PASS. Final Stage 2.8
acceptance is PASS.

## Validation commands

```powershell
python -m pytest tests\unit\book_intake\test_freeze.py -q
python -m pytest tests\integration\book_intake_freeze_test.py -q
python verification\book_intake\book_intake_stage28_freeze_acceptance.py
python -m pytest tests\unit\book_intake -q
python -m pytest tests\unit\book_intake\test_public_api_compatibility.py -q
python -m compileall core\book_intake -q
python ntpe_validate.py
git diff --check
git status --short
git diff --stat
```

## Git operations

Commit, push, and tag have not been performed.
