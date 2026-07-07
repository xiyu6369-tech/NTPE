import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.literary import LiteraryPromptBuilder


def main() -> int:
    result = LiteraryPromptBuilder().build(
        chunk_text="정태의는 난감했다. 카일은 고개를 끄덕였다.",
        locked_dictionary={"정태의": "鄭泰義", "카일": "凱爾"},
        profile="fast",
    )
    ok = bool(result.system_prompt and result.user_prompt and "鄭泰義" in result.user_prompt and result.profile == "fast")
    print("NTPE PS-04 Smoke Test")
    print("=====================")
    print(f"Literary Prompt Builder {'PASS' if ok else 'FAIL'}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
