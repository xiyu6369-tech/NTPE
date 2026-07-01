import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.context_runtime import (
    TranslationContextBuilder,
    TranslationContextCache,
    compact_segment_context,
    context_cache_key,
    create_context_bundle,
    create_context_manifest,
    create_translation_context_runtime_adapter,
    normalize_glossary,
    validate_context_bundle,
)


def check(name, condition):
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)

print("NTPE Foundation-06.3 Translation Context Runtime Test")
print("======================================================")

job = {
    "job_id": "job-063",
    "source_language": "ko",
    "target_language": "zh-TW",
    "glossary": {"정태의": "鄭泰義"},
    "character_context": {"鄭泰義": {"role": "main"}},
}
segments = [
    {"segment_id": "s1", "index": 1, "source_text": "A", "target_text": "甲", "status": "completed"},
    {"segment_id": "s2", "index": 2, "source_text": "B"},
    {"segment_id": "s3", "index": 3, "source_text": "C"},
]
legacy = {"id": "legacy", "text": "안녕", "index": 0}
compact = compact_segment_context(legacy)
check("Legacy Segment", compact["segment_id"] == "legacy")
check("Compact Segment", compact["source_text"] == "안녕")

glossary = normalize_glossary([{"source": "일라이", "target": "伊萊"}])
check("Glossary Normalized", glossary["일라이"] == "伊萊")

bundle = create_context_bundle(
    segment=segments[1],
    job=job,
    previous_segments=[segments[0]],
    next_segments=[segments[2]],
    narrative_context={"chapter": 1},
    scene_context={"location": "library"},
    version=2,
)
check("Bundle Created", bundle["type"] == "translation_context_bundle")
check("Validate Bundle", validate_context_bundle(bundle))
check("Bundle Version", bundle["version"] == 2)
check("Previous Context", bundle["previous_context"][0]["segment_id"] == "s1")
check("Next Context", bundle["next_context"][0]["segment_id"] == "s3")
check("Glossary Context", bundle["glossary_context"]["정태의"] == "鄭泰義")
check("Character Context", "鄭泰義" in bundle["character_context"])
check("Narrative Context", bundle["narrative_context"]["chapter"] == 1)
check("Scene Context", bundle["scene_context"]["location"] == "library")

key = context_cache_key("job-063", "s2", 1)
cache = TranslationContextCache()
check("Cache Created", not cache.has(key))
cache.set(key, bundle)
check("Cache Set", cache.has(key))
check("Cache Get", cache.get(key)["segment"]["segment_id"] == "s2")
check("Cache Manifest", cache.manifest()["count"] == 1)

builder = TranslationContextBuilder(job=job, window=1)
built = builder.build(segments[1], segments, version=1)
check("Builder Created", validate_context_bundle(built))
check("Builder Previous", built["previous_context"][0]["segment_id"] == "s1")
check("Builder Next", built["next_context"][0]["segment_id"] == "s3")
built_again = builder.build(segments[1], segments, version=1)
check("Builder Cache Hit", built_again["context_id"] == built["context_id"])
manifest = builder.manifest()
check("Manifest Created", manifest["type"] == "translation_context_runtime")
check("Manifest Events", len(manifest["events"]) >= 2)

adapter = create_translation_context_runtime_adapter(job=job, window=1)
ctx = adapter.build_context(segments[1], segments)
check("Adapter Created", adapter.validate(ctx))
payload = adapter.attach_context({"payload_id": "p1"}, segments[1], segments)
check("Adapter Attach", payload["translation_context"]["segment"]["segment_id"] == "s2")
check("Adapter Manifest", adapter.manifest()["version"] == "Foundation-06.3")
check("Public Adapter", create_context_manifest()["version"] == "Foundation-06.3")
check("Backward Compatible", validate_context_bundle(create_context_bundle(legacy)))

print("PASS")
