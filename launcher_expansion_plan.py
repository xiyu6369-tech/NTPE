from pathlib import Path
import json

from core.expansion.expansion_planner import ExpansionPlanner

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    package_path = ROOT / "prompt_packages" / "passion1_normalized_chunk_000001.json"
    translation_path = ROOT / "translated" / "passion1_normalized_chunk_000001_zh.txt"

    package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    source = package["source"]["chunk_text"]
    translation = translation_path.read_text(encoding="utf-8-sig")

    planner = ExpansionPlanner(ROOT)
    plan = planner.plan(source, translation)

    print("NTPE TQF-05.2 Expansion Plan")
    print("============================")
    print(f"passed: {plan['passed']}")
    print(f"source_paragraphs: {plan['source_paragraphs']}")
    print(f"translation_paragraphs: {plan['translation_paragraphs']}")
    print(f"task_count: {plan['task_count']}")

    for task in plan["tasks"]:
        print(f"- P{task['paragraph_index']:03d} ratio={task['ratio']} source={task['source_length']} zh={task['translation_length']}")
