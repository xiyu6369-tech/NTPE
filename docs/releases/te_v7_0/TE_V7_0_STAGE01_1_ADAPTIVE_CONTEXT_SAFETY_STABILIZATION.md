# TE v7.0 Stage 01.1 Adaptive Context Safety Stabilization

Stage 01.1 hardens the standalone Adaptive Context Engine without connecting it to Runtime or generation.

## Stabilized contracts

- Token estimation distinguishes Han, Hangul syllables, Hangul Jamo, Hiragana, Katakana, ASCII Latin, digits, punctuation, and other symbols. Hangul is estimated per code point instead of using the four-Latin-characters approximation.
- Narrative compression returns complete sentences only. If the first sentence does not fit, compression fails closed with an empty string.
- Dialogue preservation returns complete dialogue lines only.
- Required context must fit in full. Any required overflow makes the entire result inadmissible, clears selected output, and sets immutable fallback status and reasons.
- Blank IDs, duplicate IDs, and non-finite scoring values are rejected. Negative limits and budget inputs are deterministically clamped to zero.

`AdaptiveContextResult` adds backward-compatible defaulted fields: `admissible`, `fallback_required`, and `fallback_reasons`.

## Fingerprint scope

The fingerprint payload contains only each selected item's ID, kind, and SHA-256 of its selected content. It does not include ranking score, characters, source metadata, budget, admission state, or observability.

## Boundaries

No TE v6 Frozen Runtime, Provider, Prompt Builder, LTS, or TE v6 Release Contract file is modified. ACE remains explicit-call-only and has no runtime auto-hook, Provider client, HTTP request, or NVIDIA API access.

## Known limitations

- Token counts remain deterministic estimates rather than Provider-tokenizer output.
- Combining marks and emoji sequences are counted by code point rather than grapheme cluster.
- Narrative compression is extractive and sentence-boundary based; fragments without terminal punctuation fail closed when oversized.
- Required context does not support safe compression in Stage 01.1; it must fit verbatim.
