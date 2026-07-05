from core.ai_provider import (
    ProviderConfigLayer,
    SecretProtectionRuntime,
    fingerprint_secret,
    redact_mapping,
    redact_text,
)


def test_secret_redaction_masks_provider_keys_in_text():
    raw = "api_key=sk-1234567890abcdef and token:nvapi-abcdefghijklmnop"
    safe = redact_text(raw)

    assert "sk-1234567890abcdef" not in safe
    assert "nvapi-abcdefghijklmnop" not in safe
    assert "[NTPE_SECRET]" in safe


def test_safe_payload_redacts_nested_secret_fields():
    payload = {
        "provider": "openai",
        "api_key": "sk-1234567890abcdef",
        "nested": {"authorization": "Bearer sk-1234567890abcdef"},
    }
    safe = redact_mapping(payload)

    assert safe["provider"] == "openai"
    assert "sk-1234567890abcdef" not in str(safe)
    assert safe["api_key"].endswith("cdef")


def test_secret_runtime_reports_masked_fingerprint_without_plaintext(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-1234567890abcdef")
    runtime = SecretProtectionRuntime()
    report = runtime.credential_report("openai", env_var="OPENAI_API_KEY")

    assert report["configured"] is True
    assert report["env_var_allowed"] is True
    assert report["fingerprint"] == fingerprint_secret("sk-1234567890abcdef")
    assert "sk-1234567890abcdef" not in str(report)


def test_secret_scanner_finds_plaintext_assignment():
    runtime = SecretProtectionRuntime()
    findings = runtime.scan_text("OPENAI_API_KEY=sk-1234567890abcdef", path="config.env")

    assert findings
    assert findings[0].path == "config.env"
    assert "sk-1234567890abcdef" not in findings[0].preview


def test_provider_config_manifest_remains_masked(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-abcdefghijklmnop")
    layer = ProviderConfigLayer.standard()
    manifest = layer.manifest()

    assert "nvapi-abcdefghijklmnop" not in str(manifest)
    assert manifest["credential_validation"]["nvidia"]["configured"] is True
