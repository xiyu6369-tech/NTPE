# Stage 7.4 Fixture Fingerprint Closure

The committed Stage 7.4 Korean fixture has not drifted. Git commit
`f67a24cef3451100fb88c13ad57fc5de741640c0` added the fixture and the
canonical source fingerprint together, and the fixture blob at that commit is
identical to the blob at this closure baseline.

The apparent mismatch came from comparing two intentionally different
representations:

- `656daa78d4bc7f8f488ee308deb3490beca3327f4904dbd24e8c250c3906ebec`
  is SHA-256 over the exact committed UTF-8 fixture bytes. It is also the
  decoded-text and newline-normalized UTF-8 SHA-256 because this fixture has
  LF-only newlines and no encoding transformation.
- `53d96e78f7ce47c260185b55436844c1619a83d02c0feea11bef7793f28b9bea`
  is `sha256-canonical-json-v1`, the existing resolver-defined fingerprint
  produced by `canonical_sha256(source_text)`.

Stage 7.4 request and checkpoint `source_fingerprint` values use the canonical
source fingerprint. The raw-byte fingerprint is now separately bound by the
resolver so byte-level fixture drift, including newline-only drift, fails
closed. Request fingerprint fields now state their fingerprint type explicitly.

The authoritative fixture remains byte-for-byte unchanged. Its 1,633
characters still generate the established three chunks, ranges, canonical
chunk fingerprints, and chunk IDs. No Provider or network execution is part of
this closure.
