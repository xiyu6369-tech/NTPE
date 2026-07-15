# NTPE Architecture Consolidation Audit

Audit date: 2026-07-15  
Baseline: `main` at `77b11f5`  
Scope: pure audit. No existing source, Prompt, Runtime, Provider, timeout, retry, model, test, artifact, or manifest was modified.

## Executive conclusion

NTPE already has a real production spine:

`launcher_translate.py → ntpe_production_translate.py → TranslationRuntime → lts/txt_translation_runtime.py`

The main architectural problem is not the absence of a runtime. It is the accumulation of parallel legacy domains, frozen stage wrappers, duplicated integrity/serialization utilities, mirror tests, and retained full-worktree packages around that spine.

The strongest immediate finding is size-related: the ignored `NTPE.zip` is 587,775,785 bytes and represents 96.85% of the 606,846,346-byte non-`.git` workspace. Source code is not close to 600 MB. `.git` is another 581,496,025 bytes, but it is a separate history cost.

## Production translation path

1. `launcher_translate.py` delegates to `ntpe_production_translate.main`.
2. The official router builds TXT or batch options and constructs `core.translation_runtime.TranslationRuntime`.
3. `lts.txt_translation_runtime.read_text_auto` and `normalize_text` load and normalize input.
4. `split_text` creates paragraph-oriented chunks.
5. Locked glossary entries and character memory are loaded into the prompt package.
6. `LiteraryPromptBuilder` and `prompt_compiler` assemble the active literary prompt.
7. Adaptive Context shadow/rollout hooks are installed, but activation remains policy, flag, rollout, and kill-switch gated.
8. `TranslationEngine.translate_package` performs the Provider request through the runtime adapter, with timeout, retryability, and fallback handling.
9. Output is normalized, then Naturalness, collocation, voice/register, quality-v5, unsupported-detail, completeness, Hangul, repetition, terminology, and Translation Discipline checks run.
10. Accepted chunks update resume state; final output is assembled, formatted, saved, manifested, and used to update character memory.

Detailed evidence: `PRODUCTION_PATH.json`.

## Core classification

| Classification | Count | Main recommendation |
| --- | ---: | --- |
| KEEP | 15 | Preserve the official runtime, Provider, prompt, quality, reliability, and evidence boundaries. |
| MERGE | 41 | Consolidate Adaptive Context stage wrappers, Provider evidence tools, Stage 11 domains, and parallel facades behind compatibility imports. |
| DELETE candidates | 22 | Legacy standalone files with no official-entrypoint reachability; delete only after dynamic-import and external-user checks. |
| ARCHIVE | 7 | Historical platform families, scheduler line, and Stage 12 candidate after evidence preservation. |
| NEEDS REVIEW | 2 | `core/production_runtime` and `core/translation` require consumer/configuration tracing. |

Core KEEP examples: `translation_runtime`, `translation_engine`, `ai_provider`, `literary`, `prompt_compiler`, `translation_quality_v5`, `translation_discipline`, `translation_naturalness`, `translation_reliability`, and `adaptive_context_production_rollout`.

Major DELETE candidate type: unused legacy root files such as `core/translator.py`, `core/chunker.py`, `core/prompt_engine.py`, `core/rules.py`, and parallel normalization/glossary/formatter helpers. These are candidates only.

## Stage 11 recommendation

Converge the offline framework into:

- `quality/assessment`: defects, evidence, metrics, scoring.
- `quality/review`: structured review, human decision, improvement planning.
- `quality/corpus`: corpus validation, lifecycle, approval, supersession, deprecation.

Shared primitives should include artifact references, SHA-256 values, timezone-aware timestamps, human provenance, and audit events. Canonical JSON/hash and reference verification are duplicated heavily.

`translation_quality_framework_integration` is not empty: it resolves and hashes references, validates order, checks cross-stage identity, and derives integration status. It should first become a thin compatibility facade, not be deleted outright.

Improvement Planner is offline human-governed planning and should move under review/planning; it is not an independent production module. Human Decision and Corpus Governance can share provenance primitives but must retain separate lifecycle schemas. Existing Stage 11 imports need compatibility wrappers because frozen artifacts and tests encode them.

## Stage 12 recommendation

**Stage 12 A/B expansion should stop.**

- 12.1: candidate prepared, zero Provider requests, no verified improvement.
- 12.2: A/B package prepared, not executed.
- 12.2.1: baseline timed out; candidate was not sent.
- 12.2.2: independent baseline and candidate both failed; pair not reviewable.
- 12.2.3: baseline succeeded, candidate failed; pair remained incomplete and manual review stayed null.

There is no complete reviewable pair, no human winner, and no verified quality improvement. The candidate is experimental rather than a production feature. Preserve the disabled code and evidence long enough for rollback/audit, then move the candidate to `experiments/` and Provider execution records to external evidence storage. Merge the five Stage 12 root/integration pairs into a parameterized integrity suite after compatibility coverage is proven.

## Quality critical path

Naturalness Engine is truly active: canonicalization, literary collocation, voice/register analysis, and unsupported-detail checks run after Provider output. Stage 11 remains offline and does not automatically change production policy. Stage 12.1 is not connected.

Subject/pronoun errors should be addressed in entity continuity and context selection before prompt assembly. The current production path has character context, but `core/character_resolver.py` is test-only. A prompt candidate alone cannot replace explicit entity-resolution evidence.

Provider timeout and Prompt quality must remain separate dimensions. Timeout measures transport/runtime reliability; it cannot score semantic quality.

## Duplicate capabilities

Static search found:

- SHA-256 logic in 55 files.
- Canonical JSON logic in 37 files.
- Serialization logic in 89 files.
- Boundary flags in 59 files.
- Frozen dataclasses in 182 files.
- Timestamp validation in 19 files.
- Redaction logic in 56 files.
- Sensitive-data scanning in 18 files.
- Manifest validation in 16 files.

Safe consolidation is limited to primitives. Boundary policies, artifact schemas, and credential/redaction semantics must not be flattened into one generic model.

## Tests

There are 828 Python test files: 243 root, 221 integration, 24 unit, 38 smoke, 74 freeze, and 218 historical-classified tests. Eight root/integration pairs are byte-identical. Many additional pairs are semantic mirrors.

Keep runtime, Provider boundary, resume/recovery, output assembly, active quality, and current freeze gates. Parameterize repeated stage boundary flags and hash/schema checks. Earlier freezes may move to `tests/archive/` only after every assertion is mapped into a current compatibility matrix.

## Artifact retention

The required inventory covers 1,044 unique paths:

- `artifacts/`: 88 files, 204,025 bytes.
- `manifests/`: 144 files, 211,302 bytes.
- `docs/releases/`: 161 files, 212,213 bytes.
- `tests/literary/outputs/`: 651 files, 2,973,523 bytes.

Current Stage 11 anchors remain active. Stage 12 timeout/partial-pair records have long-term audit value and should be externally archived with SHA-256. Raw Provider responses must not enter the Audit ZIP. Historical literary outputs are rebuildable but should be externalized by stage, not deleted blindly.

## Repository size

| Area | Bytes |
| --- | ---: |
| Non-`.git` workspace | 606,846,346 |
| Existing `NTPE.zip` | 587,775,785 |
| `.git` | 581,496,025 |
| Tests | 4,132,486 |
| Literary outputs | 2,973,523 |
| Core | 2,348,254 |
| Artifacts | 204,025 |
| Manifests | 211,302 |
| Exact duplicate waste outside `.git` | 318,846 |

Removing or externalizing the ignored full-worktree ZIP is the dominant Batch 1 size action. Git-history reduction is a separate, destructive repository operation and must not be bundled with ordinary hygiene.

## Public API recommendation

Retain the CLI and `TranslationRuntime` as stable boundaries. Treat LTS implementation modules as compatibility-only, and decide explicitly whether SDK, runtime API, and REST API remain supported products.

Target facade:

- `ntpe.translate(...)`
- `ntpe.runtime.run(...)`
- `ntpe.quality.assess(...)`
- `ntpe.quality.review(...)`
- `ntpe.corpus.manage(...)`

Introduce these additively; migrate callers; retain frozen wrappers for at least two releases; remove old imports only after parity and rollback rehearsal.

## Consolidation batches

1. Repository Hygiene: externalize `NTPE.zip`, rebuildable outputs, cache, backup, and historical packages under an archive manifest.
2. Test Consolidation: remove exact duplicates, retain compatibility launchers, parameterize stage families.
3. Shared Utilities: migrate canonical JSON, hashes, references, time/path validation, and redaction one primitive at a time.
4. Quality API Consolidation: assessment, review, corpus, then thin compatibility facades.
5. Production Path Simplification: one CLI, one runtime, one prompt builder, explicit quality boundary; highest-risk batch.

## Highest risks

1. CRITICAL — weakening Provider authorization, redaction, or one-attempt boundaries during merge.
2. CRITICAL — breaking timeout, retry, resume, or output assembly while converging runtime paths.
3. CRITICAL — weakening root-confined artifact paths or integrity semantics in shared helpers.
4. HIGH — invalidating Stage 11 frozen hashes, schemas, or public imports.
5. HIGH — deleting latent legacy workflows without dynamic import and external consumer evidence.

## Deliverables

All detailed JSON reports live in this directory. Artifact inventory is split into indexed parts to preserve complete 1,044-path coverage. `REPOSITORY_DUPLICATES.json` contains all SHA-256 duplicate groups.

This audit makes recommendations only. No consolidation, deletion, move, rename, Provider call, translation, commit, push, or tag is part of this delivery.

