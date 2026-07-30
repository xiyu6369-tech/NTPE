
from core.translation_reliability import (
    AdaptiveRetryPolicy,
    AdaptiveChunkSplitPlanner,
)


def check(name, condition):
    print(f"{name:<44} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.3 Adaptive Chunk Split Planner Test")
    print("=" * 78)

    retry_policy = AdaptiveRetryPolicy()
    planner = AdaptiveChunkSplitPlanner()
    source = "가" * 600

    timeout_decision = retry_policy.decide({
        "outcome": "read_timeout",
        "attempt": 1,
        "max_attempts": 5,
        "timeout_seconds": 180,
        "chunk_size": 600,
    })

    timeout_plan = planner.plan(source, timeout_decision)
    check("Timeout Split Enabled", timeout_plan["should_split"] is True)
    check("Timeout Effective Size", timeout_plan["effective_chunk_size"] == 300)
    check("Timeout Segment Count", timeout_plan["segment_count"] == 2)
    check("Timeout Merge Strategy", timeout_plan["merge_strategy"] == "ordered_concat_trim_overlap")
    check("Timeout Reconstructs Source", planner.merge_preview(timeout_plan) == source)

    short_decision = retry_policy.decide({
        "outcome": "too_short",
        "attempt": 0,
        "max_attempts": 5,
        "chunk_size": 600,
    })
    short_plan = planner.plan(source, short_decision)
    check("Too Short Split Enabled", short_plan["should_split"] is True)
    check("Too Short Segment Count", short_plan["segment_count"] == 2)

    no_split_decision = retry_policy.decide({
        "outcome": "http_503",
        "attempt": 1,
        "max_attempts": 5,
        "chunk_size": 600,
    })
    no_split_plan = planner.plan(source, no_split_decision)
    check("503 Split Disabled", no_split_plan["should_split"] is False)
    check("503 Identity Merge", no_split_plan["merge_strategy"] == "identity")
    check("503 Reconstructs Source", planner.merge_preview(no_split_plan) == source)

    overlap_source = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    overlap_plan = planner.plan(
        overlap_source,
        {
            "outcome": "read_timeout",
            "retry": True,
            "next_chunk_size": 10,
        },
        {
            "min_chunk_size": 5,
            "default_chunk_size": 10,
            "max_chunk_size": 10,
            "overlap_chars": 2,
        },
    )
    check("Overlap Split Enabled", overlap_plan["should_split"] is True)
    check("Overlap Recorded", overlap_plan["overlap_chars"] == 2)
    check("Overlap Reconstructs Source", planner.merge_preview(overlap_plan) == overlap_source)

    empty_plan = planner.plan("", timeout_decision)
    check("Empty Source No Split", empty_plan["should_split"] is False)
    check("Empty Source No Segments", empty_plan["segment_count"] == 0)

    disabled_plan = planner.plan(
        source,
        {
            "outcome": "read_timeout",
            "retry": False,
            "next_chunk_size": 300,
        },
    )
    check("Retry Disabled No Split", disabled_plan["should_split"] is False)

    for plan in [
        timeout_plan,
        short_plan,
        no_split_plan,
        overlap_plan,
        empty_plan,
        disabled_plan,
    ]:
        check("Plan Valid", planner.validate_plan(plan))

    check("No Provider Call", timeout_plan["metadata"]["provider_called"] is False)
    check("No HTTP Call", timeout_plan["metadata"]["http_called"] is False)
    check("No API Key Access", timeout_plan["metadata"]["api_key_accessed"] is False)
    check("No Runtime Modification", timeout_plan["metadata"]["runtime_modified"] is False)
    check("No Translation Execution", timeout_plan["metadata"]["translation_executed"] is False)

    print("NTPE TE-v4.0 Stage-4.0.3 Adaptive Chunk Split Planner PASS")


if __name__ == "__main__":
    main()
