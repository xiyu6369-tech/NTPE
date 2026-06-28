# =====================================================
# TQF-01 Document Structure Engine Test
# 放置位置：D:\Python\NTPE\launcher_structure_test.py
# =====================================================

from pathlib import Path
from core.prompt_builder.prompt_builder import PromptBuilder

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    sample = "패션 1\n\n초인종이 울린 순간 정태의는 멈칫했다.\n"

    builder = PromptBuilder(root=ROOT)
    package = builder.build(
        chunk_text=sample,
        file_name="structure_test.txt",
        chunk_index=1,
        chunk_total=1,
        session_id="SESSION_STRUCTURE_TEST",
    )

    output_path = ROOT / "prompt_packages" / "prompt_package_structure_test.json"
    builder.save_package(package, output_path)

    structure = package["source"].get("document_structure", {})
    title = structure.get("title") or {}

    print("TQF-01 Document Structure Engine Test")
    print("=====================================")
    print(f"has_title: {structure.get('has_title')}")
    print(f"source: {title.get('source', '')}")
    print(f"target: {title.get('target', '')}")
    print(f"output: {output_path}")

    if not structure.get("has_title"):
        raise SystemExit("FAIL: title was not detected")

    if title.get("target") != "《PASSION》第一卷":
        raise SystemExit("FAIL: title target is incorrect")

    print("PASS")
