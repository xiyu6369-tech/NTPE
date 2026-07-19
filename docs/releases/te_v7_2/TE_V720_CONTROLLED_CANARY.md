# TE v7.2 Stage 12.5.1 — Controlled Canary

## Outcome

The Controlled Canary engineering harness is complete, but the quality canary is fail-closed as `FAIL_CLOSED_INSUFFICIENT_QUALITY_EVIDENCE`. The activation gate remains `translation_quality_integration_ready_for_controlled_canary`.

No complete set of five to ten human-reviewed Baseline/Candidate translation pairs exists in the frozen repository evidence, and this stage is not authorized to make Provider or network requests. The stage therefore does not claim that Translation Quality Integration improves model output.

## Method

Six Korean chunks cover character names, multiple characters, honorifics, scene transitions, long sentences, omitted subjects, pronouns, long dialogue, mixed narrative/dialogue, and era background. Each chunk is prepared twice with the same model identity, timeout, glossary hash, literary profile, source chunk, and corpus hash.

Run A has Quality Integration, Character, Context, and Naturalness off. Run B has those four features on. The harness proves that only those feature flags differ, the disabled prompt path remains byte-equivalent, and Milestone A selects deterministic Character, Context, and Scene records within the frozen prompt budget.

This is offline prompt preparation only. Neither arm performs translation or contacts a Provider.

## Quality comparison

The fixed checklist contains Completeness, Hallucination, Character consistency, Honorific consistency, Dialogue continuity, Speaker continuity, Context continuity, Pronoun resolution, Naturalness, Era wording, and Hangul remaining. Each engineering row uses the permitted comparison vocabulary but is marked `insufficient_evidence`; these placeholders are not treated as reviewed quality results.

The review template leaves Overall score, Strength, Weakness, Regression, Notes, and every checklist decision unset for human completion after valid paired translations are separately authorized and supplied.

## Performance and prompt metrics

The evidence records selected Character/Context/Scene counts, budget usage, prompt-token totals, and local integration latency. It stores prompt and source SHA-256 values, not full prompts or Provider payloads. Timing is observational and excluded from the deterministic semantic fingerprint.

## Boundaries

- Provider requests added: 0
- Network requests added: 0
- Runtime behavior changed: false
- Frozen Prompt Builder modified: false
- Resume modified: false
- Output modified: false
- Production authorized: false
- Automatic rollout authorized: false

No Milestone A, TE v6, TE v7.1, LCR, runtime, Provider, resume, output, memory-schema, or existing-manifest file is modified.

## Known limitation and next decision

This stage validates Canary engineering and evidence integrity, not translation-quality improvement. A later explicitly authorized evidence-ingestion or controlled execution step must supply complete paired outputs and human checklist decisions. Until then, the production gate must not advance.
