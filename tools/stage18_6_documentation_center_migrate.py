from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STAGE_DIRS = {
    "STAGE14": DOCS / "stages" / "stage14",
    "STAGE15": DOCS / "stages" / "stage15",
    "STAGE16": DOCS / "stages" / "stage16",
    "STAGE17": DOCS / "stages" / "stage17",
    "STAGE18": DOCS / "stages" / "stage18",
}


def target_for(path: Path) -> Path:
    name = path.name.upper()
    for key, directory in STAGE_DIRS.items():
        if key in name:
            return directory / path.name
    return DOCS / "changelog" / path.name


def migrate() -> int:
    moved = 0
    for path in ROOT.glob("README_STAGE*.md"):
        target = target_for(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            path.unlink()
        else:
            shutil.move(str(path), str(target))
        moved += 1
    print(f"Stage-18.6 Documentation Center migration completed. Files processed: {moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(migrate())
