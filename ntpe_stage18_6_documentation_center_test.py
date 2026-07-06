from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED_DIRS = [
    "docs/architecture",
    "docs/developer",
    "docs/api",
    "docs/enterprise",
    "docs/deployment",
    "docs/release",
    "docs/roadmap",
    "docs/migration",
    "docs/freeze",
    "docs/changelog",
    "docs/stages/stage18",
]
REQUIRED_FILES = [
    "README.md",
    "docs/README.md",
    "docs/stages/README.md",
    "docs/stages/stage18/18.6.md",
    "docs/release/1.2-professional.md",
    "tools/stage18_6_documentation_center_migrate.py",
]


def check(label: str, ok: bool) -> None:
    print(f"{label:<34} {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)


def main() -> int:
    print("NTPE Stage-18.6 Documentation Center Test")
    print("=" * 48)
    for directory in REQUIRED_DIRS:
        check(directory, (ROOT / directory).is_dir())
    for file in REQUIRED_FILES:
        check(file, (ROOT / file).is_file())
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    check("Root README points to docs", "docs/" in readme)
    check("Docs center policy", "Root Directory Policy" in docs)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
