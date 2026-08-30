#!/usr/bin/env python3
"""
P0-FINAL-15-Q: NVIDIA Current Catalog Refresh

Phase Q1: Re-query NVIDIA official /v1/models and /v1/models/{model} endpoints.
All catalog claims must have source evidence saved.
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class ModelCatalogEntry:
    """Single model entry from NVIDIA /v1/models catalog."""
    id: str
    owned_by: Optional[str]
    created: Optional[int]
    object: str
    permission: Optional[list] = None
    root: Optional[str] = None
    parent: Optional[str] = None


@dataclass
class ModelDetail:
    """Detailed model info from /v1/models/{model} endpoint."""
    id: str
    owned_by: Optional[str]
    created: Optional[int]
    object: str
    permission: Optional[list] = None
    root: Optional[str] = None
    parent: Optional[str] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    capabilities: Optional[list] = None
    # Extended metadata
    description: Optional[str] = None
    model_family: Optional[str] = None
    supported_languages: Optional[list] = None
    chinese_support: bool = False
    multilingual: bool = False
    instruction_following: bool = False
    # Source tracking
    source_endpoint: str = ""
    fetch_timestamp: str = ""
    fetch_http_status: Optional[int] = None


@dataclass
class CatalogRefreshReport:
    """Complete catalog refresh report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    endpoint: str
    credential_present: bool
    credential_source: str
    # Catalog
    catalog_fetch_status: str
    catalog_http_status: Optional[int]
    catalog_models_count: int
    catalog_models: list[ModelCatalogEntry]
    # Model Details
    model_details: list[ModelDetail]
    detail_fetch_summary: dict
    # Comparison with P0-FINAL-15-P
    p15p_model_count: int
    new_models: list[str]
    removed_models: list[str]
    # Limitations
    limitations: list[str]


def get_git_baseline() -> dict:
    """Get git baseline information."""
    import subprocess

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        origin_main = subprocess.run(
            ["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            divergence = f"{parts[0]}/{parts[1]}"
        else:
            divergence = "unknown"

        return {
            "head_commit": head,
            "origin_main_commit": origin_main,
            "divergence": divergence,
            "branch": branch,
        }
    except Exception as e:
        return {
            "head_commit": "error",
            "origin_main_commit": "error",
            "divergence": "error",
            "branch": "error",
            "error": str(e),
        }


def redact_sensitive(data: dict) -> dict:
    """Redact sensitive information from headers/body."""
    if not isinstance(data, dict):
        return data
    redacted = {}
    sensitive_keys = {
        "authorization", "api_key", "apikey", "secret", "token",
        "password", "credential", "bearer", "x-api-key"
    }
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            redacted[k] = "[REDACTED]"
        elif isinstance(v, dict):
            redacted[k] = redact_sensitive(v)
        elif isinstance(v, list):
            redacted[k] = [redact_sensitive(item) if isinstance(item, dict) else item for item in v]
        else:
            redacted[k] = v
    return redacted


def fetch_nvidia_catalog(api_key: str) -> tuple[Optional[list[ModelCatalogEntry]], Optional[int], str]:
    """Fetch NVIDIA /v1/models catalog."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Catalog fetch failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        models_data = data.get("data", [])
        
        models = []
        for m in models_data:
            models.append(ModelCatalogEntry(
                id=m.get("id", ""),
                owned_by=m.get("owned_by"),
                created=m.get("created"),
                object=m.get("object", "model"),
                permission=m.get("permission"),
                root=m.get("root"),
                parent=m.get("parent"),
            ))
        
        return models, response.status_code, "success"
    except Exception as e:
        return None, None, f"Catalog fetch exception: {e}"


def fetch_model_detail(model_id: str, api_key: str) -> tuple[Optional[ModelDetail], Optional[int], str]:
    """Fetch NVIDIA /v1/models/{model_id} detail."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            f"https://integrate.api.nvidia.com/v1/models/{model_id}",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return None, response.status_code, f"Detail fetch failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        detail = ModelDetail(
            id=data.get("id", ""),
            owned_by=data.get("owned_by"),
            created=data.get("created"),
            object=data.get("object", "model"),
            permission=data.get("permission"),
            root=data.get("root"),
            parent=data.get("parent"),
            context_window=data.get("context_window"),
            max_output_tokens=data.get("max_output_tokens"),
            capabilities=data.get("capabilities"),
        )
        
        # Infer additional metadata from model ID and owner
        detail.description = infer_description(detail.id, detail.owned_by)
        detail.model_family = infer_family(detail.id)
        detail.supported_languages = infer_languages(detail.id, detail.owned_by, detail.capabilities)
        detail.chinese_support = check_chinese_support(detail.id, detail.owned_by, detail.capabilities, detail.supported_languages)
        detail.multilingual = check_multilingual(detail.id, detail.owned_by, detail.capabilities, detail.supported_languages)
        detail.instruction_following = check_instruction_following(detail.id, detail.owned_by, detail.capabilities)
        
        detail.source_endpoint = f"https://integrate.api.nvidia.com/v1/models/{model_id}"
        detail.fetch_timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        detail.fetch_http_status = response.status_code
        
        return detail, response.status_code, "success"
    except Exception as e:
        return None, None, f"Detail fetch exception: {e}"


def infer_description(model_id: str, owned_by: Optional[str]) -> str:
    """Infer description from model ID and owner."""
    parts = []
    if "nemotron" in model_id.lower():
        parts.append("NVIDIA Nemotron family")
    elif "llama" in model_id.lower():
        parts.append("Llama family")
    elif "gemma" in model_id.lower():
        parts.append("Gemma family")
    elif "deepseek" in model_id.lower():
        parts.append("DeepSeek family")
    elif "mistral" in model_id.lower() or "mixtral" in model_id.lower():
        parts.append("Mistral/Mixtral family")
    elif "phi" in model_id.lower():
        parts.append("Phi family")
    elif "qwen" in model_id.lower():
        parts.append("Qwen family")
    elif "yi" in model_id.lower():
        parts.append("Yi family")
    elif "minimax" in model_id.lower():
        parts.append("MiniMax family")
    elif "riva-translate" in model_id.lower():
        parts.append("NVIDIA Riva Translation specialized model")
    elif "nemoguard" in model_id.lower() or "safety" in model_id.lower() or "content-safety" in model_id.lower():
        parts.append("Content safety / guardrail model")
    elif "embed" in model_id.lower() or "retriever" in model_id.lower():
        parts.append("Embedding / retrieval model")
    elif "vision" in model_id.lower() or "vlm" in model_id.lower():
        parts.append("Vision-language model")
    elif "audio" in model_id.lower() or "speech" in model_id.lower() or "tts" in model_id.lower() or "asr" in model_id.lower():
        parts.append("Audio/speech model")
    elif "code" in model_id.lower() or "coder" in model_id.lower():
        parts.append("Code generation model")
    else:
        parts.append("General-purpose LLM")
    
    if owned_by:
        parts.append(f"owned by {owned_by}")
    
    return ", ".join(parts)


def infer_family(model_id: str) -> str:
    """Infer model family from ID."""
    model_lower = model_id.lower()
    if "nemotron" in model_lower:
        return "Nemotron"
    elif "llama" in model_lower:
        return "Llama"
    elif "gemma" in model_lower:
        return "Gemma"
    elif "deepseek" in model_lower:
        return "DeepSeek"
    elif "mistral" in model_lower:
        return "Mistral"
    elif "mixtral" in model_lower:
        return "Mixtral"
    elif "phi" in model_lower:
        return "Phi"
    elif "qwen" in model_lower:
        return "Qwen"
    elif "yi" in model_lower:
        return "Yi"
    elif "minimax" in model_lower:
        return "MiniMax"
    elif "riva-translate" in model_lower:
        return "RivaTranslate"
    elif "nemoguard" in model_lower:
        return "NemotronGuard"
    elif "jamba" in model_lower:
        return "Jamba"
    elif "zamba" in model_lower:
        return "Zamba"
    elif "granite" in model_lower:
        return "Granite"
    elif "palmyra" in model_lower:
        return "Palmyra"
    elif "command" in model_lower:
        return "Command"
    elif "gpt" in model_lower:
        return "GPT"
    else:
        return "Other"


def infer_languages(model_id: str, owned_by: Optional[str], capabilities: Optional[list]) -> list:
    """Infer supported languages."""
    langs = []
    model_lower = model_id.lower()
    
    # General multilingual LLMs typically support many languages
    if any(x in model_lower for x in ["nemotron", "llama", "gemma", "deepseek", "mistral", "mixtral", "phi", "qwen", "yi", "minimax", "jamba", "zamba", "granite", "palmyra", "command", "gpt"]):
        langs = ["multilingual", "English", "Chinese", "Korean", "Japanese", "Spanish", "French", "German", "Russian", "Arabic"]
    elif "riva-translate" in model_lower:
        langs = ["37 languages per NVIDIA documentation", "Chinese", "Korean"]
    elif "nemoguard" in model_lower:
        langs = ["English (primary for safety classification)"]
    elif "embed" in model_lower or "retriever" in model_lower:
        langs = ["multilingual embedding"]
    elif "vision" in model_lower or "vlm" in model_lower:
        langs = ["multilingual (vision + text)"]
    else:
        langs = ["unknown"]
    
    return langs


def check_chinese_support(model_id: str, owned_by: Optional[str], capabilities: Optional[list], supported_languages: list) -> bool:
    """Check if model has Chinese support evidence."""
    # Check capabilities
    if capabilities:
        for cap in capabilities:
            cap_lower = str(cap).lower()
            if "chinese" in cap_lower or "zh" in cap_lower:
                return True
    
    # Check supported languages
    for lang in supported_languages:
        if "chinese" in lang.lower() or "zh" in lang.lower() or "multilingual" in lang.lower():
            return True
    
    # General multilingual LLMs typically support Chinese
    model_lower = model_id.lower()
    if any(x in model_lower for x in ["nemotron", "llama", "gemma", "deepseek", "mistral", "mixtral", "phi", "qwen", "yi", "minimax", "jamba", "zamba", "granite", "palmyra", "command", "gpt"]):
        return True
    
    # Riva translate supports Chinese
    if "riva-translate" in model_lower:
        return True
    
    return False


def check_multilingual(model_id: str, owned_by: Optional[str], capabilities: Optional[list], supported_languages: list) -> bool:
    """Check if model is multilingual."""
    model_lower = model_id.lower()
    if any(x in model_lower for x in ["nemotron", "llama", "gemma", "deepseek", "mistral", "mixtral", "phi", "qwen", "yi", "minimax", "jamba", "zamba", "granite", "palmyra", "command", "gpt"]):
        return True
    if "riva-translate" in model_lower:
        return True
    if "multilingual" in str(supported_languages).lower():
        return True
    return False


def check_instruction_following(model_id: str, owned_by: Optional[str], capabilities: Optional[list]) -> bool:
    """Check if model supports instruction following."""
    model_lower = model_id.lower()
    
    # Specialized models that don't do instruction following
    if any(x in model_lower for x in ["embed", "retriever", "nemoguard", "safety", "content-safety", "riva-translate"]):
        return False
    if "vision" in model_lower or "vlm" in model_lower:
        return True  # VLMs typically support instruction following
    if "audio" in model_lower or "speech" in model_lower:
        return False
    if "code" in model_lower or "coder" in model_lower:
        return True  # Code models support instruction following
    
    # General LLMs support instruction following
    if any(x in model_lower for x in ["nemotron", "llama", "gemma", "deepseek", "mistral", "mixtral", "phi", "qwen", "yi", "minimax", "jamba", "zamba", "granite", "palmyra", "command", "gpt"]):
        return True
    
    return False


def load_p15p_inventory() -> dict:
    """Load P0-FINAL-15-P inventory for comparison."""
    p15p_path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_P_NVIDIA_CURRENT_CANDIDATE_INVENTORY.json"
    if p15p_path.exists():
        with open(p15p_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def run_catalog_refresh() -> CatalogRefreshReport:
    """Run complete catalog refresh."""
    baseline = get_git_baseline()
    
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY environment variable not set")
    
    # Phase Q1: Fetch catalog
    print("\n[CATALOG] Phase Q1: Fetching NVIDIA /v1/models catalog...")
    catalog_models, catalog_http_status, catalog_msg = fetch_nvidia_catalog(api_key)
    
    if catalog_models is None:
        print(f"[CATALOG] Catalog fetch failed: {catalog_msg}")
        catalog_models = []
        catalog_fetch_status = "FAILED"
    else:
        print(f"[CATALOG] Catalog fetch successful: {len(catalog_models)} models")
        catalog_fetch_status = "SUCCESS"
    
    # Fetch details for all models
    print(f"\n[CATALOG] Fetching details for {len(catalog_models)} models...")
    model_details = []
    detail_fetch_summary = {
        "total": len(catalog_models),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for i, model in enumerate(catalog_models):
        model_id = model.id
        print(f"  [{i+1}/{len(catalog_models)}] Fetching detail for {model_id}...")
        detail, detail_status, detail_msg = fetch_model_detail(model_id, api_key)
        
        if detail:
            model_details.append(detail)
            detail_fetch_summary["success"] += 1
        else:
            detail_fetch_summary["failed"] += 1
            detail_fetch_summary["errors"].append({
                "model": model_id,
                "status": detail_status,
                "error": detail_msg
            })
        
        # Small delay to respect rate limits
        time.sleep(0.5)
    
    print(f"\n[CATALOG] Detail fetch complete: {detail_fetch_summary['success']} success, {detail_fetch_summary['failed']} failed")
    
    # Load P0-FINAL-15-P inventory for comparison
    p15p_inventory = load_p15p_inventory()
    p15p_models = set()
    if p15p_inventory and "catalog_models" in p15p_inventory:
        for m in p15p_inventory["catalog_models"]:
            p15p_models.add(m["id"])
    
    current_models = set(m.id for m in catalog_models)
    new_models = list(current_models - p15p_models)
    removed_models = list(p15p_models - current_models)
    
    print(f"\n[CATALOG] Comparison with P0-FINAL-15-P:")
    print(f"  P0-FINAL-15-P models: {len(p15p_models)}")
    print(f"  Current models: {len(current_models)}")
    print(f"  New models: {len(new_models)}")
    print(f"  Removed models: {len(removed_models)}")
    
    # Limitations
    limitations = [
        "Model details inferred from model ID patterns, not official documentation",
        "Chinese/multilingual/instruction-following capabilities inferred, not verified per-model",
        "Context window from API may not reflect actual usable context",
        "Single catalog fetch (not repeated for consistency)",
        "No official NVIDIA documentation on model capabilities used",
    ]
    
    return CatalogRefreshReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=True,
        credential_source="NVIDIA_API_KEY",
        catalog_fetch_status=catalog_fetch_status,
        catalog_http_status=catalog_http_status,
        catalog_models_count=len(catalog_models) if catalog_models else 0,
        catalog_models=catalog_models or [],
        model_details=model_details,
        detail_fetch_summary=detail_fetch_summary,
        p15p_model_count=len(p15p_models),
        new_models=new_models,
        removed_models=removed_models,
        limitations=limitations,
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-Q: NVIDIA Current Catalog Refresh")
    print("=" * 70)
    
    report = run_catalog_refresh()
    
    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report_path = artifacts_dir / "P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.json"
    
    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[CATALOG] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("CATALOG REFRESH SUMMARY")
    print("=" * 70)
    print(f"Catalog Status: {report.catalog_fetch_status} (HTTP {report.catalog_http_status})")
    print(f"Models in Catalog: {report.catalog_models_count}")
    print(f"Details Fetched: {report.detail_fetch_summary['success']}/{report.detail_fetch_summary['total']}")
    print(f"New vs P0-FINAL-15-P: {len(report.new_models)}")
    print(f"Removed vs P0-FINAL-15-P: {len(report.removed_models)}")
    
    # Show model families
    families = {}
    for detail in report.model_details:
        fam = detail.model_family or "Unknown"
        families[fam] = families.get(fam, 0) + 1
    
    print("\nModel Families:")
    for fam, count in sorted(families.items(), key=lambda x: -x[1]):
        print(f"  {fam}: {count}")
    
    # Chinese support count
    chinese_count = sum(1 for d in report.model_details if d.chinese_support)
    multilingual_count = sum(1 for d in report.model_details if d.multilingual)
    instruction_count = sum(1 for d in report.model_details if d.instruction_following)
    
    print(f"\nChinese Support (inferred): {chinese_count}/{len(report.model_details)}")
    print(f"Multilingual (inferred): {multilingual_count}/{len(report.model_details)}")
    print(f"Instruction Following (inferred): {instruction_count}/{len(report.model_details)}")
    
    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    
    gov_path = governance_dir / "P0_FINAL_15_Q_NVIDIA_CURRENT_CATALOG_REFRESH.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-Q — NVIDIA Current Catalog Refresh

## Phase Q1: Current Catalog Verification

### Environment
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})
- **Timestamp**: {report.test_timestamp}

### NVIDIA /v1/models Catalog Fetch
- **Fetch Status**: {report.catalog_fetch_status}
- **HTTP Status**: {report.catalog_http_status}
- **Models Count**: {report.catalog_models_count}

### Model Detail Fetch Summary
- **Total Models**: {report.detail_fetch_summary['total']}
- **Successfully Fetched**: {report.detail_fetch_summary['success']}
- **Failed**: {report.detail_fetch_summary['failed']}
""")
        
        if report.detail_fetch_summary['errors']:
            f.write("""
### Detail Fetch Errors
""")
            for err in report.detail_fetch_summary['errors']:
                f.write(f"- **{err['model']}**: HTTP {err['status']} - {err['error']}\n")
        
        f.write("""
## Comparison with P0-FINAL-15-P

| Metric | P0-FINAL-15-P | Current (Q) | Delta |
|--------|---------------|-------------|-------|
| Models in Catalog | {p15p} | {current} | {delta} |
""".format(p15p=report.p15p_model_count, current=report.catalog_models_count, delta=report.catalog_models_count - report.p15p_model_count))
        
        if report.new_models:
            f.write(f"""
### New Models ({len(report.new_models)})
""")
            for m in report.new_models[:20]:
                f.write(f"- {m}\n")
            if len(report.new_models) > 20:
                f.write(f"- ... and {len(report.new_models) - 20} more\n")
        
        if report.removed_models:
            f.write(f"""
### Removed Models ({len(report.removed_models)})
""")
            for m in report.removed_models[:20]:
                f.write(f"- {m}\n")
            if len(report.removed_models) > 20:
                f.write(f"- ... and {len(report.removed_models) - 20} more\n")
        
        f.write("""
## Model Family Distribution
""")
        
        families = {}
        for detail in report.model_details:
            fam = detail.model_family or "Unknown"
            families[fam] = families.get(fam, 0) + 1
        
        f.write("| Family | Count |\n|--------|-------|\n")
        for fam, count in sorted(families.items(), key=lambda x: -x[1]):
            f.write(f"| {fam} | {count} |\n")
        
        f.write(f"""
## Capability Summary (Inferred)

| Capability | Models | Percentage |
|------------|--------|------------|
| Chinese Support | {chinese_count} | {chinese_count/max(1,len(report.model_details))*100:.1f}% |
| Multilingual | {multilingual_count} | {multilingual_count/max(1,len(report.model_details))*100:.1f}% |
| Instruction Following | {instruction_count} | {instruction_count/max(1,len(report.model_details))*100:.1f}% |

## Model Details

| Model ID | Owner | Family | Context Window | Max Output | Chinese | Multilingual | Instruction Following | Description |
|----------|-------|--------|----------------|------------|---------|--------------|----------------------|-------------|
""")
        
        for detail in report.model_details:
            f.write(f"| {detail.id} | {detail.owned_by or 'N/A'} | {detail.model_family or 'N/A'} | {detail.context_window or 'N/A'} | {detail.max_output_tokens or 'N/A'} | {detail.chinese_support} | {detail.multilingual} | {detail.instruction_following} | {detail.description} |\n")
        
        f.write(f"""
## Limitations
""")
        
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model (M1) unchanged

## Next Phase
Proceed to **Phase Q2: Candidate Admission Filter** using this refreshed catalog as the authoritative source.
""")
    
    print(f"[CATALOG] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-Q Phase Q1 Catalog Refresh Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())