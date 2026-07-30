from core.translation_quality_v5 import (
    TranslationQualityBaseline,
    CompletenessGuard,
    TerminologyConsistencyGuard,
    TraditionalChineseNormalizer,
    TranslationQualityCorePipeline,
)


def check(name, condition):
    print(f"{name:<52} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v5.0 Quality Core Milestone Test")
    print("=" * 86)

    baseline = TranslationQualityBaseline()
    completeness = CompletenessGuard()
    terminology = TerminologyConsistencyGuard()
    normalizer = TraditionalChineseNormalizer()
    pipeline = TranslationQualityCorePipeline()

    source = (
        "정태의는 문을 열었다. 그는 카일을 바라보았다.\n\n"
        "카일은 조용히 웃었다. 그리고 다시 책을 펼쳤다."
    )
    good = (
        "鄭泰義打開了門。他望向凱爾。\n\n"
        "凱爾安靜地笑了笑，接著再次翻開書本。"
    )
    terms = {"정태의": "鄭泰義", "카일": "凱爾"}

    good_report = baseline.evaluate(source, good, locked_terms=terms)
    check("Stage-5.0.1 Good Baseline Accepted", good_report["accepted"] is True)
    check("Stage-5.0.1 Report Valid", baseline.validate_report(good_report))

    bad_report = baseline.evaluate(
        source,
        "郑泰义가。",
        locked_terms=terms,
    )
    check("Stage-5.0.1 Hangul Detected", any(
        issue["code"] == "hangul_residue"
        for issue in bad_report["issues"]
    ))
    check("Stage-5.0.1 Too Short Detected", any(
        issue["code"] == "too_short"
        for issue in bad_report["issues"]
    ))

    complete = completeness.evaluate(source, good)
    check("Stage-5.0.2 Complete Accepted", complete["accepted"] is True)
    check("Stage-5.0.2 Result Valid", completeness.validate_result(complete))

    incomplete = completeness.evaluate(source, "鄭泰義。")
    check("Stage-5.0.2 Omission Rejected", incomplete["accepted"] is False)
    check("Stage-5.0.2 Retry Required", incomplete["retry_required"] is True)

    term_result = terminology.evaluate(
        source,
        good,
        locked_terms=terms,
        forbidden_variants={"정태의": ["鄭泰依", "定泰義"]},
    )
    check("Stage-5.0.3 Terms Consistent", term_result["accepted"] is True)
    check("Stage-5.0.3 Result Valid", terminology.validate_result(term_result))

    wrong_term = terminology.evaluate(
        source,
        "定泰義打開了門。他望向凱爾。",
        locked_terms=terms,
        forbidden_variants={"정태의": ["定泰義"]},
    )
    check("Stage-5.0.3 Wrong Variant Detected", wrong_term["accepted"] is False)
    check("Stage-5.0.3 Repair Applied", "鄭泰義" in wrong_term["repaired_text"])

    normalized = normalizer.normalize('“这个人说......”')
    check("Stage-5.0.4 Traditional Converted", "這個人說" in normalized["normalized_text"])
    check("Stage-5.0.4 Quotes Normalized", normalized["normalized_text"].startswith("「"))
    check("Stage-5.0.4 Ellipsis Normalized", "……" in normalized["normalized_text"])
    check("Stage-5.0.4 Result Valid", normalizer.validate_result(normalized))

    pipeline_result = pipeline.run(
        source,
        good,
        locked_terms=terms,
        forbidden_variants={"정태의": ["定泰義"]},
    )
    check("Stage-5.0.5 Pipeline Accepted", pipeline_result["accepted"] is True)
    check("Stage-5.0.5 Pipeline Valid", pipeline.validate_result(pipeline_result))
    check("Stage-5.0.5 No Provider Call", pipeline_result["integration_status"]["provider_called"] is False)
    check("Stage-5.0.5 No Runtime Modification", pipeline_result["integration_status"]["runtime_modified"] is False)

    failing_pipeline = pipeline.run(
        source,
        "这个人가。",
        locked_terms=terms,
    )
    check("Stage-5.0.5 Pipeline Rejects Bad Output", failing_pipeline["accepted"] is False)
    check("Stage-5.0.5 Repair Required", failing_pipeline["repair_required"] is True)
    check("Stage-5.0.5 Retry Required", failing_pipeline["retry_required"] is True)

    print("NTPE TE-v5.0 Quality Core Milestone PASS")


if __name__ == "__main__":
    main()
