# =====================================================
# NTPE 1.2 Professional Stage-12
# Plugin Marketplace CLI / Repository Commands
# =====================================================

from __future__ import annotations

from pathlib import Path

from core.translation_plugins.marketplace import run_cli

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    raise SystemExit(run_cli(default_root=ROOT))
