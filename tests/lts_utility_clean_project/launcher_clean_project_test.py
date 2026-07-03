from pathlib import Path
from tempfile import TemporaryDirectory
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.clean_project import clean_project


def main() -> int:
    with TemporaryDirectory() as temp:
        root = Path(temp) / "NTPE"
        root.mkdir()
        (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        (root / "launcher.py").write_text("print('ntpe')\n", encoding="utf-8")
        (root / "input").mkdir()
        (root / "input" / "sample.txt").write_text("sample", encoding="utf-8")
        result = clean_project(root, dry_run=False)
        checks = {
            "Cleaner Ran": result.changed_count > 0,
            "Input Preserved": (root / "input").exists(),
            "Gitkeep Created": (root / "input" / ".gitkeep").exists(),
            "Sample Removed": not (root / "input" / "sample.txt").exists(),
        }
        print("NTPE 1.1 LTS Clean Project Tool Test")
        print("====================================")
        for name, passed in checks.items():
            print(f"{name:24} {'PASS' if passed else 'FAIL'}")
        if not all(checks.values()):
            return 1
        print("PASS")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
