from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    client = ROOT / "core" / "translation_engine" / "nvidia_client.py"
    cli = ROOT / "ntpe_production_translate.py"
    assert client.exists()
    assert cli.exists()
    data = client.read_text(encoding="utf-8")
    assert "NVIDIA API timeout after" in data
    assert "RequestException" in data
    assert "[NTPE DEBUG] NVIDIA request start" in data
    cli_data = cli.read_text(encoding="utf-8")
    assert "NTPE_API_TIMEOUT" in cli_data
    print("Integration Stage-18.11 PASS")
    print("PASS")


if __name__ == "__main__":
    main()
