from core.translation_discipline import TargetedRetryUnit, validate_targeted_merge


def main() -> int:
    unit = TargetedRetryUnit(
        unit_id="u1", source_text="來源段落", source_start=0, source_end=40,
        metadata={"translated_start": 3, "translated_end": 3},
    )
    original = "前文。後文。"
    replacement = "補回遺漏內容。"
    merged = "前文。補回遺漏內容。後文。"
    result = validate_targeted_merge(original, replacement, merged, unit)
    assert result.accepted, result.to_metadata()

    dup = validate_targeted_merge(original, "前文。", "前文。前文。後文。", unit)
    assert not dup.accepted

    bad = TargetedRetryUnit(unit_id="u2", source_text="x", source_start=0, source_end=1, metadata={})
    assert not validate_targeted_merge(original, "x", original, bad).accepted
    print("TE v6.0 Stage 11.4 Safe Targeted Merge Validation: ALL PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
