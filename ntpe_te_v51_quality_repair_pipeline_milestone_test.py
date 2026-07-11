from core.translation_quality_v5 import (
    QualityRepairPlanner,
    QualityRetryOrchestrator,
    QualityChunkRebuildPlanner,
    QualityRepairPipeline,
)


def check(name, condition):
    print(f"{name:<54} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.1 Quality Repair Pipeline Milestone Test")
    print("=" * 88)

    planner = QualityRepairPlanner()
    retry = QualityRetryOrchestrator()
    rebuild = QualityChunkRebuildPlanner()
    pipeline = QualityRepairPipeline()

    source = (
        "정태의는 문을 열었다. 그는 카일을 바라보았다.\n\n"
        "카일은 조용히 웃었다. 그리고 다시 책을 펼쳤다."
    )
    good = (
        "鄭泰義打開了門。他望向凱爾。\n\n"
        "凱爾安靜地笑了笑，接著再次翻開書本。"
    )
    terms = {"정태의": "鄭泰義", "카일": "凱爾"}

    good_result = pipeline.run(source, good, locked_terms=terms)
    check("Good Output Accepted", good_result["accepted"] is True)
    check("Good Status Accepted", good_result["status"] == "accepted")
    check("Good No Retry", good_result["retry_result"]["retry"] is False)
    check("Good Pipeline Valid", pipeline.validate_result(good_result))

    bad_result = pipeline.run(
        source,
        "这个人가。",
        locked_terms=terms,
        runtime_state={
            "attempt": 0,
            "max_attempts": 5,
            "timeout_seconds": 180,
            "chunk_size": 600,
        },
        config={"chunk_size": 600, "min_chunk_size": 20},
    )
    check("Bad Output Rejected", bad_result["accepted"] is False)
    check("Bad Retry Planned", bad_result["status"] == "retry_planned")
    check("Bad Retry Enabled", bad_result["retry_result"]["retry"] is True)
    check("Bad Repair Actions Present", len(bad_result["repair_plan"]["actions"]) >= 1)
    check("Bad Rebuild Required", bad_result["rebuild_result"]["rebuild_required"] is True)
    check("Bad Pipeline Valid", pipeline.validate_result(bad_result))

    short_quality = {
        "accepted": False,
        "baseline_report": {
            "issues": [
                {
                    "code": "too_short",
                    "severity": "critical",
                    "repair_action": "split_and_retranslate",
                }
            ]
        },
        "normalization_result": {"simplified_residue_count": 0},
        "terminology_result": {"repair_replacements": []},
    }
    repair_plan = planner.plan(short_quality)
    check("Planner Retry Required", repair_plan["retry_required"] is True)
    check("Planner Split Required", repair_plan["split_required"] is True)
    check("Planner Valid", planner.validate_plan(repair_plan))

    retry_result = retry.build_retry_decision(
        repair_plan,
        {"attempt": 0, "max_attempts": 5, "timeout_seconds": 180, "chunk_size": 100},
        {"chunk_size": 100, "min_chunk_size": 20},
    )
    check("Retry Orchestrator Enabled", retry_result["retry"] is True)
    check("Retry Result Valid", retry.validate_result(retry_result))

    rebuild_result = rebuild.build(
        "가" * 100,
        retry_result,
        repair_plan,
        {"chunk_size": 100, "min_chunk_size": 20},
    )
    check("Rebuild Planned", rebuild_result["rebuild_required"] is True)
    check("Rebuild Result Valid", rebuild.validate_result(rebuild_result))
    check("Rebuild Text Not Retained", all(
        "text" not in segment
        for segment in rebuild_result.get("plan", {}).get("segments", [])
    ))

    check("No Provider Call", bad_result["integration_status"]["provider_called"] is False)
    check("No Runtime Modification", bad_result["integration_status"]["runtime_modified"] is False)
    check("No Real Translation", bad_result["integration_status"]["real_translation_executed"] is False)

    print("NTPE TE-v5.1 Quality Repair Pipeline Milestone PASS")


if __name__ == "__main__":
    main()
