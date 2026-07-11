# TE v5.3.1.2 Unified Nonblocking Issue Mapping

Fixes aggregate `quality_v5_report.retry_required` being copied onto every detailed issue.

- Medium warnings no longer become provider retries merely because another aggregate stage requested retry.
- `PARAGRAPH_STRUCTURE_MERGED` is explicitly nonblocking.
- `SIMPLIFIED_CHINESE` with deterministic normalization repair remains a warning rather than a provider retry.
- High and critical completeness issues remain blocking.
