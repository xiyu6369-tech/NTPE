# TE v7.2 Milestone A — Translation Quality Integration

## Status

`translation_quality_integration_ready_for_controlled_canary`

Milestone A implements Stages 12.3–12.5 as one default-off, provider-free additive prompt integration. It is ready for controlled-canary review only. Production, Provider execution, automatic rollout, formal output replacement, and dual-pass execution remain unauthorized.

## Integration design

Character Memory V2 is read through its frozen public selection API. The integration first limits candidates to characters directly mentioned or explicitly active in the current scene, then applies deterministic priority and token trimming. Expired, rejected, superseded, conflicted, invalid, low-confidence, and unapproved AI-inference records remain excluded by the frozen selector. Rendered prompt content contains only the eligible translation aid; it omits raw evidence, evidence identifiers, hashes, paths, audit fields, and lifecycle metadata.

Context／Scene Memory is also read through its frozen public API. Selection is restricted to the current chapter/scene and bounded sequence, present or mentioned participants, non-stale previous context, valid unresolved references, and trusted evidence. Exited participants, stale or conflicting context, experimental inference, and other-scene data are excluded.

The Naturalness policy is a prompt-only, fidelity-first instruction for Traditional Chinese literary prose. It explicitly preserves completeness, semantics, terminology, ambiguity, negation, numbers, and time; it forbids summaries, omissions, additions, unsupported causality, and automatic full-name completion.

## Runtime boundary and flags

One hook is installed in `lts.txt_translation_runtime.build_prompt_package()` after existing prompt/context intelligence and before provider preparation. Disabled flags return the original package object. Enabled integration shallow-copies only the package and prompt metadata that it changes; it never calls Provider, writes Output, mutates Resume, or writes either memory store.

Flags are default false:

- `--quality-integration-v72`
- `--quality-character-memory-v72`
- `--quality-context-scene-v72`
- `--quality-naturalness-v72`
- `--quality-integration-kill-switch-v72`

The global flag enables all three components. Subflags can be enabled independently. The kill switch overrides every enable flag immediately.

## Prompt budget

The existing prompt profile, including full source, mandatory policy, and matched glossary, is reserved before any Milestone A allocation. The default total ceiling is 4096 estimated tokens. Default component ceilings are Character 256, Context 384, Scene 192, and Naturalness 192. A second check measures the fully rendered section and trims bounded context first, then scene metadata, then non-core character material. Source text is never truncated.

## Determinism and performance

All record iteration, selection, rendering, metadata, and fingerprint inputs use stable sorting and canonical JSON. Runtime callers may provide a fixed selection timestamp; the default fails closed for time-bounded records rather than using wall-clock time.

The measured pure integration layer completed 100 runs with one unique output and one unique fingerprint:

- p50: 0.03655 ms
- p95: 0.0609 ms
- max: 0.3749 ms
- 100-run total: 4.7597 ms

## Validation boundary

Focused acceptance passed 20 tests. TE v6.0 Final Release, TE v7.1 Stage 11.8 Freeze, and TE v7.2 Stage 12.1 Frozen Boundary wrappers all passed. Applicable Character Memory, Context／Scene Memory, Multilingual Profile, Naturalness, Prompt, Provider security, Resume, Output, and production-shadow behaviors passed.

Five historical batch-local gates were isolated: four assert that the dirty worktree contains only their old batch, and one expects the original uncommitted Batch 10.1 diff. A Batch 2 hash report also pins shared runtime paths now intentionally changed by this additive milestone. These historical tests were not modified; their behavior portions passed when the obsolete batch-local gate was deselected. Details are recorded in `boundary_evidence.json`.

## Authorization

- `active_production_authorized=false`
- `provider_execution_authorized=false`
- `automatic_rollout_authorized=false`
- `formal_output_replacement_authorized=false`
- `dual_pass_authorized=false`

