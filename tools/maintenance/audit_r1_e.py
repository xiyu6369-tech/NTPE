import subprocess
import json
from collections import Counter

# Get all changed files
result = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True, cwd='D:/Python/NTPE')
changed_files = {f.strip() for f in result.stdout.strip().split('\n') if f.strip()}

# Get untracked files
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, cwd='D:/Python/NTPE')
untracked = {line[3:].strip() for line in result.stdout.strip().split('\n') if line.startswith('??')}

# R1-A expected files
r1_a_files = {
    'core/adaptive_context_authorized_provider_cli/report_path.py',
    'core/adaptive_context_controlled_provider_retry/config.py',
    'core/adaptive_context_controlled_provider_retry/report.py',
    'core/adaptive_context_provider_evidence_pipeline/report.py',
    'core/adaptive_context_provider_execution_freeze/report.py',
    'core/adaptive_context_provider_session_cli/harness.py',
    'core/adaptive_context_real_provider_preflight/validator.py',
    'core/adaptive_context_single_real_invocation/report.py',
    'core/translation_intelligence_corpus/inventory.py',
    'core/translation_intelligence_corpus/alignment.py',
    'core/prompt_verification_canary_stage1257/framework.py',
    'core/prompt_contract_verification_canary/framework.py',
    'core/prompt_contract_verification_canary/candidate_structural_canary.py',
    'core/translation_quality_provider_canary/framework.py',
}

# R1-B test files (actually modified)
r1_b_test_files = {
    'tests/integration/tic_batch7_offline_translation_quality_gate_test.py',
    'tests/integration/tic_batch5_historical_human_evidence_expansion_test.py',
    'tests/integration/translation_engine_v700_stage103_controlled_provider_session_cli_harness_test.py',
    'tests/integration/translation_engine_v700_stage102_controlled_provider_benchmark_session_test.py',
    'tests/integration/translation_engine_v700_stage101_provider_timing_evidence_adapter_test.py',
    'tests/integration/translation_engine_v700_stage1010_single_real_provider_invocation_test.py',
    'tests/integration/translation_engine_v700_stage10101_provider_timeout_controlled_retry_test.py',
    'tests/integration/tic_batch1_translation_corpus_inventory_test.py',
}

# R1-B fixtures
r1_b_fixtures_tracked = {
    'tests/fixtures/tic_batch5/HISTORICAL_HUMAN_EVIDENCE_EXPANSION.json',
}
r1_b_fixtures_untracked = {
    'tests/fixtures/tic_batch7/quality_gate_context.json',
    'tests/fixtures/te_v7_stage09/TE_V7_STAGE09_BASELINE.json',
    'tests/fixtures/te_v7_stage1010/TE_V7_STAGE1010_SINGLE_REAL_INVOCATION.json',
}

# R1-C files
r1_c_files = {
    'tools/provider_controls/ntpe_single_real_provider_invocation.py',
    'tools/provider_controls/ntpe_controlled_real_provider_retry.py',
    'tools/generate_te_v720_stage1254_prompt_contract_preservation.py',
    'tools/generate_te_v720_stage1258_candidate_structural_verification_canary.py',
    'tools/generate_te_v720_stage1258a_candidate_structural_failure_sealing.py',
    'tools/generate_te_v720_stage1257a_execution_evidence_sealing.py',
    'tools/generate_te_v720_stage1256a_claim_safe_corpus_binding_remediation.py',
    'tools/generate_te_v720_stage1259_name_resolution_contract_remediation.py',
}

# R1-D deliverables (untracked)
r1_d_files = {
    'docs/governance/repository/P0_FINAL_12_FINAL_GLOBAL_MIGRATION_VERIFICATION.md',
    'artifacts/P0_FINAL_12_FINAL_Global_Migration_Verification_Report.json',
}

# R1-INVENTORY (untracked)
r1_inventory = {
    'docs/governance/repository/P0_FINAL_12_R1_INVENTORY_REPORT.md',
}

# R1-C preserved (no changes)
r1_c_preserved = {
    'tools/rm_3_2_validate_classifications.py',
}

# Classify
classified = {}
for f in changed_files:
    if f in r1_a_files:
        classified[f] = 'R1-A'
    elif f in r1_b_test_files:
        classified[f] = 'R1-B'
    elif f in r1_b_fixtures_tracked:
        classified[f] = 'R1-B'
    elif f in r1_c_files:
        classified[f] = 'R1-C'
    elif f.startswith('artifacts/'):
        classified[f] = 'PROTECTED_WORKTREE'
    elif f.startswith('tools/one_shots/'):
        classified[f] = 'PROTECTED_WORKTREE'
    elif f.startswith('tests/literary/outputs/'):
        classified[f] = 'PROTECTED_WORKTREE'
    elif f == 'docs/governance/repository/P0_REPOSITORY_FINAL_CLEANUP_BATCH_D_RECONCILIATION.md':
        classified[f] = 'PROTECTED_WORKTREE'
    else:
        classified[f] = 'UNKNOWN'

# Classify untracked
for f in untracked:
    if f in r1_b_fixtures_untracked:
        classified[f] = 'R1-B'
    elif f in r1_d_files:
        classified[f] = 'R1-D'
    elif f in r1_inventory:
        classified[f] = 'R1-INVENTORY'
    elif f.startswith('tests/fixtures/'):
        classified[f] = 'R1-B'
    elif f.startswith('tools/monitoring/'):
        classified[f] = 'UNKNOWN'
    elif f.startswith('artifacts/DUMMY-'):
        classified[f] = 'UNKNOWN'
    elif f.startswith('artifacts/P0_FINAL_') and 'VERIFICATION' in f:
        classified[f] = 'R1-D'
    elif f.startswith('docs/governance/repository/P0_FINAL_') and 'RECONCILIATION' in f:
        classified[f] = 'PROTECTED_WORKTREE'
    elif f.startswith('docs/governance/repository/P0_FINAL_') and 'PREFLIGHT' in f:
        classified[f] = 'PROTECTED_WORKTREE'
    elif f.startswith('docs/governance/rm8/'):
        classified[f] = 'PROTECTED_WORKTREE'
    else:
        classified[f] = 'UNKNOWN'

# Count
counts = Counter(classified.values())
print("=== CLASSIFICATION SUMMARY ===")
for cat, count in sorted(counts.items()):
    print(f"  {cat}: {count}")

# Safe R1 commit candidates (tracked + untracked R1 files)
safe_r1 = []
for f, cat in classified.items():
    if cat in ['R1-A', 'R1-B', 'R1-C', 'R1-D', 'R1-INVENTORY']:
        safe_r1.append(f)

unsafe = []
for f, cat in classified.items():
    if cat in ['PROTECTED_WORKTREE', 'UNKNOWN']:
        unsafe.append(f)

print(f"\n=== SAFE R1 COMMIT CANDIDATES ({len(safe_r1)}) ===")
for f in sorted(safe_r1):
    cat = classified[f]
    print(f"  [{cat}] {f}")

print(f"\n=== UNSAFE TO STAGE ({len(unsafe)}) ===")
for f in sorted(unsafe):
    cat = classified.get(f, 'UNCLASSIFIED')
    print(f"  [{cat}] {f}")

# Check OVERLAP - any R1 file also showing as protected worktree?
overlap = []
for f in r1_a_files | r1_b_test_files | r1_b_fixtures_tracked | r1_c_files:
    if f in classified and classified[f] == 'PROTECTED_WORKTREE':
        overlap.append(f)

print(f"\n=== OVERLAP (R1 file classified as Protected) ===")
if overlap:
    for f in overlap:
        print(f"  {f}")
else:
    print("  None")

# Check for R1 files not in diff or untracked (no changes)
print("\n=== R1 FILES WITH NO CHANGES ===")
all_r1_expected = r1_a_files | r1_b_test_files | r1_b_fixtures_tracked | r1_b_fixtures_untracked | r1_c_files
for f in sorted(all_r1_expected):
    if f not in changed_files and f not in untracked:
        print(f"  NO CHANGE: {f}")

# Save full classification to JSON
output = {
    "baseline": {
        "branch": "main",
        "head": "53e04767f9a1012641152e96786011fbb3b0e466",
        "origin_main": "53e04767f9a1012641152e96786011fbb3b0e466",
    },
    "total_changed_paths": len(changed_files),
    "total_untracked_paths": len(untracked),
    "classification_counts": dict(counts),
    "r1_a": [f for f, c in classified.items() if c == 'R1-A'],
    "r1_b": [f for f, c in classified.items() if c == 'R1-B'],
    "r1_c": [f for f, c in classified.items() if c == 'R1-C'],
    "r1_d": [f for f, c in classified.items() if c == 'R1-D'],
    "r1_inventory": [f for f, c in classified.items() if c == 'R1-INVENTORY'],
    "protected_worktree": [f for f, c in classified.items() if c == 'PROTECTED_WORKTREE'],
    "unknown": [f for f, c in classified.items() if c == 'UNKNOWN'],
    "safe_commit_candidates": sorted(safe_r1),
    "unsafe_to_stage": sorted(unsafe),
    "overlap": overlap,
    "r1_files_no_changes": [f for f in sorted(all_r1_expected) if f not in changed_files and f not in untracked],
}

with open('D:/Python/NTPE/artifacts/P0_FINAL_12_R1_E_Commit_Boundary_Audit_Report.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nReport saved to artifacts/P0_FINAL_12_R1_E_Commit_Boundary_Audit_Report.json")