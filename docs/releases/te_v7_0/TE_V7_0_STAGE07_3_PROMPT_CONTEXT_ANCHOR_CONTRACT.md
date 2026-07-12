# TE v7.0 Stage 07.3 — Prompt Context Anchor Contract

## Purpose

Stage 07.3 replaces unsafe full-prompt text search with a deterministic prompt-context anchor. The canary may replace previous context only when the prompt section is uniquely identified, its content hash matches the package context contract, and prefix/suffix bytes remain unchanged.

## Contract

- No prompt policy text, provider configuration, LTS source, or TE v6 frozen contract is modified.
- Supported anchor strategies are the production Traditional Chinese previous-context section and the compact literary `【Previous】` section.
- Anchor metadata records offsets, strategy, and SHA-256 values only; context text is redacted.
- Replacement uses verified offsets, not `str.replace()` or first-match selection.
- Text outside the anchored span remains byte-identical.
- Missing, ambiguous, malformed, or hash-mismatched anchors fail closed.
- Canary remains single-chunk, explicit opt-in, and non-expanding.

## Safety reasons

Possible fallback reasons include:

- `prompt-context-anchor-marker-missing`
- `prompt-context-anchor-ambiguous`
- `prompt-context-anchor-hash-mismatch`
- `prompt-context-anchor-content-unavailable`
- `prompt-context-anchor-replacement-failed`

## Scope

This Stage provides the addressing contract required for a real canary activation. It does not enable full active mode and does not claim translation quality, provider latency, or cost improvement.
