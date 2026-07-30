"""List all .py files in root directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = sorted(f.name for f in ROOT.glob("*.py"))
for f in files:
    print(f)
print(f"---\nTotal: {len(files)}")