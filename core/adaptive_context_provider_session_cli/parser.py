from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TE v7 Stage 10.3 controlled mock-only Provider benchmark session harness")
    parser.add_argument("--enable-controlled-session", action="store_true")
    parser.add_argument("--pair-id", default="")
    parser.add_argument("--run-kind", choices=("baseline", "candidate"), default="baseline")
    parser.add_argument("--set-name", default="")
    parser.add_argument("--chunk-index", type=int, default=1)
    parser.add_argument("--source-hash", default="")
    parser.add_argument("--chunk-hash", default="")
    parser.add_argument("--model", default="mock-provider-model")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--estimated-input-tokens", type=int, default=0)
    parser.add_argument("--estimated-output-tokens", type=int, default=0)
    parser.add_argument("--minimum-output-tokens", type=int, default=0)
    parser.add_argument("--attempt", action="append", default=[], metavar="MODEL|TIMEOUT|FALLBACK")
    parser.add_argument("--mock-outcome", action="append", choices=("success", "timeout", "503", "failed"), default=[])
    parser.add_argument("--mock-output-tokens", action="append", type=int, default=[])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--report", default="")
    return parser
