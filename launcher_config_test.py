from pathlib import Path

from core.config import ConfigManager

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    cfg = ConfigManager(ROOT)

    checks = {
        "App Name": cfg.app_name == "NTPE",
        "Version": bool(cfg.version),
        "Provider": cfg.provider == "nvidia",
        "Model": bool(cfg.model),
        "Target Language": cfg.target_language == "zh-TW",
        "Timeout": cfg.timeout > 0,
        "RPM Limit": cfg.rpm_limit > 0,
        "Chunk Size": cfg.chunk_size > 0,
        "Context Size": cfg.context_size > 0,
    }

    print("NTPE v1.2 Foundation Configuration Center Test")
    print("==============================================")

    for name, ok in checks.items():
        print(f"{name:<18} {'PASS' if ok else 'FAIL'}")

    print(f"version: {cfg.version}")
    print(f"model: {cfg.model}")

    if not all(checks.values()):
        print("FAIL")
        raise SystemExit(2)

    print("PASS")