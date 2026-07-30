from pathlib import Path
from engine.pipeline.adaptive_recovery import AdaptiveRecoveryPipeline

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    pipeline = AdaptiveRecoveryPipeline(root=ROOT)
    result = pipeline.run()

    print("")
    print("NTPE v0.9.2 Adaptive Chunk Recovery")
    print("===================================")
    print(f"status: {result['status']}")
    print(f"recovered: {result.get('recovered_count', 0)}")
    print(f"failed: {result.get('failed_count', 0)}")
    print(f"report: {result.get('report_path', '')}")
    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
