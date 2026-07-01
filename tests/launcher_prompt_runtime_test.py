import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.context_runtime import create_context_bundle
from translation.prompt_runtime import (
    PromptPackageCache,
    PromptRuntimeBuilder,
    build_prompt_text,
    create_prompt_package,
    create_prompt_runtime_adapter,
    create_prompt_runtime_manifest,
    create_prompt_template,
    normalize_prompt_package,
    normalize_prompt_template,
    validate_prompt_package,
    validate_prompt_template,
)


def check(name, condition):
    print(f"{name:<32} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)

print("NTPE Foundation-06.4 Prompt Runtime Test")
print("=========================================")

job = {"job_id": "job-064", "source_language": "ko", "target_language": "zh-TW", "glossary": {"정태의": "鄭泰義"}}
segments = [
    {"segment_id": "s1", "index": 1, "source_text": "前段", "target_text": "前段譯文", "status": "completed"},
    {"segment_id": "s2", "index": 2, "source_text": "안녕하세요"},
    {"segment_id": "s3", "index": 3, "source_text": "後段"},
]
ctx = create_context_bundle(segment=segments[1], job=job, previous_segments=[segments[0]], next_segments=[segments[2]])
legacy = normalize_prompt_package({"id": "legacy", "content": "請翻譯"})
check("Legacy Package", legacy["package_id"] == "legacy")

template = create_prompt_template()
check("Template Created", template["type"] == "translation_prompt_template")
check("Validate Template", validate_prompt_template(template))
normalized = normalize_prompt_template({"id": "custom", "instruction": "翻譯"})
check("Normalize Template", normalized["template_id"] == "custom")

text = build_prompt_text(ctx, template)
check("Prompt Text", "【待翻譯內容】" in text)
check("Prompt Glossary", "정태의" in text and "鄭泰義" in text)
check("Prompt Previous", "前段譯文" in text)

package = create_prompt_package(ctx, template)
check("Package Created", package["type"] == "translation_prompt_package")
check("Validate Package", validate_prompt_package(package))
check("Package Messages", package["messages"][0]["role"] == "system")
check("Package Target", package["target_language"] == "zh-TW")

cache = PromptPackageCache()
check("Cache Created", not cache.has("p1"))
cache.set("p1", package)
check("Cache Set", cache.has("p1"))
check("Cache Get", cache.get("p1")["package_id"] == package["package_id"])
check("Cache Manifest", cache.manifest()["count"] == 1)

builder = PromptRuntimeBuilder(template=template)
built = builder.build(ctx)
check("Builder Created", validate_prompt_package(built))
built_again = builder.build(ctx)
check("Builder Cache Hit", built_again["package_id"] == built["package_id"])
manifest = builder.manifest()
check("Manifest Created", manifest["type"] == "prompt_runtime")
check("Manifest Events", len(manifest["events"]) >= 2)

adapter = create_prompt_runtime_adapter()
prompt = adapter.build_prompt(ctx)
check("Adapter Created", adapter.validate(prompt))
payload = adapter.attach_prompt({"payload_id": "payload-064"}, ctx)
check("Adapter Attach", payload["prompt_package"]["segment"]["segment_id"] == "s2")
check("Adapter Manifest", adapter.manifest()["version"] == "Foundation-06.4")
check("Public Manifest", create_prompt_runtime_manifest()["version"] == "Foundation-06.4")
check("Backward Compatible", validate_prompt_package(normalize_prompt_package({"prompt_text": "請翻譯"})))

print("PASS")
