"""NTPE Provider Configuration Audit.

TER-v2.3 adds a read-only provider configuration audit layer. The tool does not
modify runtime code, provider code, or environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER_CONFIG = ROOT / "config" / "provider_config.json"

SECRET_PATTERNS: Sequence[tuple[str, re.Pattern[str]]] = (
    ("NVIDIA", re.compile(r"nvapi-[A-Za-z0-9_\-]{8,}")),
    ("OpenAI", re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("Gemini", re.compile(r"AIza[0-9A-Za-z_\-]{16,}")),
)

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "cache",
    "logs",
    "output",
    "translated",
    "backup",
    "failed_chunks",
}

LEGACY_CONFIG_FILES = (
    Path("config/config.json"),
    Path("config/default_config.json"),
)

RUNTIME_CHAIN_FILES = (
    Path("launcher_translate.py"),
    Path("ntpe_production_translate.py"),
    Path("core/translation_runtime/__init__.py"),
    Path("core/translation_engine/translation_engine.py"),
    Path("core/translation_engine/provider_runtime.py"),
)


@dataclass(frozen=True)
class AuditItem:
    name: str
    status: str
    detail: str = ""


def _status_rank(status: str) -> int:
    return {"PASS": 0, "WARN": 1, "FAIL": 2}.get(status, 2)


def load_provider_config(path: Path = PROVIDER_CONFIG) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing provider config: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("provider_config.json must contain a JSON object")
    return data


def iter_scan_files(root: Path = ROOT) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in {".py", ".json", ".env", ".txt", ".md"}:
            continue
        yield path


def check_provider_config() -> AuditItem:
    try:
        data = load_provider_config()
    except Exception as exc:  # pragma: no cover - detail path
        return AuditItem("Provider Config", "FAIL", str(exc))

    providers = data.get("providers")
    if not isinstance(providers, dict) or not providers:
        return AuditItem("Provider Config", "FAIL", "providers section missing or empty")

    missing = []
    for provider, config in providers.items():
        if not isinstance(config, dict) or not config.get("env_var"):
            missing.append(provider)
    if missing:
        return AuditItem("Provider Config", "FAIL", f"missing env_var: {', '.join(missing)}")

    default_provider = data.get("default_provider", "")
    if default_provider and default_provider not in providers:
        return AuditItem("Provider Config", "FAIL", f"default provider not in providers: {default_provider}")
    return AuditItem("Provider Config", "PASS", f"providers={len(providers)} default={default_provider or 'unset'}")


def check_environment(required_provider: str = "nvidia") -> AuditItem:
    try:
        data = load_provider_config()
    except Exception as exc:
        return AuditItem("Environment Variables", "FAIL", str(exc))
    providers = data.get("providers", {})
    provider_config = providers.get(required_provider)
    if not isinstance(provider_config, dict):
        return AuditItem("Environment Variables", "FAIL", f"provider not found: {required_provider}")
    env_var = provider_config.get("env_var")
    if not env_var:
        return AuditItem("Environment Variables", "FAIL", f"env_var missing for {required_provider}")
    value = os.getenv(env_var, "")
    if not value:
        return AuditItem("Environment Variables", "WARN", f"{env_var} not set")
    return AuditItem("Environment Variables", "PASS", f"{env_var} set")


def scan_hardcoded_keys(root: Path = ROOT) -> AuditItem:
    production_hits: list[str] = []
    fixture_hits: list[str] = []
    for path in iter_scan_files(root):
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        is_fixture = "tests" in rel.parts or rel.name.endswith("_test.py")
        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                hit = f"{rel}:{line_no}:{label}"
                if is_fixture:
                    fixture_hits.append(hit)
                else:
                    production_hits.append(hit)
    if production_hits:
        preview = "; ".join(production_hits[:8])
        suffix = "" if len(production_hits) <= 8 else f"; +{len(production_hits) - 8} more"
        return AuditItem("Hardcoded API Keys", "FAIL", preview + suffix)
    if fixture_hits:
        return AuditItem("Hardcoded API Keys", "PASS", f"production clean; ignored {len(fixture_hits)} test fixture literals")
    return AuditItem("Hardcoded API Keys", "PASS", "no key-like literals found")


def check_legacy_config(root: Path = ROOT) -> AuditItem:
    warnings: list[str] = []
    for rel in LEGACY_CONFIG_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "api_key" in text or "自行輸入" in text or "API_KEY" in text:
            warnings.append(str(rel))
    if warnings:
        return AuditItem("Legacy Config", "WARN", "legacy api_key fields: " + ", ".join(warnings))
    return AuditItem("Legacy Config", "PASS", "no legacy api_key config detected")


def check_runtime_provider_path(root: Path = ROOT) -> AuditItem:
    missing = [str(rel) for rel in RUNTIME_CHAIN_FILES if not (root / rel).exists()]
    if missing:
        return AuditItem("Runtime Provider Path", "FAIL", "missing: " + ", ".join(missing))
    provider_runtime = root / "core" / "translation_engine" / "provider_runtime.py"
    text = provider_runtime.read_text(encoding="utf-8", errors="ignore")
    if "provider_config.json" not in text and "PROVIDER_CONFIG" not in text:
        return AuditItem("Runtime Provider Path", "WARN", "provider_runtime exists but config load path is not explicit")
    return AuditItem("Runtime Provider Path", "PASS", "production provider runtime present")


def check_provider_imports(root: Path = ROOT) -> AuditItem:
    direct_calls: list[str] = []
    for rel in (Path("launcher_translate.py"), Path("ntpe_production_translate.py"), Path("lts/txt_translation_runtime.py"), Path("lts/batch_translation_runtime.py")):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "requests.post" in text or "integrate.api.nvidia.com" in text:
            direct_calls.append(str(rel))
    if direct_calls:
        return AuditItem("Provider Imports", "WARN", "direct provider calls: " + ", ".join(direct_calls))
    return AuditItem("Provider Imports", "PASS", "launcher/runtime do not directly call provider HTTP API")


def run_audit(required_provider: str = "nvidia") -> list[AuditItem]:
    return [
        check_provider_config(),
        check_environment(required_provider),
        scan_hardcoded_keys(),
        check_legacy_config(),
        check_runtime_provider_path(),
        check_provider_imports(),
    ]


def print_report(items: Sequence[AuditItem]) -> int:
    print("======================================")
    print("NTPE Provider Configuration Audit")
    print("======================================")
    print()
    for item in items:
        line = f"{item.name:<28} {item.status}"
        if item.detail:
            line += f"  {item.detail}"
        print(line)
    print()
    worst = max((_status_rank(item.status) for item in items), default=2)
    overall = "FAIL" if worst == 2 else "PASS_WITH_WARNINGS" if worst == 1 else "PASS"
    print(f"OVERALL {overall}")
    return 1 if worst == 2 else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit NTPE provider configuration without modifying runtime code.")
    parser.add_argument("--provider", default="nvidia", help="provider to treat as required for environment checks")
    parser.add_argument("--strict", action="store_true", help="treat warnings as non-zero exit")
    args = parser.parse_args(argv)
    items = run_audit(args.provider)
    code = print_report(items)
    if args.strict and any(item.status != "PASS" for item in items):
        return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
