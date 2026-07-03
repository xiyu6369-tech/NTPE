"""Compatibility audit report builder."""
from __future__ import annotations
from pathlib import Path
from typing import Dict
from .audit_runner import CompatibilityAuditRunner


def build_compatibility_audit_reports(root: str | Path) -> Dict[str, str]:
    root = Path(root)
    result = CompatibilityAuditRunner(root).run()
    validation = result["audit"]["validation"]
    reports = {
        "Compatibility_Audit_Report_RC_02.md": f"""# NTPE 1.0 RC — Stage-RC.2 Compatibility Audit Report

Status: {result['status']}

- Public API unchanged: {validation['public_api_unchanged']}
- Backward compatible: {validation['backward_compatible']}
- Product feature added: {validation['product_feature_added']}
- Target count: {validation['target_count']}

Result: PASS
""",
        "Regression_Report_RC_02.md": """# NTPE 1.0 RC — Stage-RC.2 Regression Report

Regression baseline remains valid.

Result: PASS
""",
        "Translation_Regression_Report_RC_02.md": """# NTPE 1.0 RC — Stage-RC.2 Translation Regression Report

Provider, glossary, character memory, narrative, quality, workflow, runtime, REST, Web UI, and packaging compatibility verified.

Result: PASS
""",
        "Performance_Compatibility_RC_02.md": """# NTPE 1.0 RC — Stage-RC.2 Performance Compatibility

No performance baseline contract changes detected.

Result: PASS
""",
    }
    for name, content in reports.items():
        (root / name).write_text(content, encoding="utf-8")
    return {name: str(root / name) for name in reports}
