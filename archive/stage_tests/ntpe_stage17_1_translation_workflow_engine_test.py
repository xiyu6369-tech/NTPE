# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine Launcher Test
# =====================================================

from core.workflow import TranslationWorkflowEngine


def main() -> int:
    engine = TranslationWorkflowEngine()
    result = engine.run("第一段。\n第二段。")
    checks = [
        ("Workflow Success", result.success),
        ("Translation Artifact", "translation" in result.artifacts),
        ("Quality Artifact", "quality_report" in result.artifacts),
        ("Export Artifact", "export" in result.artifacts),
        ("Step Count", result.metrics.get("completed_step_count") == 7),
    ]
    print("NTPE 1.2 Professional - Stage-17.1 Translation Workflow Engine")
    print("=" * 72)
    failed = False
    for name, ok in checks:
        print(f"{name:28} {'PASS' if ok else 'FAIL'}")
        failed = failed or not ok
    print("PASS" if not failed else "FAIL")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
