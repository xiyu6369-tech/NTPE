import subprocess

result = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True, cwd='D:/Python/NTPE')
changed_files = {f.strip() for f in result.stdout.strip().split('\n') if f.strip()}

# Missing R1-B test files from R1-B report
expected_r1_b_tests = {
    'tests/integration/translation_engine_v700_stage109_real_provider_execution_preflight_contract_test.py',
    'tests/integration/translation_engine_v700_stage108_fake_transport_end_to_end_freeze_test.py',
    'tests/integration/translation_engine_v700_stage107_provider_evidence_artifact_pipeline_test.py',
    'tests/integration/translation_engine_v700_stage106_authorized_provider_execution_cli_test.py',
    'tests/integration/translation_engine_v700_stage104_real_provider_invocation_boundary_contract_test.py',
    'tests/integration/translation_engine_v710_stage117_quality_framework_integration_test.py',
}

print("Missing from diff:")
for f in expected_r1_b_tests:
    if f not in changed_files:
        print(f"  MISSING: {f}")
    else:
        print(f"  PRESENT: {f}")

# Check R1-B fixtures (untracked)
r1_b_fixtures = {
    'tests/fixtures/tic_batch7/quality_gate_context.json',
    'tests/fixtures/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION.json',
    'tests/fixtures/te_v7_stage09/TE_V7_STAGE09_BASELINE.json',
    'tests/fixtures/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json',
}

print("\nR1-B fixtures (untracked):")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd='D:/Python/NTPE')
untracked = {line[3:].strip() for line in result.stdout.strip().split('\n') if line.startswith('??')}
for f in r1_b_fixtures:
    if f in untracked:
        print(f"  UNTRACKED: {f}")
    else:
        print(f"  NOT FOUND: {f}")

# Check R1-D, R1-INVENTORY (untracked)
r1_d_untracked = {
    'docs/governance/repository/P0_FINAL_12_FINAL_GLOBAL_MIGRATION_VERIFICATION.md',
    'artifacts/P0_FINAL_12_FINAL_Global_Migration_Verification_Report.json',
}
print("\nR1-D (untracked):")
for f in r1_d_untracked:
    if f in untracked:
        print(f"  UNTRACKED: {f}")
    else:
        print(f"  NOT FOUND: {f}")

r1_inventory = {'docs/governance/repository/P0_FINAL_12_R1_INVENTORY_REPORT.md'}
print("\nR1-INVENTORY (untracked):")
for f in r1_inventory:
    if f in untracked:
        print(f"  UNTRACKED: {f}")
    else:
        print(f"  NOT FOUND: {f}")

# Check R1-C preserved
r1_c_preserved = {'tools/rm_3_2_validate_classifications.py'}
print("\nR1-C-PRESERVED:")
for f in r1_c_preserved:
    if f in changed_files:
        print(f"  IN DIFF: {f}")
    elif f in untracked:
        print(f"  UNTRACKED: {f}")
    else:
        print(f"  NOT CHANGED: {f}")