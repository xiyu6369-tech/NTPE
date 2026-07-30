#!/usr/bin/env python3
"""
RM-4.2A Safe Migration Execution
Only moves items verified as having ZERO imports from tests/ or core/.
Uses git mv for proper git tracking.
"""
import os
import subprocess
import json
import sys

ROOT = 'd:/Python/NTPE'
move_log = []
errors = []

def run_git_mv(src, dst):
    """Execute git mv, return True on success."""
    result = subprocess.run(
        ['git', 'mv', src, dst],
        capture_output=True, text=True,
        cwd=ROOT
    )
    if result.returncode != 0:
        errors.append(f'git mv {src} -> {dst}: {result.stderr.strip()}')
        return False
    move_log.append({
        'source': src,
        'destination': dst,
        'status': 'MOVED',
        'type': 'directory' if os.path.isdir(os.path.join(ROOT, src)) else 'file'
    })
    print(f'  MOVED: {src} -> {dst}')
    return True

def mkdir(path):
    full = os.path.join(ROOT, path)
    os.makedirs(full, exist_ok=True)

def exists_in_root(path):
    return os.path.exists(os.path.join(ROOT, path))

errors = []

# Create archive structure
for s in [
    'archive/historical',
    'archive/lts_duplicates',
    'archive/legacy',
    'archive/legacy_ui_safe',
    'archive/legacy_config',
    'archive/release_artifacts',
    'archive/translation_history',
    'archive/stage_tests',
    'archive/one_shot_creation',
    'archive/data_artifacts',
]:
    mkdir(s)

# ============================================================
# CONFIRMED SAFE — ZERO imports from tests/ or core/
# ============================================================

# --- Historical/Analysis Directories ---
historical = ['analysis', 'audits', 'memory', 'quality_corpus', 'quality_reports', 'reports', 'sessions']
for d in historical:
    if exists_in_root(d):
        run_git_mv(d, f'archive/historical/{d}')

# --- Legacy data/config ---
for d, dest in [
    ('data', 'archive/legacy/data'),
    ('examples', 'archive/legacy/examples'),
    ('rules', 'archive/legacy_config/rules'),
    ('gui', 'archive/legacy_ui_safe/gui'),
]:
    if exists_in_root(d):
        run_git_mv(d, dest)

# --- prompt_packages ---
if exists_in_root('prompt_packages'):
    run_git_mv('prompt_packages', 'archive/legacy_config/prompt_packages')

# --- LTS duplicate directories ---
lts_dirs = [
    'lts_rc_compatibility', 'lts_rc_final_validation', 'lts_rc_freeze',
    'lts_rc_performance', 'lts_rc_quality', 'lts_rc_regression',
    'lts_release_candidate', 'lts_runtime_freeze',
    'lts_stable_complete', 'lts_stable_finalization', 'lts_stable_preparation',
]
for d in lts_dirs:
    if exists_in_root(d):
        run_git_mv(d, f'archive/lts_duplicates/{d}')

# --- release/ directory ---
if exists_in_root('release'):
    run_git_mv('release', 'archive/release_artifacts/release')

# --- translation_cache ---
if exists_in_root('translation_cache'):
    run_git_mv('translation_cache', 'archive/translation_history/translation_cache')

# --- LTS root scripts ---
lts_scripts = [f for f in os.listdir(ROOT) if f.startswith('ntpe_lts_') and f.endswith('.py')]
for f in sorted(lts_scripts):
    if exists_in_root(f):
        run_git_mv(f, f'archive/lts_duplicates/{f}')

# --- One-shot creation scripts ---
create_scripts = [f for f in os.listdir(ROOT) if f.startswith('create_') and f.endswith('.py')]
for f in sorted(create_scripts):
    if exists_in_root(f):
        run_git_mv(f, f'archive/one_shot_creation/{f}')

# --- Data override JSON files ---
data_overrides = [f for f in os.listdir(ROOT) if f.endswith('_override.json')]
for f in sorted(data_overrides):
    if exists_in_root(f):
        run_git_mv(f, f'archive/data_artifacts/{f}')

# ============================================================
# REPORT
# ============================================================
print(f'\n=== RM-4.2A Execution Summary ===')
print(f'Total moved: {len(move_log)}')
print(f'Errors: {len(errors)}')
if errors:
    for e in errors:
        print(f'  ERR: {e}')

# Save mapping
mapping = {
    'batch': 'RM-4.2A',
    'total_moved': len(move_log),
    'errors': len(errors),
    'error_details': errors,
    'move_mapping': move_log,
}
with open(os.path.join(ROOT, 'docs/governance/migration/RM_4_2A_EXECUTION_LOG.json'), 'w', encoding='utf-8') as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
print(f'\nExecution log saved: docs/governance/migration/RM_4_2A_EXECUTION_LOG.json')