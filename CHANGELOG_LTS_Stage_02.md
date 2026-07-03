# NTPE 1.1 LTS Stage-02 — Resume / Retry 強化

## Added
- Added chunk-level resume state tracking for TXT novel translation.
- Added retryable provider error detection for 503, 429, ResourceExhausted, timeout, and temporary service failures.
- Added exponential retry backoff options to `ntpe_translate_txt.py`.
- Added resume-state manifest output beside each translated TXT job.
- Added Stage-02 unit and launcher tests.

## Compatibility
- Preserves `python ntpe_translate_txt.py input.txt output` Stage-01 command compatibility.
- Does not modify Foundation v1.0, frozen CLI, frozen Runtime API, frozen External API, frozen Web UI, or Stable release artifacts.
