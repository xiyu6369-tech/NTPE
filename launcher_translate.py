# =====================================================
# NTPE Translation Engine v2.0 Core
# Launcher
# 放置位置：D:\Python\NTPE\launcher_translate.py
# =====================================================

from pathlib import Path
from core.translation_engine.translation_engine import TranslationEngine

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    package_path = ROOT / "prompt_packages" / "prompt_package_sample.json"

    engine = TranslationEngine(root=ROOT)
    result = engine.translate_package_file(package_path)

    print("NTPE Translation Engine v2.0 Core")
    print("=================================")
    print(f"status: {result['status']}")
    print(f"output: {result.get('output_path', '')}")

    if result["status"] != "success":
        print(f"error: {result.get('error', '')}")
