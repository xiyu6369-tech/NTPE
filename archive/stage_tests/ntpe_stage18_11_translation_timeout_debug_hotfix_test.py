# NTPE 1.2 Stage-18.11 Translation Timeout & Debug Hotfix Test
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def assert_contains(path, text):
    data = path.read_text(encoding="utf-8")
    assert text in data, f"missing {text} in {path}"


def main():
    assert_contains(ROOT / "core" / "translation_engine" / "nvidia_client.py", "NTPE_TRANSLATE_DEBUG")
    assert_contains(ROOT / "core" / "translation_engine" / "nvidia_client.py", "NTPE_API_TIMEOUT")
    assert_contains(ROOT / "core" / "translation_engine" / "nvidia_client.py", "timeout=(self.connect_timeout, self.timeout)")
    assert_contains(ROOT / "core" / "translation_engine" / "translation_engine.py", "return 60")
    print("Stage-18.11 Translation Timeout Debug Hotfix PASS")
    print("PASS")


if __name__ == "__main__":
    main()
