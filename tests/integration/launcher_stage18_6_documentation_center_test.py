from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(path: str) -> None:
    full = ROOT / path
    print(f"{path:<46} {'PASS' if full.exists() else 'FAIL'}")
    if not full.exists():
        raise SystemExit(1)


def main() -> int:
    print("NTPE Stage-18.6 Documentation Center Integration Test")
    print("=" * 60)
    for path in [
        "docs/README.md",
        "docs/stages/stage18/README.md",
        "docs/stages/stage18/18.6.md",
        "docs/enterprise/Deployment.md",
        "docs/freeze/Foundation.md",
        "docs/roadmap/NTPE-1.x.md",
    ]:
        require(path)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
