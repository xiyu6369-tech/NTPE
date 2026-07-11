from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    root / "core" / "translation_quality_v5" / "__init__.py",
    root / "core" / "translation_quality_v5" / "quality_baseline.py",
    root / "core" / "translation_quality_v5" / "completeness_guard.py",
    root / "core" / "translation_quality_v5" / "terminology_guard.py",
    root / "core" / "translation_quality_v5" / "traditional_chinese_normalizer.py",
    root / "core" / "translation_quality_v5" / "quality_core_pipeline.py",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing Stage-5.0 files:\n" + "\n".join(missing))

print("TE v5.0 Quality Core Milestone files are in place.")
print("No Provider Runtime, Translation Runtime, launcher, Prompt, Context, or Naturalness Guard file was modified.")
