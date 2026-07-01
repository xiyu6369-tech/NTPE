import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.intelligence import IntelligenceAdapter, IntelligenceMemoryStore


def check(label, condition):
    print(f"{label:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def main():
    print("NTPE Foundation-07.0 Translation Intelligence Contract Test")
    print("=" * 62)

    store = IntelligenceMemoryStore()
    store.add_character("정태의", "鄭泰義", aliases=["Tae-ui"], traits=["適應力強"])
    store.add_glossary("일라이 리그로우", "伊萊・里格勞", category="character", locked=True)
    store.add_narrative("tone", "台灣繁體中文、自然流暢、不得漏譯")
    store.add_scene("scene-001", "主角在陌生環境中建立初始關係", location="海外", participants=["鄭泰義"])

    adapter = IntelligenceAdapter(store)
    snapshot = store.build_snapshot().to_dict()
    prompt_package = adapter.attach_to_prompt_package({"id": "demo_prompt"})
    manifest = adapter.attach_to_manifest({"components": []})
    validation = adapter.validate_output("鄭泰義看著伊萊・里格勞，沉默了一會兒。")

    check("Character Memory", len(snapshot["characters"]) == 1)
    check("Glossary Intelligence", len(snapshot["glossary"]) == 1)
    check("Narrative Memory", len(snapshot["narrative"]) == 1)
    check("Scene Memory", len(snapshot["scenes"]) == 1)
    check("Snapshot Manifest", snapshot["manifest"]["foundation"] == "07.0")
    check("Prompt Context Attached", len(prompt_package["context_components"]) == 1)
    check("Runtime Manifest Attached", len(manifest["components"]) == 1)
    check("Consistency Contract", validation["issue_count"] == 0)
    check("Intelligence Adapter", manifest["components"][0]["enabled"] is True)

    print("PASS")


if __name__ == "__main__":
    main()
