from pathlib import Path
import json

from core.voice.voice_profile import VoiceProfile
from core.voice.voice_memory import VoiceMemory

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    text = """
정태의는 현관 쪽을 바라보았다.
삼촌은 조용히 웃었다.
일라이는 아무 말 없이 그를 바라보았다.
"""

    profile = VoiceProfile(ROOT)
    matches = profile.match(text)
    rules = profile.build_prompt_rules(matches)

    memory = VoiceMemory(ROOT)
    memory_data = memory.update_seen(
        matches,
        file_name="voice_test.txt",
        chunk_index=1,
    )

    out = ROOT / "prompt_packages" / "character_voice_test_package.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "matches": matches,
                "prompt_rules": rules,
                "memory": memory_data,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    required = {"鄭泰義", "叔叔", "伊萊"}
    found = {item["target_name"] for item in matches}

    print("NTPE v1.1 / TQF-06.3 Character Voice Engine")
    print("===========================================")
    print(f"matches: {len(matches)}")
    print(f"rules: {len(rules)}")
    print(f"found: {', '.join(sorted(found))}")
    print(f"package: {out}")

    if not required.issubset(found):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")