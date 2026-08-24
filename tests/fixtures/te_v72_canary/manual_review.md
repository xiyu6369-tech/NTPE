# TE v7.2 Stage 12.5.2 Manual Review

Status: COMPLETED - FAIL CLOSED

## canary-001-character-honorific

Overall: Candidate regression

Major improvement: None observed.

Minor improvement: None sufficient to offset the regressions.

Regression: Candidate retained the complete Korean source sentence and a Korean character name in the translated output. This introduced mixed-language output, reduced naturalness, and weakened character-name consistency compared with Baseline.

Comments: Baseline produced a concise Traditional Chinese translation. Candidate duplicated the source before the translation and retained Hangul inside the Chinese sentence. Mark Candidate as regressed; do not accept Quality Integration from this evidence.

## canary-002-scene-pronoun

Overall: Incomplete pair

Major improvement: Not assessable.

Minor improvement: Not assessable.

Regression: Not scored because the Candidate request timed out and produced no translation output.

Comments: Baseline completed, Candidate timed out after its single authorized 180-second attempt. The pair is incomplete and must not be converted into a quality judgement. No retry or Provider replay is authorized.
