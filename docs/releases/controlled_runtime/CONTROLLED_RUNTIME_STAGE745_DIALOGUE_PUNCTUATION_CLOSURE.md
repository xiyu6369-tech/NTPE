# Stage 7.4.5 Deterministic Dialogue Punctuation Closure

The consumed Stage 7.4.4 real canary established that prompt-only enforcement
is insufficient: chunk 2 returned a successful Provider response whose only
mandatory quality failure was Chinese dialogue written with balanced curly
double quotation marks instead of Traditional Chinese corner quotes.

The Stage 7.4 mandatory dialogue validator remains unchanged and fail-closed.
The correction is isolated to the authentic Stage 7.4 formatter path, after
the existing translation formatter and before mandatory quality assessment.

Conversion from `“內容”` to `「內容」` occurs only when all of these conditions
hold:

- the source proves a balanced dialogue-pair count;
- the candidate has the same number of balanced, non-nested curly pairs;
- every pair contains Chinese text and ends with dialogue punctuation;
- no corner/ASCII/single-quote system is mixed into the candidate;
- no multiline, code-like, escaped, empty, unmatched, or ambiguous content is
  present.

If any condition fails, the candidate is returned byte-identically so the
unchanged mandatory validator rejects unsafe punctuation. Already canonical
corner quotes, nested `『』`, English prose quotations, apostrophes,
measurements, and code-like content are not blindly rewritten. The operation
is idempotent and changes only eligible quote glyphs; words and speaker
attribution remain unchanged.

Chunk completion evidence version 1.1 separately records the raw Provider
candidate fingerprint, the authentic formatter fingerprint, the
post-dialogue-normalization fingerprint, whether normalization occurred, and
the converted-pair count. Quality is assessed on the normalized bytes, and
successful persisted bytes must equal the assessed bytes exactly.

The retained Stage 7.4.4 chunk-002 invalid candidate is used read-only by an
