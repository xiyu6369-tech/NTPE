from core.ai_provider import ProviderConfigLayer, SecretProtectionRuntime, redact_text


def main() -> int:
    runtime = SecretProtectionRuntime()
    redacted = redact_text("api_key=sk-1234567890abcdef")
    findings = runtime.scan_text("OPENAI_API_KEY=sk-1234567890abcdef", path="config.env")
    layer = ProviderConfigLayer.standard()
    manifest = runtime.manifest()
    checks = {
        "Stage": manifest["stage"] == "NTPE 1.2 Professional Stage-14.6",
        "Redaction": "sk-1234567890abcdef" not in redacted,
        "Scanner": len(findings) >= 1 and "sk-1234567890abcdef" not in findings[0].preview,
        "Policy": manifest["policy"]["allow_plaintext_in_logs"] is False,
        "Config Compatibility": "nvidia" in layer.profiles,
    }
    print("NTPE 1.2 Professional Stage-14.6 Provider Security Test")
    print("=" * 64)
    for name, ok in checks.items():
        print(f"{name:24} {'PASS' if ok else 'FAIL'}")
    if all(checks.values()):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
