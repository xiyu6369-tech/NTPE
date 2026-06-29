from pathlib import Path
import json

from core.quality.semantic_repair import SemanticRepair

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

    repairer = SemanticRepair(root=ROOT)
    result = repairer.repair(source, translation)

    if result["changed"]:
        backup = translation_path.with_suffix(".semantic_bak.txt")
        backup.write_text(translation, encoding="utf-8")
        translation_path.write_text(result["translation"], encoding="utf-8")

    report_dir = ROOT / "quality_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "semantic_repair_latest.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("NTPE TQF-04 Semantic QA + Auto Repair")
    print("=====================================")
    print(f"changed: {result['changed']}")
    print(f"applied: {len(result['applied'])}")
    print(f"issues_after: {result['qa']['issue_count']}")
    print(f"report: {report_path}")

    for item in result["applied"]:
        print(f"- {item.get('rule_id')} {item.get('type')}")
