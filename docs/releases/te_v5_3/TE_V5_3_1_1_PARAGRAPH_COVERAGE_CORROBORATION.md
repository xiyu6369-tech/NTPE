# TE v5.3.1.1 Paragraph Coverage Corroboration Fix

## Problem

Literary Korean-to-Traditional-Chinese translation may legitimately merge adjacent source paragraphs. The v5 baseline treated paragraph-count reduction alone as a high-severity omission and forced repeated provider calls even when sentence and length coverage remained healthy.

## Fix

- Paragraph-count reduction now requires independent sentence-count or length-ratio corroboration before becoming `paragraph_omission_suspected` (high/retry).
- A paragraph-only mismatch becomes `paragraph_structure_merged` (medium/warning).
- Genuine omission still remains blocking.
- No Provider, timeout, retry, 40 RPM, backpressure, resume, terminology, or safe-normalization behavior is changed.
