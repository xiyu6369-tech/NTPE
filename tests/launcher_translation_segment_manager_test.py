import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.segment_manager import (
    SEGMENT_COMPLETED,
    SEGMENT_PENDING,
    TranslationSegmentManager,
    create_segment_queue,
    create_translation_segment_manager_adapter,
    export_segment_manifest,
    merge_segments,
    normalize_managed_segment,
    queue_metrics,
    sort_segments,
    split_segment,
    validate_managed_segment,
)


def check(name, condition):
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)


print("NTPE Foundation-06.2 Translation Segment Manager Test")
print("======================================================")

legacy = {"id": "legacy-s1", "text": "안녕하세요", "requires": []}
seg = normalize_managed_segment(legacy, 0)
check("Legacy Segment", seg["segment_id"] == "legacy-s1")
check("Segment Created", seg["source_text"] == "안녕하세요")
check("Validate Segment", validate_managed_segment(seg))

segments = [
    {"segment_id": "s2", "index": 2, "priority": 20, "source_text": "B", "dependencies": ["s1"]},
    {"segment_id": "s1", "index": 1, "priority": 10, "source_text": "A"},
]
ordered = sort_segments(segments)
check("Segment Order", ordered[0]["segment_id"] == "s1")

queue = create_segment_queue(segments)
check("Queue Created", queue["type"] == "translation_segment_queue")
check("Queue Ready", queue["status"] == "ready")
check("Queue Order", queue["segments"][0]["segment_id"] == "s1")

manager = TranslationSegmentManager(segments)
check("Manager Created", len(manager.queue["segments"]) == 2)
first = manager.next()
check("Next Ready", first["segment_id"] == "s1")
manager.start("s1")
check("Segment Running", manager.get("s1")["status"] == "running")
manager.complete("s1", "甲")
check("Segment Completed", manager.get("s1")["target_text"] == "甲")
second = manager.next()
check("Dependency Released", second["segment_id"] == "s2")

manager.start("s2")
failed = manager.fail("s2", {"message": "temporary"})
check("Retry Pending", failed["status"] == SEGMENT_PENDING)
check("Retry Attempt", failed["retry"]["attempts"] == 1)
manager.start("s2")
manager.complete("s2", "乙")
metrics = manager.metrics()
check("Metrics Created", metrics["completed"] == 2)
check("Metrics Percent", metrics["percent"] == 100.0)

long_seg = normalize_managed_segment({"segment_id": "long", "index": 10, "source_text": "abcdef"}, 10)
children = split_segment(long_seg, max_length=2)
check("Segment Split", len(children) == 3)
check("Split Parent", children[0]["split_from"] == "long")
for child in children:
    child["status"] = SEGMENT_COMPLETED
    child["target_text"] = child["source_text"].upper()
merged = merge_segments(children)
check("Segment Merge", merged["target_text"] == "ABCDEF")
check("Merge Completed", merged["completed"] is True)

manager2 = TranslationSegmentManager([long_seg])
split_children = manager2.split("long", max_length=3)
check("Manager Split", len(split_children) == 2)
manager2.complete("long.1", "ABC")
manager2.complete("long.2", "DEF")
merge_result = manager2.merge("long")
check("Manager Merge", merge_result["target_text"] == "ABCDEF")

manifest = manager.manifest()
check("Manifest Created", manifest["type"] == "translation_segment_manifest")
check("Manifest Metrics", manifest["metrics"]["completed"] == 2)
check("Manifest Segment IDs", len(manifest["segment_ids"]) == 2)

adapter = create_translation_segment_manager_adapter(segments)
check("Adapter Created", adapter.validate())
adapter_next = adapter.next()
check("Adapter Next", adapter_next["segment_id"] == "s1")
adapter.start("s1")
adapter.complete("s1", "甲")
check("Adapter Complete", adapter.manifest()["metrics"]["completed"] == 1)
check("Adapter Manifest", adapter.manifest()["type"] == "translation_segment_manifest")

legacy_queue = create_segment_queue([{"id": "old", "text": "K"}])
legacy_manifest = export_segment_manifest(legacy_queue)
check("Legacy Queue", legacy_manifest["segment_ids"] == ["old"])
check("Backward Compatible", validate_managed_segment(legacy_queue["segments"][0]))

print("PASS")
