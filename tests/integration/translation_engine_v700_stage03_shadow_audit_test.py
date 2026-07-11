from __future__ import annotations

import json

from core.adaptive_context_runtime_shadow import (
    ShadowAuditRecord,
    clear_shadow_records,
    shadow_records,
    write_shadow_audit,
)
from core.adaptive_context_runtime_shadow.registry import append_shadow_record


def test_shadow_audit_jsonl_is_redacted(tmp_path):
    path = tmp_path / "shadow.jsonl"
    record = ShadowAuditRecord(
        version="7.0.0-stage03",
        package_id="TXT_SAMPLE_000001",
        mode="shadow",
        payload_hash_before="a",
        payload_hash_after="a",
        payload_equivalent=True,
        provider_calls_added=0,
        metrics={"baseline_context_tokens": 100, "ace_context_tokens": 60},
    )
    written = write_shadow_audit(record, path)
    assert written == path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["payload_equivalent"] is True
    assert "content" not in payload
    assert "context" not in payload

    clear_shadow_records()
    append_shadow_record(record)
    assert shadow_records() == (record,)
