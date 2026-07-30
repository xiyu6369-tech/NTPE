from pathlib import Path
from engine.pipeline.pipeline_v1 import ProductionPipelineV1

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    pipeline = ProductionPipelineV1(root=ROOT)
    result = pipeline.run()

    print("")
    print("NTPE v1.0.1 Production Pipeline")
    print("===============================")
    for key in [
        "status", "file_count", "chunk_count", "translated_count", "skipped_count",
        "semantic_repaired_count", "style_expanded_count", "quality_failed_count",
        "missing_file_count", "failed_count", "report_path"
    ]:
        print(f"{key}: {result.get(key, '')}")

    if result.get("status") not in ["success", "partial_success", "interrupted"]:
        print(f"error: {result.get('error', '')}")
