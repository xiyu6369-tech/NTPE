#!/usr/bin/env python3
"""
NTPE Translation Studio — Root Launcher

This is the official user entry point for NTPE Translation Studio.
It delegates to the UI shell in ui.translation_studio.app.
"""

from __future__ import annotations

def main() -> int:
    """Launch NTPE Translation Studio UI."""
    from ui.translation_studio.app import run
    return run()


if __name__ == "__main__":
    import sys
    sys.exit(main())