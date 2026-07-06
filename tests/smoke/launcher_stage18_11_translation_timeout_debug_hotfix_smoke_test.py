from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    text = (ROOT / "core" / "translation_engine" / "nvidia_client.py").read_text(encoding="utf-8")
    assert "timeout=(self.connect_timeout, self.timeout)" in text
    assert "flush=True" in text
    print("Smoke Stage-18.11 PASS")
    print("PASS")


if __name__ == "__main__":
    main()
