from pathlib import Path
import json

from core.expansion.style_expansion_engine import StyleExpansionEngine

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    package_path = ROOT / "prompt_packages" / "passion1_normalized_chunk_000001.json"
    translation_path = ROOT / "translated" / "passion1_normalized_chunk_000001_zh.txt"

    if not package_path.exists():
        print(f"Missing package: {package_path}")
        raise SystemExit(1)

    if not translation_path.exists():
        print(f"Missing translation: {translation_path}")
        raise SystemExit(1)

    package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    source = package["source"]["chunk_text"]
    translation = translation_path.read_text(encoding="utf-8-sig")

    engine = StyleExpansionEngine(root=ROOT)
    result = engine.expand(
        source_text=source,
        translation_text=translation,
        file_name=package["session"]["file_name"],
        chunk_index=int(package["session"]["chunk_index"]),
        model=package["model_profile"]["model"],
        max_output_tokens=1600,
    )

    report_dir = ROOT / "quality_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "style_expansion_latest.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if result["status"] == "expanded":
        backup = translation_path.with_suffix(".style_expansion_bak.txt")
        backup.write_text(translation, encoding="utf-8")
        translation_path.write_text(result["translation"], encoding="utf-8")

    print("NTPE TQF-05.2 Coverage-Aware Style Expansion")
    print("============================================")
    print(f"status: {result['status']}")
    print(f"tasks: {result['plan'].get('task_count', 0)}")
    print(f"expanded: {len(result.get('expanded', {}))}")
    print(f"report: {report_path}")
