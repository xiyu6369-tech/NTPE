# =====================================================
# NTPE Translation Runtime v1.2 Professional Stage-01
# Launcher compatibility entry
# 放置位置：D:\Python\NTPE\launcher_translate.py
# =====================================================

from pathlib import Path
from core.translation_runtime import TranslationRuntime

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    package_path = ROOT / "prompt_packages" / "prompt_package_sample.json"

    runtime = TranslationRuntime(root=ROOT)
    result = runtime.translate_package_file(package_path)

    print("NTPE Translation Runtime v1.2 Professional")
    print("==========================================")
    print(f"status: {result['status']}")
    print(f"output: {result.get('output_path', '')}")

    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
