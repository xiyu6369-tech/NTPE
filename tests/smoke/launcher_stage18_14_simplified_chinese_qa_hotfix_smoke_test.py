from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ntpe_production_translate import build_parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(["batch", "input", "output", "--profile", "fast", "--simplified-chinese-policy", "normalize", "--dry-run"])
    ok = args.command == "batch" and args.simplified_chinese_policy == "normalize"
    print("Stage-18.14 Smoke", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
