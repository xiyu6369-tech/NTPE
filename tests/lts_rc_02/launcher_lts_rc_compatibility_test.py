from __future__ import annotations

from pathlib import Path

from lts.compatibility_validation import LTSRCCompatibilityOptions, build_lts_rc_compatibility_manifest, validate_lts_rc_compatibility


def main() -> int:
    manifest = build_lts_rc_compatibility_manifest(LTSRCCompatibilityOptions(root=Path.cwd()))
    result = validate_lts_rc_compatibility(manifest)
    print("NTPE 1.1 LTS RC-02 Compatibility Validation Test")
    print("==================================================")
    print(f"Compatibility Status      {result['status'].upper()}")
    print(f"Failure Count             {result['failure_count']}")
    print(f"Public Commands           {result['public_command_count']}")
    print(f"Runtime Files             {result['runtime_file_count']}")
    print("PASS" if result["status"] == "pass" else "FAIL")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
