from __future__ import annotations

import argparse
from pathlib import Path

from .inventory import generate_batch1_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the read-only TIC Batch 1 inventory")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    paths = generate_batch1_artifacts(args.root)
    for path in paths:
        print(path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
