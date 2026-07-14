from __future__ import annotations

import argparse
from collections.abc import Sequence

from .config import AuthorizedProviderCliConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one explicitly authorized Stage 10 Provider session.",
    )
    parser.add_argument("--enable-boundary", action="store_true")
    parser.add_argument("--enable-real-provider", action="store_true")
    parser.add_argument("--authorization-id", default="")
    parser.add_argument("--execution-mode", choices=("fake", "real"), default="fake")
    parser.add_argument("--provider", default="nvidia")
    parser.add_argument(
        "--provider-url",
        default="https://integrate.api.nvidia.com/v1/chat/completions",
    )
    parser.add_argument("--model", default="meta/llama-3.3-70b-instruct")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--source-fingerprint", required=True)
    parser.add_argument("--chunk-fingerprint", required=True)
    parser.add_argument("--chunk-index", type=int, default=1)
    parser.add_argument("--report-path", default="")
    return parser


def parse_config(argv: Sequence[str] | None = None) -> AuthorizedProviderCliConfig:
    values = vars(build_parser().parse_args(argv))
    return AuthorizedProviderCliConfig(
        boundary_enabled=values["enable_boundary"],
        real_provider_enabled=values["enable_real_provider"],
        authorization_id=values["authorization_id"],
        execution_mode=values["execution_mode"],
        provider=values["provider"],
        provider_url=values["provider_url"],
        model=values["model"],
        session_id=values["session_id"],
        source_fingerprint=values["source_fingerprint"],
        chunk_fingerprint=values["chunk_fingerprint"],
        chunk_index=values["chunk_index"],
        report_path=values["report_path"],
    )
