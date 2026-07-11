# TE v6.0 Stage 04 — Adaptive Local Repair Framework

Stage 04 adds a deterministic, provider-free local repair registry backed by
TE v6 discipline routes. Repairs are followed by the existing Quality v5 and
Legacy QA analysis so the Unified Quality Gate always decides on the repaired
text, not the pre-repair candidate.

## Safe handlers

- Traditional Chinese orthography (`一周` → `一週`, `雇員` → `僱員`)
- Balanced dialogue quotes (`“…”` → `「…」`)
- Conservative spacing before CJK punctuation

Naturalness and paragraph-merge warnings have no automatic semantic handler.
Completeness, residue, terminology, repetition and hallucination routes remain
provider-blocking.

## Compatibility

No Provider, timeout, retry, RPM, resume, score or decision threshold is
changed. Reports without Stage 03 route metadata continue through the v5
Smart Local Repair fallback.
