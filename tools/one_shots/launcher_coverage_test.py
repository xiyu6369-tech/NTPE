from pathlib import Path
import json
from core.quality.coverage_checker import CoverageChecker

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

    checker = CoverageChecker(root=ROOT)
    result = checker.check(source, translation)

    print("NTPE TQF-03 Coverage Test")
    print("=========================")
    print(f"passed: {result['passed']}")
    print(f"score: {result['score']}")
    print(f"length_ratio: {result['metrics']['length_ratio']}")
    print(f"paragraph_ratio: {result['metrics']['paragraph_ratio']}")
    print(f"source_paragraphs: {result['metrics']['source_paragraphs']}")
    print(f"translation_paragraphs: {result['metrics']['translation_paragraphs']}")
    print(f"issues: {len(result['issues'])}")

    for issue in result["issues"][:10]:
        print(f"- [{issue['severity']}] {issue['type']}: {issue['message']}")
