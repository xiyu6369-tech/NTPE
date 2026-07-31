from __future__ import annotations

import json
from pathlib import Path

from core.adaptive_context_authorized_provider_cli import run_from_argv

ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    result = run_from_argv(root=ROOT)
    print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
