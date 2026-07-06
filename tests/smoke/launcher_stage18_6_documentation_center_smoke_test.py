from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    print("NTPE Stage-18.6 Documentation Center Smoke Test")
    docs = ROOT / "docs"
    ok = docs.is_dir() and (docs / "README.md").is_file() and (ROOT / "README.md").is_file()
    print(f"Documentation Center           {'PASS' if ok else 'FAIL'}")
    if not ok:
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
