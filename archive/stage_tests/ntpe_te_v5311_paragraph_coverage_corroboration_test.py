from __future__ import annotations

from core.translation_quality_v5.quality_baseline import TranslationQualityBaseline


def _issue(report: dict, code: str) -> dict | None:
    return next((item for item in report["issues"] if item["code"] == code), None)


def main() -> int:
    baseline = TranslationQualityBaseline()

    source = "甲。\n\n乙。\n\n丙。\n\n丁。\n\n戊。"

    # Five Korean paragraphs may become two polished Chinese paragraphs while
    # preserving all five sentence units. This must not force a retranslation.
    merged = "甲。乙。丙。\n\n丁。戊。"
    report = baseline.evaluate(
        source,
        merged,
        config={"min_paragraph_ratio": 0.7},
    )
    warning = _issue(report, "paragraph_structure_merged")
    assert warning is not None
    assert warning["severity"] == "medium"
    assert warning["metadata"]["corroborated"] is False
    assert report["accepted"] is True

    # Paragraph loss plus sentence/length loss remains a blocking omission.
    omitted = "甲。"
    report = baseline.evaluate(
        source,
        omitted,
        config={"min_paragraph_ratio": 0.7, "min_length_ratio": 0.1},
    )
    blocking = _issue(report, "paragraph_omission_suspected")
    assert blocking is not None
    assert blocking["severity"] == "high"
    assert blocking["metadata"]["corroborated"] is True
    assert report["accepted"] is False

    print("TE v5.3.1.1 Paragraph Coverage Corroboration")
    print("================================================")
    print("Natural paragraph merge is warning       PASS")
    print("Corroborated omission remains blocking    PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
