import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.translation.runtime_contract import (
    create_translation_segment,
    normalize_translation_segment,
    validate_translation_segment,
    create_translation_job,
    normalize_translation_job,
    validate_translation_job,
    create_translation_context,
    validate_translation_context,
    create_translation_error,
    validate_translation_error,
    create_translation_result,
    validate_translation_result,
    create_translation_manifest,
    validate_translation_manifest,
    build_production_runtime_payload,
    TranslationRuntimeContractAdapter,
)
from adapters.translation_runtime_adapter import (
    TranslationRuntimeAdapter,
    create_translation_runtime_adapter,
    validate_translation_runtime_adapter,
)


def check(name, cond):
    print(f"{name:<28} {'PASS' if cond else 'FAIL'}")
    if not cond:
        raise AssertionError(name)


def main():
    print("NTPE Foundation-06.0 Translation Runtime Contract Test")
    print("======================================================")

    legacy_segment = normalize_translation_segment("안녕하세요", index=0)
    check("Legacy Segment", legacy_segment["source_text"] == "안녕하세요")

    segment = create_translation_segment("문장", index=1)
    check("Segment Created", segment["index"] == 1)
    check("Validate Segment", validate_translation_segment(segment))

    normalized_segment = normalize_translation_segment({"source": "소스"}, index=2)
    check("Normalize Segment", normalized_segment["source_text"] == "소스")

    job = create_translation_job(["첫 문장", "둘째 문장"], target_language="zh-TW")
    check("Job Created", len(job["segments"]) == 2)
    check("Validate Job", validate_translation_job(job))
    check("Job Target", job["target_language"] == "zh-TW")

    normalized_job = normalize_translation_job({"source": "단일", "target_language": "zh-TW"})
    check("Normalize Job", len(normalized_job["segments"]) == 1)

    context = create_translation_context(job, glossary={"정태의": "鄭泰義"})
    check("Context Created", context["job_id"] == job["job_id"])
    check("Validate Context", validate_translation_context(context))
    check("Context Glossary", context["glossary"]["정태의"] == "鄭泰義")

    err = create_translation_error("MODEL_TIMEOUT", "timeout", retryable=True)
    check("Error Created", err["code"] == "MODEL_TIMEOUT")
    check("Validate Error", validate_translation_error(err))

    completed_segments = []
    for s in job["segments"]:
        item = dict(s)
        item["status"] = "completed"
        item["translated_text"] = f"翻譯:{item['index']}"
        completed_segments.append(item)

    result = create_translation_result(job, segments=completed_segments, context=context)
    check("Result Created", result["ok"] is True)
    check("Validate Result", validate_translation_result(result))
    check("Result Output", "翻譯:0" in result["output_text"] and "翻譯:1" in result["output_text"])

    manifest = create_translation_manifest(test="foundation-06.0")
    check("Manifest Created", manifest["version"] == "06.0")
    check("Validate Manifest", validate_translation_manifest(manifest))

    payload = build_production_runtime_payload(job)
    check("Payload Created", "첫 문장" in payload["source"])
    check("Payload Contract", payload["metadata"]["contract"] == "translation-runtime")
    check("Payload Job", payload["metadata"]["translation_job"]["job_id"] == job["job_id"])

    adapter = TranslationRuntimeContractAdapter()
    ajob = adapter.normalize_job("어댑터")
    check("Adapter Created", adapter.validate())
    check("Adapter Normalize", adapter.validate_job(ajob))
    apayload = adapter.build_payload(ajob)
    check("Adapter Payload", apayload["metadata"]["translation_job"]["job_id"] == ajob["job_id"])
    aresult = adapter.create_result(ajob)
    check("Adapter Result", validate_translation_result(aresult))
    check("Adapter Manifest", adapter.manifest()["contract"] == "translation-runtime")

    public_adapter = TranslationRuntimeAdapter()
    check("Public Adapter", public_adapter.validate())
    factory_adapter = create_translation_runtime_adapter(factory=True)
    check("Factory Adapter", validate_translation_runtime_adapter(factory_adapter))

    # Backward compatibility: plain string source can become a valid job and payload.
    legacy_job = normalize_translation_job("레거시 입력")
    legacy_payload = build_production_runtime_payload(legacy_job)
    check("Backward Compatible", legacy_payload["source"] == "레거시 입력")

    print("PASS")


if __name__ == "__main__":
    main()
