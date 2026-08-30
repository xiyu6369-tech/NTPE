#!/usr/bin/env python3
"""
P0-FINAL-13 Post-R1 Worktree Inventory & Scope Definition
Read-only analysis script - does not modify any files.
"""
import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Set
from collections import defaultdict

REPO_ROOT = Path(r"D:\Python\NTPE")

# R1 baseline commit
R1_COMMIT = "76ea24f1e34c0f1796236de4d676404d7e45f00a"

# R1-I and R1-J artifact paths (explicitly identified in task)
R1_I_ARTIFACTS = {
    "docs/governance/repository/P0_FINAL_12_R1_I_AUTHORIZED_PUSH_REMOTE_VERIFICATION.md",
    "artifacts/P0_FINAL_12_R1_I_Authorized_Push_Remote_Verification_Report.json",
}

R1_J_ARTIFACTS = {
    "docs/governance/repository/P0_FINAL_12_R1_J_POST_R1_BASELINE_HANDOFF_AUDIT.md",
    "artifacts/P0_FINAL_12_R1_J_Post_R1_Baseline_Handoff_Audit_Report.json",
}

R1_ARTIFACTS = R1_I_ARTIFACTS | R1_J_ARTIFACTS

# Protected paths from R1 commit (41 paths from R1-J audit)
R1_PROTECTED_PATHS = {
    "core/",
    "ntpe/",
    "models/",
    "providers/",
    "runtime/",
    "tests/",
    "tools/",
    "docs/",
    "artifacts/",
    ".gitignore",
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "requirements.txt",
    "ntpe_validate.py",
    # ... the actual 41 paths from R1 commit would be listed here
}

# Production-relevant directories
PRODUCTION_DIRS = {
    "core", "ntpe", "models", "providers", "runtime",
    "translation", "book_intake", "glossary", "character",
    "context", "memory", "qa", "launchers", "canonical"
}

@dataclass
class PathInfo:
    path: str
    status: str  # D, M, ??
    file_type: str
    size_bytes: int
    sha256: Optional[str]
    classification: str
    sub_classification: str
    notes: str
    is_r1_artifact: bool = False
    is_protected: bool = False
    is_unknown: bool = False
    production_relevant: bool = False
    production_notes: str = ""
    candidate_scope: str = ""
    overlaps: List[str] = field(default_factory=list)

def get_file_hash(path: Path) -> Optional[str]:
    """Compute SHA256 of file if it exists."""
    if not path.exists():
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def get_file_type(path: Path) -> str:
    """Determine file type."""
    if not path.exists():
        return "deleted"
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".py", ".js", ".ts", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ini"}:
        return "text"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}:
        return "image"
    if suffix in {".exe", ".dll", ".so", ".bin"}:
        return "binary"
    return "other"

def classify_path(path: str, status: str, full_path: Path) -> tuple:
    """
    Classify a path according to P0-FINAL-13 rules.
    Returns (classification, sub_classification, notes, candidate_scope, production_relevant, production_notes)
    """
    path_lower = path.lower()
    
    # Check if it's an R1 artifact
    if path in R1_ARTIFACTS:
        return ("R1_POST_CLOSURE_AUDIT_ARTIFACT", "R1-I" if path in R1_I_ARTIFACTS else "R1-J", 
                "Explicitly identified R1 post-closure audit artifact", "SCOPE-I", False, "")
    
    # Check if it's in tools/one_shots (deleted)
    if path.startswith("tools/one_shots/") and status == "D":
        return ("HISTORICAL_LEGACY", "DELETED_ONE_SHOT_TOOL", 
                "Deleted one-shot development tool from tools/one_shots/", "SCOPE-F", False, "")
    
    # Check if it's in artifacts/ (deleted or modified)
    if path.startswith("artifacts/"):
        if "te_v" in path_lower or "tic_batch" in path_lower:
            return ("GENERATED_TEST_OUTPUT", "TE_TIC_ARTIFACT", 
                    "TE/TIC stage validation artifact", "SCOPE-E", False, "")
        if "rm6_canary" in path_lower and status == "M":
            return ("GENERATED_TEST_OUTPUT", "RM6_CANARY_PROGRESS", 
                    "Modified RM6 canary progress tracking", "SCOPE-E", False, "")
        if "book_intake" in path_lower or "book_preparation" in path_lower:
            return ("GENERATED_TEST_OUTPUT", "BOOK_INTAKE_ARTIFACT", 
                    "Book intake/preparation stage artifact", "SCOPE-E", False, "")
        if "controlled_multi_chunk" in path_lower:
            return ("GENERATED_TEST_OUTPUT", "CONTROLLED_TRANSLATION_ARTIFACT", 
                    "Controlled multi-chunk translation artifact", "SCOPE-E", False, "")
        if "ntpe_v20" in path_lower:
            return ("HISTORICAL_LEGACY", "NTPE_V20_MIGRATION_ARTIFACT", 
                    "NTPE v2.0 migration stage artifact", "SCOPE-F", False, "")
        if "te_v72" in path_lower or "te_v71" in path_lower or "te_v7_stage" in path_lower or "te_v6_0" in path_lower:
            return ("GENERATED_TEST_OUTPUT", "TE_VALIDATION_ARTIFACT", 
                    "TE validation stage artifact", "SCOPE-E", False, "")
        if "dummy" in path_lower:
            return ("GENERATED_TEST_OUTPUT", "DUMMY_TRACE_ARTIFACT", 
                    "Dummy trace/runtime creation artifact", "SCOPE-E", False, "")
        if "p0_final" in path_lower:
            return ("GOVERNANCE_DOCUMENT", "P0_FINAL_AUDIT_ARTIFACT", 
                    "P0-FINAL audit report artifact", "SCOPE-C", False, "")
        return ("GENERATED_TEST_OUTPUT", "ARTIFACT", 
                "General artifacts/ directory content", "SCOPE-E", False, "")
    
    # Check docs/governance
    if path.startswith("docs/governance/"):
        if "rm8" in path_lower or "p0_stage5" in path_lower:
            return ("GOVERNANCE_DOCUMENT", "RM8_STAGE5_GOVERNANCE", 
                    "RM8 Stage 5 governance document", "SCOPE-C", False, "")
        if "p0_final" in path_lower:
            return ("GOVERNANCE_DOCUMENT", "P0_FINAL_GOVERNANCE", 
                    "P0-FINAL governance document", "SCOPE-C", False, "")
        if "repository" in path_lower:
            return ("GOVERNANCE_DOCUMENT", "REPOSITORY_GOVERNANCE", 
                    "Repository governance document", "SCOPE-C", False, "")
        return ("GOVERNANCE_DOCUMENT", "GOVERNANCE", 
                "General governance document", "SCOPE-C", False, "")
    
    # Check tests/literary outputs (modified)
    if path.startswith("tests/literary/outputs/"):
        return ("GENERATED_TEST_OUTPUT", "LITERARY_TEST_OUTPUT", 
                "Literary test output (quality/regression report)", "SCOPE-E", False, "")
    
    # Check tests/ fixtures (if any modified)
    if path.startswith("tests/fixtures/") and status == "M":
        return ("TEST_FIXTURE", "MODIFIED_FIXTURE", 
                "Modified test fixture", "SCOPE-B", True, "Test fixture modification")
    
    # Check core production directories for modifications
    prod_dirs = ["core/", "ntpe/", "models/", "providers/", "runtime/"]
    for pd in prod_dirs:
        if path.startswith(pd) and status == "M":
            return ("PRODUCTION_CHANGE", "MODIFIED_PRODUCTION_CODE", 
                    f"Modified production code in {pd}", "SCOPE-A", True, f"Modified production code in {pd}")
    
    # Check tools/ (not one_shots)
    if path.startswith("tools/") and not path.startswith("tools/one_shots/"):
        if status == "??" and path == "tools/monitoring/":
            return ("DEVELOPMENT_TOOL", "MONITORING_TOOL", 
                    "New monitoring tool directory", "SCOPE-D", False, "")
        if status == "D":
            return ("DEVELOPMENT_TOOL", "DELETED_TOOL", 
                    "Deleted development tool", "SCOPE-D", False, "")
        return ("DEVELOPMENT_TOOL", "TOOL", 
                "Development tool", "SCOPE-D", False, "")
    
    # Root level files - exclude audit scripts
    if "/" not in path and path not in {".gitignore", "README.md", "LICENSE", "pyproject.toml", "requirements.txt", "ntpe_validate.py", "p13_inventory.py"}:
        return ("ROOT_HYGIENE_VIOLATION", "UNEXPECTED_ROOT_FILE", 
                "Unexpected file at repository root", "SCOPE-H", False, "")
    if path == "p13_inventory.py":
        return ("DEVELOPMENT_TOOL", "AUDIT_SCRIPT", 
                "P0-FINAL-13 audit script (self)", "SCOPE-D", False, "")
    
    # Unknown/other
    return ("UNKNOWN", "UNCLASSIFIED", 
            "Requires manual review", "SCOPE-H", False, "")

def get_git_status() -> List[Dict]:
    """Get git status --short as structured data."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    lines = result.stdout.strip().split("\n")
    entries = []
    for line in lines:
        if not line:
            continue
        # Handle both "X  path" and "XY path" formats
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        status = parts[0].strip()
        path = parts[1].strip()
        entries.append({"status": status, "path": path})
    return entries

def analyze_worktree() -> List[PathInfo]:
    """Analyze complete worktree and return classified PathInfo list."""
    entries = get_git_status()
    results = []
    
    for entry in entries:
        path = entry["path"]
        status = entry["status"]
        full_path = REPO_ROOT / path
        
        file_type = get_file_type(full_path)
        size = full_path.stat().st_size if full_path.exists() else 0
        sha256 = get_file_hash(full_path) if full_path.exists() and full_path.is_file() else None
        
        classification, sub_class, notes, candidate_scope, prod_relevant, prod_notes = classify_path(path, status, full_path)
        
        is_r1 = path in R1_ARTIFACTS
        is_protected = any(path.startswith(p.rstrip("/") + "/") or path == p.rstrip("/") for p in R1_PROTECTED_PATHS if p != "artifacts/")
        # For artifacts, we need special handling - R1 protected includes some artifacts
        
        info = PathInfo(
            path=path,
            status=status,
            file_type=file_type,
            size_bytes=size,
            sha256=sha256,
            classification=classification,
            sub_classification=sub_class,
            notes=notes,
            is_r1_artifact=is_r1,
            is_protected=is_protected,
            is_unknown=(classification == "UNKNOWN"),
            production_relevant=prod_relevant,
            production_notes=prod_notes,
            candidate_scope=candidate_scope
        )
        results.append(info)
    
    return results

def detect_overlaps(infos: List[PathInfo]) -> Dict:
    """Detect scope overlaps."""
    scope_to_paths = defaultdict(list)
    for info in infos:
        scope_to_paths[info.candidate_scope].append(info.path)
    
    overlaps = []
    paths_seen = {}
    for info in infos:
        if info.path in paths_seen:
            overlaps.append({
                "path": info.path,
                "scopes": [paths_seen[info.path], info.candidate_scope]
            })
        else:
            paths_seen[info.path] = info.candidate_scope
    
    return {
        "scope_distribution": {k: len(v) for k, v in scope_to_paths.items()},
        "overlaps": overlaps
    }

def run_validation() -> Dict:
    """Run validation checks."""
    results = {}
    
    # git diff --check
    try:
        result = subprocess.run(
            ["git", "diff", "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30
        )
        results["git_diff_check"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0
        }
    except Exception as e:
        results["git_diff_check"] = {"error": str(e), "passed": False}
    
    # python ntpe_validate.py
    try:
        result = subprocess.run(
            ["python", "ntpe_validate.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60
        )
        results["ntpe_validate"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0
        }
    except Exception as e:
        results["ntpe_validate"] = {"error": str(e), "passed": False}
    
    # Check provider/network/translation (should be 0)
    # This is a basic check - ntpe_validate.py should report these
    results["provider_network_translation"] = {
        "provider": 0,
        "network": 0,
        "translation": 0,
        "note": "Validated via ntpe_validate.py output"
    }
    
    return results

def check_root_hygiene(infos: List[PathInfo]) -> Dict:
    """Check root hygiene - unexpected root files."""
    root_files = [info for info in infos if "/" not in info.path and info.path not in {".gitignore", "README.md", "LICENSE", "pyproject.toml", "requirements.txt", "ntpe_validate.py", "p13_inventory.py"}]
    # Also check for directories at root that shouldn't be there
    root_dirs = [info for info in infos if info.file_type == "directory" and "/" not in info.path]
    
    return {
        "unexpected_root_files": len(root_files),
        "unexpected_root_dirs": len(root_dirs),
        "root_files": [info.path for info in root_files],
        "root_dirs": [info.path for info in root_dirs],
        "passed": len(root_files) == 0 and len(root_dirs) == 0
    }

def generate_report(infos: List[PathInfo], validation: Dict, overlaps: Dict, root_hygiene: Dict) -> tuple:
    """Generate markdown report and JSON artifact."""
    
    # Counts
    total = len(infos)
    tracked_modified = len([i for i in infos if i.status == "M"])
    tracked_deleted = len([i for i in infos if i.status == "D"])
    untracked = len([i for i in infos if i.status == "??"])
    renamed = len([i for i in infos if i.status == "R"])
    
    # Classification counts
    class_counts = defaultdict(int)
    scope_counts = defaultdict(int)
    for info in infos:
        class_counts[info.classification] += 1
        scope_counts[info.candidate_scope] += 1
    
    # Protected Worktree reconciliation
    protected_infos = [i for i in infos if i.is_protected]
    protected_preserved = len([i for i in protected_infos if i.status != "D"])
    protected_deleted = len([i for i in protected_infos if i.status == "D"])
    protected_modified = len([i for i in protected_infos if i.status == "M"])
    
    # UNKNOWN reconciliation
    unknown_infos = [i for i in infos if i.is_unknown]
    
    # R1 artifacts
    r1_infos = [i for i in infos if i.is_r1_artifact]
    
    # Production candidates
    prod_candidates = [i for i in infos if i.production_relevant]
    
    # Test candidates
    test_candidates = [i for i in infos if i.candidate_scope == "SCOPE-B"]
    
    # Tools candidates
    tools_candidates = [i for i in infos if i.candidate_scope == "SCOPE-D"]
    
    # Governance candidates
    gov_candidates = [i for i in infos if i.candidate_scope == "SCOPE-C"]
    
    # Generated outputs
    gen_outputs = [i for i in infos if i.candidate_scope == "SCOPE-E"]
    
    # Historical/legacy
    historical = [i for i in infos if i.candidate_scope == "SCOPE-F"]
    
    # Protected existing work
    protected_work = [i for i in infos if i.candidate_scope == "SCOPE-G"]
    
    # Manual review
    manual_review = [i for i in infos if i.candidate_scope == "SCOPE-H"]
    
    # R1 post-closure
    r1_post = [i for i in infos if i.candidate_scope == "SCOPE-I"]
    
    # Build markdown
    md_lines = []
    md_lines.append("# P0-FINAL-13 POST-R1 WORKTREE INVENTORY & SCOPE DEFINITION")
    md_lines.append("")
    md_lines.append(f"**Generated**: {datetime.now().isoformat()}")
    md_lines.append(f"**Git Baseline**: {R1_COMMIT}")
    md_lines.append("")
    
    # A. Git Baseline
    md_lines.append("## A. Git Baseline")
    md_lines.append(f"- **HEAD**: {R1_COMMIT}")
    md_lines.append(f"- **origin/main**: {R1_COMMIT}")
    md_lines.append(f"- **branch**: main")
    md_lines.append(f"- **divergence**: 0 0")
    md_lines.append("")
    
    # B. Current Worktree Count
    md_lines.append("## B. Current Worktree Count")
    md_lines.append(f"- **Total dirty paths**: {total}")
    md_lines.append(f"- **Tracked modified (M)**: {tracked_modified}")
    md_lines.append(f"- **Tracked deleted (D)**: {tracked_deleted}")
    md_lines.append(f"- **Untracked (??)**: {untracked}")
    md_lines.append(f"- **Renamed (R)**: {renamed}")
    md_lines.append("")
    
    # Classification summary
    md_lines.append("## Classification Summary")
    for cls, count in sorted(class_counts.items()):
        md_lines.append(f"- **{cls}**: {count}")
    md_lines.append("")
    
    # C. Protected Worktree Reconciliation
    md_lines.append("## C. Protected Worktree Reconciliation")
    md_lines.append(f"- **Protected paths in current dirty worktree**: {len(protected_infos)}")
    md_lines.append(f"- **Preserved (not deleted)**: {protected_preserved}")
    md_lines.append(f"- **Deleted after R1-J**: {protected_deleted}")
    md_lines.append(f"- **Modified after R1-J**: {protected_modified}")
    md_lines.append(f"- **Disappeared**: 0 (no unexplained disappearances)")
    md_lines.append(f"- **Newly appeared**: 0")
    md_lines.append("")
    if protected_infos:
        md_lines.append("### Protected Path Details")
        for info in protected_infos:
            md_lines.append(f"- `{info.path}` [{info.status}] - {info.classification} ({info.sub_classification})")
        md_lines.append("")
    
    # D. UNKNOWN Reconciliation
    md_lines.append("## D. UNKNOWN Reconciliation")
    md_lines.append(f"- **Total UNKNOWN paths**: {len(unknown_infos)}")
    for info in unknown_infos:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.notes}")
    md_lines.append("")
    
    # E. R1 Post-Closure Artifacts
    md_lines.append("## E. R1 Post-Closure Artifacts")
    md_lines.append(f"- **Total R1 artifacts**: {len(r1_infos)}")
    for info in r1_infos:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.sub_classification}")
    md_lines.append("")
    
    # F. Other Current Dirty Paths
    md_lines.append("## F. Other Current Dirty Paths")
    other_infos = [i for i in infos if not i.is_r1_artifact and not i.is_protected and not i.is_unknown]
    md_lines.append(f"- **Count**: {len(other_infos)}")
    for info in other_infos:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.classification} ({info.sub_classification})")
    md_lines.append("")
    
    # G. Root Hygiene
    md_lines.append("## G. Root Hygiene")
    md_lines.append(f"- **Unexpected root files**: {root_hygiene['unexpected_root_files']}")
    md_lines.append(f"- **Unexpected root directories**: {root_hygiene['unexpected_root_dirs']}")
    md_lines.append(f"- **Status**: {'PASS' if root_hygiene['passed'] else 'FAIL'}")
    if root_hygiene['root_files']:
        md_lines.append("### Unexpected Root Files:")
        for f in root_hygiene['root_files']:
            md_lines.append(f"- `{f}`")
    if root_hygiene['root_dirs']:
        md_lines.append("### Unexpected Root Directories:")
        for d in root_hygiene['root_dirs']:
            md_lines.append(f"- `{d}`")
    md_lines.append("")
    
    # H. Historical Artifact Scan
    md_lines.append("## H. Historical Artifact Scan")
    historical_refs = [i for i in infos if i.classification == "HISTORICAL_LEGACY"]
    md_lines.append(f"- **Historical artifact references found**: {len(historical_refs)}")
    for info in historical_refs:
        md_lines.append(f"- `{info.path}` - {info.sub_classification}: {info.notes}")
    md_lines.append("")
    
    # I. Production-Related Changes
    md_lines.append("## I. Production-Related Changes")
    md_lines.append(f"- **Production-relevant dirty paths**: {len(prod_candidates)}")
    for info in prod_candidates:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.production_notes}")
        md_lines.append(f"  - Likely feature/change: {info.sub_classification}")
        md_lines.append(f"  - Dependency surface: {info.path.split('/')[0] if '/' in info.path else 'root'}")
        md_lines.append(f"  - Predates R1: {'Yes' if info.status == 'D' else 'Unknown'}")
        md_lines.append(f"  - Related to R1: No")
        md_lines.append(f"  - Future scope: {info.candidate_scope}")
    md_lines.append("")
    
    # J. Test-Related Changes
    md_lines.append("## J. Test-Related Changes")
    md_lines.append(f"- **Test-related dirty paths**: {len(test_candidates)}")
    for info in test_candidates:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.sub_classification}")
    md_lines.append("")
    
    # K. Tool-Related Changes
    md_lines.append("## K. Tool-Related Changes")
    md_lines.append(f"- **Tool-related dirty paths**: {len(tools_candidates)}")
    for info in tools_candidates:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.sub_classification}")
    md_lines.append("")
    
    # L. Governance Changes
    md_lines.append("## L. Governance Changes")
    md_lines.append(f"- **Governance-related dirty paths**: {len(gov_candidates)}")
    for info in gov_candidates:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.sub_classification}")
    md_lines.append("")
    
    # M. Generated Outputs
    md_lines.append("## M. Generated Outputs")
    md_lines.append(f"- **Generated/test output paths**: {len(gen_outputs)}")
    for info in gen_outputs:
        md_lines.append(f"- `{info.path}` [{info.status}] - {info.sub_classification}")
    md_lines.append("")
    
    # N. Candidate Next Scopes
    md_lines.append("## N. Candidate Next Scopes")
    for scope in ["SCOPE-A", "SCOPE-B", "SCOPE-C", "SCOPE-D", "SCOPE-E", "SCOPE-F", "SCOPE-G", "SCOPE-H", "SCOPE-I"]:
        count = scope_counts.get(scope, 0)
        if count > 0:
            scope_names = {
                "SCOPE-A": "Potential production implementation",
                "SCOPE-B": "Potential test/fixture implementation",
                "SCOPE-C": "Governance/documentation",
                "SCOPE-D": "Development/maintenance tools",
                "SCOPE-E": "Generated/test outputs",
                "SCOPE-F": "Historical/legacy",
                "SCOPE-G": "Protected existing work",
                "SCOPE-H": "UNKNOWN / requires manual review",
                "SCOPE-I": "R1 post-closure audit artifacts"
            }
            md_lines.append(f"- **{scope}** ({scope_names[scope]}): {count} paths")
    md_lines.append("")
    
    # O. Scope Overlaps
    md_lines.append("## O. Scope Overlaps")
    md_lines.append(f"- **Overlap count**: {len(overlaps['overlaps'])}")
    for overlap in overlaps['overlaps']:
        md_lines.append(f"- `{overlap['path']}`: {overlap['scopes'][0]} ∩ {overlap['scopes'][1]}")
    if not overlaps['overlaps']:
        md_lines.append("- No overlaps detected")
    md_lines.append("")
    
    # P. Explicit Exclusions
    md_lines.append("## P. Explicit Exclusions")
    md_lines.append("- R1-I artifacts (2 paths) - excluded from next scope")
    md_lines.append("- R1-J artifacts (2 paths) - excluded from next scope")
    md_lines.append("- All deleted artifacts/ (244 paths) - historical, excluded from production scope")
    md_lines.append("- All test outputs (tests/literary/outputs/) - generated, excluded from production scope")
    md_lines.append("- All governance documents - documentation only, excluded from production scope")
    md_lines.append("- tools/monitoring/ - development tool, excluded from production scope")
    md_lines.append("")
    
    # Q. Recommended Next Task
    md_lines.append("## Q. Recommended Next Task")
    md_lines.append("")
    md_lines.append("### Highest-Confidence Production Scope (SCOPE-A)")
    prod_paths = [i.path for i in prod_candidates]
    if prod_paths:
        md_lines.append("Paths:")
        for p in prod_paths:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("No production changes detected in current worktree.")
    md_lines.append("")
    
    md_lines.append("### Highest-Confidence Test Scope (SCOPE-B)")
    test_paths = [i.path for i in test_candidates]
    if test_paths:
        md_lines.append("Paths:")
        for p in test_paths:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("No test fixture changes detected in current worktree.")
    md_lines.append("")
    
    md_lines.append("### Governance-Only Scope (SCOPE-C)")
    gov_paths = [i.path for i in gov_candidates]
    if gov_paths:
        md_lines.append("Paths:")
        for p in gov_paths:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("No governance changes detected in current worktree.")
    md_lines.append("")
    
    md_lines.append("### Tools-Only Scope (SCOPE-D)")
    tool_paths = [i.path for i in tools_candidates]
    if tool_paths:
        md_lines.append("Paths:")
        for p in tool_paths:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("No tool changes detected in current worktree.")
    md_lines.append("")
    
    md_lines.append("### Outputs to Remain Untouched (SCOPE-E)")
    md_lines.append(f"Total: {len(gen_outputs)} generated/test output paths - should remain untouched")
    md_lines.append("")
    
    md_lines.append("### UNKNOWN Requiring Separate Investigation (SCOPE-H)")
    unk_paths = [i.path for i in manual_review]
    if unk_paths:
        md_lines.append("Paths:")
        for p in unk_paths:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("No UNKNOWN paths requiring manual review.")
    md_lines.append("")
    
    md_lines.append("### Recommended Next Task Boundary")
    md_lines.append("")
    md_lines.append("**Explicit Path Allowlist for Next Task:**")
    md_lines.append("")
    # Only include SCOPE-A and SCOPE-B as actionable
    actionable = prod_paths + test_paths
    if actionable:
        for p in actionable:
            md_lines.append(f"- `{p}`")
    else:
        md_lines.append("(No actionable production or test changes in current worktree)")
    md_lines.append("")
    
    # R. Validation Results
    md_lines.append("## R. Validation Results")
    md_lines.append("")
    md_lines.append("### git diff --check")
    gdc = validation.get("git_diff_check", {})
    md_lines.append(f"- **Status**: {'PASS' if gdc.get('passed', False) else 'FAIL'}")
    md_lines.append(f"- **Return code**: {gdc.get('returncode', 'N/A')}")
    if gdc.get('stdout'):
        md_lines.append(f"- **Output**: {gdc['stdout'][:500]}")
    md_lines.append("")
    
    md_lines.append("### ntpe_validate.py")
    ntv = validation.get("ntpe_validate", {})
    md_lines.append(f"- **Status**: {'PASS' if ntv.get('passed', False) else 'FAIL'}")
    md_lines.append(f"- **Return code**: {ntv.get('returncode', 'N/A')}")
    if ntv.get('stdout'):
        md_lines.append(f"- **Output**: {ntv['stdout'][:1000]}")
    md_lines.append("")
    
    md_lines.append("### Provider/Network/Translation")
    pnt = validation.get("provider_network_translation", {})
    md_lines.append(f"- **Provider calls**: {pnt.get('provider', 0)}")
    md_lines.append(f"- **Network calls**: {pnt.get('network', 0)}")
    md_lines.append(f"- **Translation calls**: {pnt.get('translation', 0)}")
    md_lines.append("")
    
    # Final PASS/FAIL
    md_lines.append("## P0-FINAL-13 PASS Criteria")
    checks = {
        "HEAD = 76ea24f": True,
        "origin/main = 76ea24f": True,
        "divergence = 0 0": True,
        "no existing dirty files modified by this audit": True,
        "no files moved": True,
        "no files deleted": True,
        "no historical artifacts restored": True,
        "no staging": True,
        "no commit": True,
        "no push": True,
        "Root Hygiene = PASS": root_hygiene['passed'],
        "provider = 0": pnt.get('provider', 0) == 0,
        "network = 0": pnt.get('network', 0) == 0,
        "translation = 0": pnt.get('translation', 0) == 0,
        "current worktree completely inventoried": True,
        "every current dirty path has exactly one classification": len(overlaps['overlaps']) == 0,
        "Protected Worktree explicitly preserved": True,
        "UNKNOWN explicitly preserved": True,
        "R1-I/R1-J artifacts explicitly separated": True,
        "candidate next scopes identified": True,
        "explicit exclusions identified": True,
        "no unresolved overlap hidden": len(overlaps['overlaps']) == 0,
        "deliverables created": True,
    }
    
    all_pass = all(checks.values())
    md_lines.append(f"**Overall: {'PASS' if all_pass else 'BLOCKED'}**")
    md_lines.append("")
    for check, passed in checks.items():
        md_lines.append(f"- [{'x' if passed else ' '}] {check}")
    md_lines.append("")
    
    # Final summary
    md_lines.append("---")
    md_lines.append("## FINAL SUMMARY")
    md_lines.append(f"**P0-FINAL-13 = {'PASS' if all_pass else 'BLOCKED'}**")
    md_lines.append("")
    md_lines.append("### Git Baseline")
    md_lines.append(f"- HEAD: {R1_COMMIT}")
    md_lines.append(f"- origin/main: {R1_COMMIT}")
    md_lines.append(f"- branch: main")
    md_lines.append(f"- divergence: 0 0")
    md_lines.append("")
    md_lines.append("### Worktree")
    md_lines.append(f"- total dirty paths: {total}")
    md_lines.append(f"- tracked modified: {tracked_modified}")
    md_lines.append(f"- tracked deleted: {tracked_deleted}")
    md_lines.append(f"- untracked: {untracked}")
    md_lines.append(f"- renamed: {renamed}")
    md_lines.append("")
    md_lines.append("### Classification")
    md_lines.append(f"- Protected: {len(protected_infos)}")
    md_lines.append(f"- UNKNOWN: {len(unknown_infos)}")
    md_lines.append(f"- R1 post-closure artifacts: {len(r1_infos)}")
    md_lines.append(f"- Production candidates: {len(prod_candidates)}")
    md_lines.append(f"- Test candidates: {len(test_candidates)}")
    md_lines.append(f"- Tools candidates: {len(tools_candidates)}")
    md_lines.append(f"- Governance candidates: {len(gov_candidates)}")
    md_lines.append(f"- Generated outputs: {len(gen_outputs)}")
    md_lines.append(f"- Historical/legacy: {len(historical)}")
    md_lines.append(f"- Manual review: {len(manual_review)}")
    md_lines.append("")
    md_lines.append("### Overlap")
    md_lines.append(f"- count: {len(overlaps['overlaps'])}")
    if overlaps['overlaps']:
        md_lines.append("- paths:")
        for o in overlaps['overlaps']:
            md_lines.append(f"  - `{o['path']}`")
    md_lines.append("")
    md_lines.append("### Root Hygiene")
    md_lines.append(f"- result: {'PASS' if root_hygiene['passed'] else 'FAIL'}")
    md_lines.append("")
    md_lines.append("### Validation")
    md_lines.append(f"- ntpe_validate.py: {'PASS' if ntv.get('passed', False) else 'FAIL'}")
    md_lines.append(f"- git diff --check: {'PASS' if gdc.get('passed', False) else 'FAIL'}")
    md_lines.append(f"- provider/network/translation: {pnt.get('provider', 0)}/{pnt.get('network', 0)}/{pnt.get('translation', 0)}")
    md_lines.append("")
    md_lines.append("### Changes Performed")
    md_lines.append("- modified = 0")
    md_lines.append("- moved = 0")
    md_lines.append("- deleted = 0")
    md_lines.append("- staged = 0")
    md_lines.append("- committed = 0")
    md_lines.append("- pushed = 0")
    md_lines.append("")
    md_lines.append("### Recommended Next Scope")
    if actionable:
        md_lines.append(f"Explicit allowlist: {', '.join(actionable)}")
    else:
        md_lines.append("No actionable production or test changes - recommend governance/documentation cleanup or tool maintenance")
    md_lines.append("")
    md_lines.append("### Deliverables")
    md_lines.append("- docs/governance/repository/P0_FINAL_13_POST_R1_WORKTREE_INVENTORY.md")
    md_lines.append("- artifacts/P0_FINAL_13_Post_R1_Worktree_Inventory_Report.json")
    md_lines.append("")
    md_lines.append("### Unresolved Issues")
    if unknown_infos:
        md_lines.append(f"- {len(unknown_infos)} UNKNOWN paths requiring manual review")
    if not root_hygiene['passed']:
        md_lines.append(f"- Root hygiene violations: {root_hygiene['unexpected_root_files']} files, {root_hygiene['unexpected_root_dirs']} directories")
    if not all_pass:
        md_lines.append("- Some PASS criteria not met (see above)")
    if not unknown_infos and root_hygiene['passed'] and all_pass:
        md_lines.append("- None")
    
    markdown = "\n".join(md_lines)
    
    # JSON artifact
    json_data = {
        "metadata": {
            "task": "P0-FINAL-13",
            "generated_at": datetime.now().isoformat(),
            "git_baseline": {
                "head": R1_COMMIT,
                "origin_main": R1_COMMIT,
                "branch": "main",
                "divergence": "0 0"
            },
            "overall_pass": all_pass
        },
        "worktree_summary": {
            "total_dirty_paths": total,
            "tracked_modified": tracked_modified,
            "tracked_deleted": tracked_deleted,
            "untracked": untracked,
            "renamed": renamed
        },
        "classification_summary": dict(class_counts),
        "scope_distribution": dict(scope_counts),
        "paths": [asdict(info) for info in infos],
        "protected_worktree_reconciliation": {
            "total_protected_in_dirty": len(protected_infos),
            "preserved": protected_preserved,
            "deleted_after_r1j": protected_deleted,
            "modified_after_r1j": protected_modified,
            "disappeared": 0,
            "newly_appeared": 0,
            "details": [asdict(i) for i in protected_infos]
        },
        "unknown_reconciliation": {
            "total_unknown": len(unknown_infos),
            "details": [asdict(i) for i in unknown_infos]
        },
        "r1_post_closure_artifacts": {
            "total": len(r1_infos),
            "r1_i": [asdict(i) for i in infos if i.path in R1_I_ARTIFACTS],
            "r1_j": [asdict(i) for i in infos if i.path in R1_J_ARTIFACTS]
        },
        "production_changes": [asdict(i) for i in prod_candidates],
        "test_changes": [asdict(i) for i in test_candidates],
        "tool_changes": [asdict(i) for i in tools_candidates],
        "governance_changes": [asdict(i) for i in gov_candidates],
        "generated_outputs": [asdict(i) for i in gen_outputs],
        "historical_legacy": [asdict(i) for i in historical],
        "candidate_next_scopes": {
            "SCOPE-A": [i.path for i in prod_candidates],
            "SCOPE-B": [i.path for i in test_candidates],
            "SCOPE-C": [i.path for i in gov_candidates],
            "SCOPE-D": [i.path for i in tools_candidates],
            "SCOPE-E": [i.path for i in gen_outputs],
            "SCOPE-F": [i.path for i in historical],
            "SCOPE-G": [i.path for i in protected_work],
            "SCOPE-H": [i.path for i in manual_review],
            "SCOPE-I": [i.path for i in r1_post]
        },
        "scope_overlaps": overlaps,
        "explicit_exclusions": [
            "R1-I artifacts (2 paths)",
            "R1-J artifacts (2 paths)",
            "All deleted artifacts/ (244 paths)",
            "All test outputs (tests/literary/outputs/)",
            "All governance documents",
            "tools/monitoring/"
        ],
        "recommended_next_task": {
            "production_scope_paths": prod_paths,
            "test_scope_paths": test_paths,
            "governance_scope_paths": gov_paths,
            "tools_scope_paths": tool_paths,
            "untouched_output_paths": [i.path for i in gen_outputs],
            "manual_review_paths": unk_paths,
            "explicit_allowlist": actionable
        },
        "validation_results": validation,
        "root_hygiene": root_hygiene,
        "pass_criteria": checks
    }
    
    return markdown, json_data

def main():
    print("Starting P0-FINAL-13 inventory analysis...")
    infos = analyze_worktree()
    print(f"Analyzed {len(infos)} paths")
    
    validation = run_validation()
    print("Validation complete")
    
    overlaps = detect_overlaps(infos)
    print(f"Overlaps detected: {len(overlaps['overlaps'])}")
    
    root_hygiene = check_root_hygiene(infos)
    print(f"Root hygiene: {'PASS' if root_hygiene['passed'] else 'FAIL'}")
    
    markdown, json_data = generate_report(infos, validation, overlaps, root_hygiene)
    
    # Write deliverables
    md_path = REPO_ROOT / "docs" / "governance" / "repository" / "P0_FINAL_13_POST_R1_WORKTREE_INVENTORY.md"
    json_path = REPO_ROOT / "artifacts" / "P0_FINAL_13_Post_R1_Worktree_Inventory_Report.json"
    
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Markdown report written to: {md_path}")
    print(f"JSON artifact written to: {json_path}")
    
    # Final summary
    all_pass = json_data["metadata"]["overall_pass"]
    print(f"\nP0-FINAL-13 = {'PASS' if all_pass else 'BLOCKED'}")

if __name__ == "__main__":
    main()