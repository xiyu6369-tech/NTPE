"""TER-v2.3 Provider Configuration Audit smoke test."""

from __future__ import annotations

import ntpe_provider_audit as audit


def main() -> int:
    items = audit.run_audit("nvidia")
    names = {item.name for item in items}
    required = {
        "Provider Config",
        "Environment Variables",
        "Hardcoded API Keys",
        "Legacy Config",
        "Runtime Provider Path",
        "Provider Imports",
    }
    missing = required - names
    if missing:
        print("Missing audit items", missing)
        return 1
    provider_config = next(item for item in items if item.name == "Provider Config")
    hardcoded = next(item for item in items if item.name == "Hardcoded API Keys")
    if provider_config.status != "PASS":
        print("Provider Config", provider_config.status, provider_config.detail)
        return 1
    if hardcoded.status == "FAIL":
        print("Hardcoded API Keys", hardcoded.detail)
        return 1
    print("TER-v2.3 Provider Configuration Audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
