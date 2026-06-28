# =====================================================
# NTPE TQF Quality Benchmark v1.0
# Launcher
# 放置位置：D:\Python\NTPE\launcher_quality_benchmark.py
# =====================================================

from pathlib import Path
import sys

from core.quality.quality_benchmark import QualityBenchmark

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    package_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else ROOT / "prompt_packages" / "passion1_normalized_chunk_000001.json"
    translation_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else ROOT / "translated" / "passion1_normalized_chunk_000001_zh.txt"

    benchmark = QualityBenchmark(root=ROOT)
    result = benchmark.evaluate_files(package_path=package_path, translation_path=translation_path)

    print("NTPE TQF Quality Benchmark v1.0")
    print("===============================")
    print(f"status: {result['status']}")
    print(f"overall_score: {result['scores']['overall']}")
    print(f"structure: {result['scores']['structure']}")
    print(f"semantic: {result['scores']['semantic']}")
    print(f"coverage: {result['scores']['coverage']}")
    print(f"hallucination: {result['scores']['hallucination']}")
    print(f"style: {result['scores']['style']}")
    print(f"issues: {len(result['issues'])}")
    print(f"report_json: {result['report_json']}")
    print(f"report_txt: {result['report_txt']}")

    if result["issues"]:
        print("")
        print("Top Issues:")
        for issue in result["issues"][:10]:
            print(f"- [{issue['severity']}] {issue['type']}: {issue['message']}")
