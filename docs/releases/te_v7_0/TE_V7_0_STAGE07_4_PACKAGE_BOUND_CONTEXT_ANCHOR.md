# TE v7.0 Stage 07.4 — Package-Bound Context Anchor

Stage 07.4 removes the final dependence on global prompt-marker uniqueness for ACE Canary replacement.

The runtime wrapper binds the previous-context section immediately after the prompt package is built. The binding stores only start/end offsets and SHA-256 values for the prompt, source context, and selected section. No novel text is stored in metadata.

When policy text repeats the same section label, the binder enumerates all labeled sections and accepts exactly one section whose content matches `previous_chunk_tail`. The Canary then validates the bound prompt hash, content hash, source hash, and offsets before replacement. Any mutation or ambiguity fails closed.

The contract remains single-chunk, opt-in, redacted, and does not change Provider, QA, retry, LTS, or TE v6 frozen behavior.
