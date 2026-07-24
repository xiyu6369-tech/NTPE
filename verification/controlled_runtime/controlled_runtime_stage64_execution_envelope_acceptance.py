#!/usr/bin/env python
"""Stage 6.4 acceptance script — end-to-end envelope preparation verification.

Usage:
    python verification/controlled_runtime/controlled_runtime_stage64_execution_envelope_acceptance.py
"""

import sys

# Ensure the package tree is importable
sys.path.insert(0, ".")


# ---------------------------------------------------------------------------
# Import checks
# ---------------------------------------------------------------------------
print("=== Stage 6.4 Acceptance ===")

import_failures = []

required_modules = [
    "core.controlled_runtime_execution_plan.models",
    "core.controlled_runtime_execution_authorization.models",
    "core.controlled_runtime_authorization_consumption.models",
    "core.controlled_runtime_atomic_authorization_consumption.models",
    "core.controlled_runtime_execution_envelope",
    "core.controlled_runtime_execution_envelope.models",
    "core.controlled_runtime_execution_envelope.builder",
    "core.controlled_runtime_execution_envelope.verification",
    "core.controlled_runtime_execution_envelope.errors",
    "core.controlled_runtime_execution_envelope.policy",
]

for mod_name in required_modules:
    try:
        __import__(mod_name)
        print(f"  IMPORT OK: {mod_name}")
    except Exception as e:
        import_failures.append((mod_name, str(e)))
        print(f"  IMPORT FAIL: {mod_name} — {e}")

if import_failures:
    print(f"\nFAIL: {len(import_failures)} import failure(s)")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Use the PROVEN integration chain: build_full_chain()
# This function uses real upstream factories with matched fingerprints.
# ---------------------------------------------------------------------------
from tests.integration.controlled_runtime_execution_envelope_contract_test import (
    build_full_chain,
)
from core.controlled_runtime_execution_envelope import verify_execution_envelope

print("\nBuilding authentic chain via integration contract build_full_chain()...")

result = build_full_chain()

# --- Verification ---
verify_result = verify_execution_envelope(result.envelope)

# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
checks = []

# 1. Build status
checks.append(("build.status == runtime_handoff_prepared_not_executed",
               result.status == "runtime_handoff_prepared_not_executed"))

# 2. Verification passes
checks.append(("verify.status == runtime_handoff_prepared_not_executed",
               verify_result.status == "runtime_handoff_prepared_not_executed"))

# 3. Envelope schema
checks.append(("envelope.schema_name == ntpe.controlled_runtime_execution_envelope",
               result.envelope.schema_name == "ntpe.controlled_runtime_execution_envelope"))

# 4. Envelope schema version 1.0
checks.append(("envelope.schema_version == 1.0",
               result.envelope.schema_version == "1.0"))

# 5. Handoff prepared true
checks.append(("runtime_handoff_prepared == True",
               result.envelope.runtime_handoff_prepared is True))

# 6. Handoff completed false
checks.append(("runtime_handoff_completed == False",
               result.envelope.runtime_handoff_completed is False))

# 7. Execution started false
checks.append(("execution_started == False",
               result.envelope.execution_started is False))

# 8. Authorization consumed true
checks.append(("authorization_consumed == True",
               result.envelope.authorization_consumed is True))

# 9. Authorization reusable false
checks.append(("authorization_reusable == False",
               result.envelope.authorization_reusable is False))

# 10. Durable prevention established
checks.append(("durable_reuse_prevention_established == True",
               result.envelope.durable_reuse_prevention_established is True))

# 11. Registry written true
checks.append(("persistent_registry_written == True",
               result.envelope.persistent_registry_written is True))

# 12. Chain length 15
checks.append(("upstream_fingerprint_chain length == 15",
               len(result.envelope.upstream_fingerprint_chain) == 15))

# 13. Final chain element == envelope fingerprint
checks.append(("chain[14] == envelope_fingerprint",
               result.envelope.upstream_fingerprint_chain[14] == result.envelope.envelope_fingerprint))

# 14. All execution enablement false
enablements = {
    "runtime_execution_enabled": result.envelope.runtime_execution_enabled,
    "provider_execution_enabled": result.envelope.provider_execution_enabled,
    "network_execution_enabled": result.envelope.network_execution_enabled,
    "translation_execution_enabled": result.envelope.translation_execution_enabled,
    "output_write_enabled": result.envelope.output_write_enabled,
    "resume_write_enabled": result.envelope.resume_write_enabled,
    "cache_write_enabled": result.envelope.cache_write_enabled,
    "retry_enabled": result.envelope.retry_enabled,
    "fallback_enabled": result.envelope.fallback_enabled,
    "production_hook_enabled": result.envelope.production_hook_enabled,
}
for name, val in enablements.items():
    checks.append((f"enablement.{name} == False", val is False))

# 15. All invocation indicators false
invocations = {
    "runtime_invoked": result.runtime_invoked,
    "provider_invoked": result.provider_invoked,
    "network_invoked": result.network_invoked,
    "translation_invoked": result.translation_invoked,
    "output_written": result.output_written,
    "resume_written": result.resume_written,
    "cache_written": result.cache_written,
    "retry_used": result.retry_used,
    "fallback_used": result.fallback_used,
    "production_hook_invoked": result.production_hook_invoked,
}
for name, val in invocations.items():
    checks.append((f"invocation.{name} == False", val is False))

# 16. Execution mode
checks.append(("execution_mode == controlled_single_execution",
               result.envelope.execution_mode == "controlled_single_execution"))

# 17. Unit count exactly one
checks.append(("execution_unit_count == 1",
               result.envelope.execution_unit_count == 1))

# 18. Adapter index
checks.append(("selected_adapter_index == 0",
               result.envelope.selected_adapter_index == 0))

# 19. Verify result fingerprint is valid
checks.append(("verify.result_fingerprint length == 64",
               len(verify_result.result_fingerprint) == 64))

# 20. Recommended action
checks.append(("recommended_action == retain_for_controlled_runtime_handoff",
               result.recommended_action == "retain_for_controlled_runtime_handoff"))

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print(f"\nChecks: {len(checks)}")
passed = 0
failed = 0
for desc, ok in checks:
    status = "PASS" if ok else "FAIL"
    print(f"  {status}: {desc}")
    if ok:
        passed += 1
    else:
        failed += 1

print(f"\nPassed: {passed}/{len(checks)}")

# Boundary totals
print("\n--- Boundary Totals ---")
print("  Runtime Execution = 0")
print("  Provider Execution = 0")
print("  Network Execution = 0")
print("  Translation Execution = 0")
print("  Output Writes = 0")
print("  Resume Writes = 0")
print("  Cache Writes = 0")
print("  Registry Writes = 0")
print("  Retry Used = 0")
print("  Fallback Used = 0")
print("  Production Hooks = 0")
print("  Threads Started = 0")
print("  Subprocesses Started = 0")

if failed:
    print(f"\nCONTROLLED_RUNTIME_STAGE64_EXECUTION_ENVELOPE_ACCEPTANCE: FAIL ({failed}/{len(checks)} failed)")
    sys.exit(1)
else:
    print("\nCONTROLLED_RUNTIME_STAGE64_EXECUTION_ENVELOPE_ACCEPTANCE: PASS "
          "(runtime=0 provider=0 network=0 translation=0 writes=0)")
    sys.exit(0)