from pathlib import Path


def main():
    root = Path.cwd()
    cli = (root / "ntpe_production_translate.py").read_text(encoding="utf-8")
    client = (root / "core" / "translation_engine" / "nvidia_client.py").read_text(encoding="utf-8")
    assert "--api-timeout" in cli
    assert "Golden_Set" in cli
    assert "Increase the read timeout" in client
    assert "請檢查網路" not in client
    print("PS-04.1 Integration PASS")
    print("PASS")


if __name__ == "__main__":
    main()
