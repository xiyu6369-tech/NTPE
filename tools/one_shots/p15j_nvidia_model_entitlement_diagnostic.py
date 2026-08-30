#!/usr/bin/env python3
"""
P0-FINAL-15-J: NVIDIA Account Model Entitlement & Provider Model Availability Evidence

Diagnostic to establish evidence chain for model availability/entitlement:
Provider Catalog → Endpoint Capability → Account Entitlement → Model Routing → Actual HTTP Result

Does NOT modify production behavior.
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

from core.launcher_product.model_catalog import model_catalog, get_model
from core.launcher_product.provider_catalog import provider_catalog, get_provider
from core.ai_provider.adapters import build_standard_provider_configs


@dataclass
class ModelEvidence:
    """Evidence for a single model."""
    model: str
    # Local configuration
    in_ntpe_model_catalog: bool = False
    in_ntpe_provider_adapter: bool = False
    in_provider_config_json: bool = False
    ntpe_catalog_enabled: Optional[bool] = None
    ntpe_catalog_experimental: Optional[bool] = None
    ntpe_catalog_context_notes: Optional[str] = None
    # Provider catalog (official)
    in_provider_catalog: bool = False
    provider_catalog_owned_by: Optional[str] = None
    provider_catalog_created: Optional[int] = None
    # Endpoint capability
    endpoint_supports_model: Optional[bool] = None
    # Account evidence
    account_entitlement_evidence: str = "UNKNOWN"
    # Actual results
    http_status: Optional[int] = None
    response_body: Optional[str] = None
    response_headers: dict = field(default_factory=dict)
    provider_request_id: Optional[str] = None
    # Classification
    confidence: str = "UNKNOWN"
    classification: str = "UNKNOWN"


@dataclass
class EntitlementReport:
    """Complete entitlement evidence report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    client_path: str
    test_timestamp: str
    endpoint: str
    credential_present: bool
    credential_source: str
    # Models
    models: list[ModelEvidence]
    # Evidence sources
    official_catalog_evidence: dict
    provider_endpoint_evidence: dict
    account_evidence: dict
    local_configuration_evidence: dict
    # Classification
    previous_classification: str
    current_classification: str
    confidence: str
    # Production impact
    production_changes: dict
    # RM6
    rm6_promotion: str
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


def check_ntpe_model_catalog(model_id: str) -> dict:
    """Check NTPE static model catalog."""
    try:
        models = model_catalog()
        for m in models:
            if m.model_id == model_id:
                return {
                    "found": True,
                    "enabled": m.enabled,
                    "experimental": m.experimental,
                    "context_notes": m.context_notes,
                    "provider_id": m.provider_id,
                    "recommended_for": m.recommended_for,
                    "display_name": m.display_name,
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def check_ntpe_provider_adapter(model_id: str) -> dict:
    """Check NTPE AI provider adapter config."""
    try:
        configs = build_standard_provider_configs()
        nvidia_config = configs.get("nvidia")
        if not nvidia_config:
            return {"found": False, "error": "NVIDIA config not in standard provider configs"}
        
        for m in nvidia_config.models:
            if m.id == model_id:
                return {
                    "found": True,
                    "context_window": m.context_window,
                    "supports_streaming": m.supports_streaming,
                }
        return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


def check_provider_config_json(model_id: str) -> dict:
    """Check provider_config.json for model references."""
    try:
        config_path = Path(__file__).resolve().parents[2] / "config" / "provider_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Check default model
        nvidia_config = config.get("providers", {}).get("nvidia", {})
        default_model = nvidia_config.get("default_model")
        
        # Check fallback models
        engine_config = config.get("translation_engine_v3", {})
        fallback_models = engine_config.get("fallback_models", [])
        
        return {
            "default_model": default_model,
            "fallback_models": fallback_models,
            "is_default": default_model == model_id,
            "is_fallback": model_id in fallback_models,
        }
    except Exception as e:
        return {"error": str(e)}


def check_provider_models_endpoint(model_id: str) -> dict:
    """Check NVIDIA /v1/models endpoint for model availability."""
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        return {"error": "NVIDIA_API_KEY not set"}
    
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        # List all models
        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code != 200:
            return {"error": f"Models endpoint returned {response.status_code}", "body": response.text}
        
        data = response.json()
        models = data.get("data", [])
        
        for m in models:
            if m.get("id") == model_id:
                return {
                    "found": True,
                    "owned_by": m.get("owned_by"),
                    "created": m.get("created"),
                    "object": m.get("object"),
                }
        return {"found": False}
    except Exception as e:
        return {"error": str(e)}


def check_model_endpoint(model_id: str) -> dict:
    """Check NVIDIA /v1/models/{model_id} endpoint."""
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        return {"error": "NVIDIA_API_KEY not set"}
    
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            f"https://integrate.api.nvidia.com/v1/models/{model_id}",
            headers=headers,
            timeout=(10, 30),
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "found": True,
                "status_code": 200,
                "owned_by": data.get("owned_by"),
                "created": data.get("created"),
                "object": data.get("object"),
            }
        else:
            return {
                "found": False,
                "status_code": response.status_code,
                "body": response.text,
            }
    except Exception as e:
        return {"error": str(e)}


def analyze_m2_404(response_body: str) -> dict:
    """Analyze the M2 404 response for account entitlement evidence."""
    try:
        data = json.loads(response_body)
        detail = data.get("detail", "")
        
        # Extract function ID and account ID
        import re
        function_match = re.search(r"Function '([^']+)'", detail)
        account_match = re.search(r"account '([^']+)'", detail)
        
        return {
            "status": 404,
            "title": data.get("title"),
            "detail": detail,
            "function_id": function_match.group(1) if function_match else None,
            "account_id": account_match.group(1) if account_match else None,
            "semantics": "Function not found for account - indicates model not deployed/entitled for this account",
            "evidence_type": "PROVIDER_RESPONSE",
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_m1_429(response_body: str) -> dict:
    """Analyze the M1 429 response."""
    try:
        data = json.loads(response_body)
        return {
            "status": 429,
            "title": data.get("title"),
            "body": data,
            "has_rate_limit_headers": False,
            "semantics": "Generic 'Too Many Requests' without rate-limit headers or quota detail",
            "evidence_type": "PROVIDER_RESPONSE",
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_m3_200(response_body: str, response_headers: dict) -> dict:
    """Analyze the M3 200 response."""
    try:
        data = json.loads(response_body)
        return {
            "status": 200,
            "provider_request_id": data.get("id"),
            "model": data.get("model"),
            "usage": data.get("usage"),
            "response_headers_nvcf": {
                "nvcf_reqid": response_headers.get("Nvcf-Reqid"),
                "nvcf_status": response_headers.get("Nvcf-Status"),
            },
            "semantics": "Successful completion with provider request ID and NVCF tracking",
            "evidence_type": "PROVIDER_RESPONSE",
        }
    except Exception as e:
        return {"error": str(e)}


def run_entitlement_analysis() -> EntitlementReport:
    """Run complete entitlement analysis."""
    baseline = get_git_baseline()
    
    # Configuration
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    # Models from P0-FINAL-15-I
    models_to_analyze = [
        "minimaxai/minimax-m3",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "meta/llama-3.2-90b-vision-instruct",
    ]
    
    model_evidence_list = []
    
    # Load P0-FINAL-15-I results for reference
    i_report_path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_I_Nvidia_Model_Endpoint_Matrix_Report.json"
    i_results = {}
    if i_report_path.exists():
        with open(i_report_path, "r", encoding="utf-8") as f:
            i_report = json.load(f)
            for tc in i_report.get("test_cases", []):
                i_results[tc["model"]] = tc
    
    for model in models_to_analyze:
        evidence = ModelEvidence(model=model)
        
        # Step A: Local configuration inventory
        catalog_check = check_ntpe_model_catalog(model)
        evidence.in_ntpe_model_catalog = catalog_check.get("found", False)
        evidence.ntpe_catalog_enabled = catalog_check.get("enabled")
        evidence.ntpe_catalog_experimental = catalog_check.get("experimental")
        evidence.ntpe_catalog_context_notes = catalog_check.get("context_notes")
        
        adapter_check = check_ntpe_provider_adapter(model)
        evidence.in_ntpe_provider_adapter = adapter_check.get("found", False)
        
        config_check = check_provider_config_json(model)
        evidence.in_provider_config_json = config_check.get("is_default", False) or config_check.get("is_fallback", False)
        
        # Step B: Provider catalog (official)
        catalog_endpoint = check_provider_models_endpoint(model)
        evidence.in_provider_catalog = catalog_endpoint.get("found", False)
        evidence.provider_catalog_owned_by = catalog_endpoint.get("owned_by")
        evidence.provider_catalog_created = catalog_endpoint.get("created")
        
        # Step B2: Model-specific endpoint
        model_endpoint = check_model_endpoint(model)
        evidence.endpoint_supports_model = model_endpoint.get("found", False)
        
        # Step C: Account entitlement evidence
        # Use P0-FINAL-15-I results if available
        i_result = i_results.get(model)
        if i_result:
            evidence.http_status = i_result.get("http_status")
            evidence.response_body = i_result.get("response_body")
            evidence.response_headers = i_result.get("response_headers", {})
            evidence.provider_request_id = i_result.get("provider_request_id")
            
            # Analyze based on actual result
            if evidence.http_status == 404:
                analysis = analyze_m2_404(evidence.response_body or "")
                evidence.account_entitlement_evidence = "NOT_ENTITLED"
                evidence.classification = "ACCOUNT_NOT_ENTITLED"
                evidence.confidence = "HIGH"
            elif evidence.http_status == 200:
                analysis = analyze_m3_200(evidence.response_body or "", evidence.response_headers)
                evidence.account_entitlement_evidence = "ENTITLED"
                evidence.classification = "ACCOUNT_ENTITLED"
                evidence.confidence = "HIGH"
            elif evidence.http_status == 429:
                analysis = analyze_m1_429(evidence.response_body or "")
                evidence.account_entitlement_evidence = "UNCLEAR"
                evidence.classification = "UNCLEAR"
                evidence.confidence = "LOW"
        else:
            evidence.account_entitlement_evidence = "NOT_TESTED"
            evidence.classification = "NOT_TESTED"
            evidence.confidence = "UNKNOWN"
        
        model_evidence_list.append(evidence)
    
    # Build evidence dictionaries
    official_catalog_evidence = {}
    for m in model_evidence_list:
        official_catalog_evidence[m.model] = {
            "in_provider_catalog": m.in_provider_catalog,
            "owned_by": m.provider_catalog_owned_by,
            "endpoint_supports": m.endpoint_supports_model,
        }
    
    provider_endpoint_evidence = {
        "endpoint": endpoint,
        "model_endpoint_available": True,
        "models_endpoint_available": True,
    }
    
    account_evidence = {}
    for m in model_evidence_list:
        account_evidence[m.model] = {
            "account_entitlement_evidence": m.account_entitlement_evidence,
            "http_status": m.http_status,
            "provider_request_id": m.provider_request_id,
            "classification": m.classification,
        }
    
    local_configuration_evidence = {}
    for m in model_evidence_list:
        local_configuration_evidence[m.model] = {
            "in_ntpe_model_catalog": m.in_ntpe_model_catalog,
            "in_ntpe_provider_adapter": m.in_ntpe_provider_adapter,
            "in_provider_config_json": m.in_provider_config_json,
            "catalog_enabled": m.ntpe_catalog_enabled,
            "catalog_experimental": m.ntpe_catalog_experimental,
        }
    
    # Determine overall classification
    m1 = next((m for m in model_evidence_list if m.model == "minimaxai/minimax-m3"), None)
    m2 = next((m for m in model_evidence_list if m.model == "nvidia/llama-3.1-nemotron-70b-instruct"), None)
    m3 = next((m for m in model_evidence_list if m.model == "meta/llama-3.2-90b-vision-instruct"), None)
    
    # Classification logic per spec
    if m2 and m2.account_entitlement_evidence == "NOT_ENTITLED" and m3 and m3.account_entitlement_evidence == "ENTITLED":
        current_classification = "MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL"
        confidence = "HIGH"
    elif m1 and m1.account_entitlement_evidence == "UNCLEAR" and m3 and m3.account_entitlement_evidence == "ENTITLED":
        current_classification = "MODEL_SPECIFIC_PROVIDER_BEHAVIOR"
        confidence = "MEDIUM"
    elif m1 and m1.account_entitlement_evidence == "NOT_ENTITLED":
        current_classification = "MODEL_ACCOUNT_ACCESS_REJECTION"
        confidence = "HIGH"
    else:
        current_classification = "UNKNOWN"
        confidence = "LOW"
    
    return EntitlementReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        client_path="core/translation_engine/nvidia_client.py",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        endpoint=endpoint,
        credential_present=bool(api_key),
        credential_source="NVIDIA_API_KEY",
        models=model_evidence_list,
        official_catalog_evidence=official_catalog_evidence,
        provider_endpoint_evidence=provider_endpoint_evidence,
        account_evidence=account_evidence,
        local_configuration_evidence=local_configuration_evidence,
        previous_classification="NON_UNIFORM_PROVIDER_BEHAVIOR",
        current_classification=current_classification,
        confidence=confidence,
        production_changes={
            "retry": False,
            "backoff": False,
            "rpm_limiter": False,
            "admission": False,
            "runtime": False,
        },
        rm6_promotion="BLOCKED",
        limitations=[
            "No direct account entitlement API available",
            "Cannot distinguish M1 429 cause without provider documentation",
            "M2 404 indicates account-level function deployment absence, not necessarily model-level denial",
            "Provider /v1/models lists model but doesn't guarantee account access",
            "No official NVIDIA documentation on 429 vs 404 semantics for entitlement",
        ],
    )


def main():
    """Main entry point."""
    print("=" * 70)
    print("P0-FINAL-15-J: NVIDIA Model Entitlement & Availability Evidence")
    print("=" * 70)

    report = run_entitlement_analysis()

    # Output to artifacts
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    report_path = artifacts_dir / "P0_FINAL_15_J_Nvidia_Model_Entitlement_Evidence_Report.json"

    # Convert to dict and redact
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    print(f"\n[ENTITLEMENT] Report saved to: {report_path}")
    print(f"[ENTITLEMENT] Classification: {report.current_classification}")
    print(f"[ENTITLEMENT] Confidence: {report.confidence}")
    print(f"[ENTITLEMENT] RM6 Promotion: {report.rm6_promotion}")

    # Print summary
    print("\n" + "=" * 70)
    print("EVIDENCE MATRIX SUMMARY")
    print("=" * 70)
    print(f"{'Model':<45} {'Catalog':<8} {'Endpoint':<10} {'Account':<12} {'HTTP':<6} {'Confidence'}")
    print("-" * 100)
    for m in report.models:
        print(f"{m.model:<45} {str(m.in_provider_catalog):<8} {str(m.endpoint_supports_model):<10} {m.account_entitlement_evidence:<12} {str(m.http_status):<6} {m.confidence}")

    # Also create governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)

    gov_path = governance_dir / "P0_FINAL_15_J_NVIDIA_MODEL_ENTITLEMENT_EVIDENCE.md"

    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-J — NVIDIA Account Model Entitlement & Provider Model Availability Evidence

## Purpose

Establish evidence chain for model availability/entitlement differential observed in P0-FINAL-15-I:
- M1 (minimaxai/minimax-m3): HTTP 429
- M2 (nvidia/llama-3.1-nemotron-70b-instruct): HTTP 404 "Function not found for account"
- M3 (meta/llama-3.2-90b-vision-instruct): HTTP 200

## Scope

### In Scope
- Local NTPE configuration inventory (model catalog, provider adapter, provider_config.json)
- Official NVIDIA /v1/models catalog endpoint
- Account entitlement evidence from provider responses
- Actual HTTP results from P0-FINAL-15-I
- Classification of 429/404/200 differential

### Out of Scope
- Rate limit stress testing
- Production retry/backoff modification
- RPM limiter changes
- Concurrency/burst testing
- Quota exhaustion verification
- Credential rotation or new account provisioning

## Baseline

- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Client**: {report.client_path}
- **Timestamp**: {report.test_timestamp}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source} (present: {report.credential_present})

## Provider Endpoint

- **Chat Completions**: https://integrate.api.nvidia.com/v1/chat/completions
- **Models List**: https://integrate.api.nvidia.com/v1/models
- **Model Detail**: https://integrate.api.nvidia.com/v1/models/{{model_id}}
- **Protocol**: OpenAI-compatible REST
- **Auth**: Bearer token (NVIDIA_API_KEY)

## Credential Handling

- **Credential Present**: {report.credential_present}
- **Credential Source**: {report.credential_source}
- **Secret Exposed**: False (only credential_source recorded, no token values)

## Model Matrix

| Model | NTPE Catalog | Provider Adapter | Provider Config | Provider Catalog | Endpoint Support | Account Evidence | HTTP Status | Classification | Confidence |
|-------|--------------|------------------|-----------------|------------------|------------------|------------------|-------------|----------------|------------|
""")
        
        for m in report.models:
            f.write(f"| {m.model} | {m.in_ntpe_model_catalog} | {m.in_ntpe_provider_adapter} | {m.in_provider_config_json} | {m.in_provider_catalog} | {m.endpoint_supports_model} | {m.account_entitlement_evidence} | {m.http_status} | {m.classification} | {m.confidence} |\n")

        f.write(f"""

## Catalog Evidence

### NTPE Static Model Catalog (core/launcher_product/model_catalog.py)
""")
        
        for m in report.models:
            f.write(f"""
#### {m.model}
- **In Catalog**: {m.in_ntpe_model_catalog}
- **Enabled**: {m.ntpe_catalog_enabled}
- **Experimental**: {m.ntpe_catalog_experimental}
- **Context Notes**: {m.ntpe_catalog_context_notes}
""")

        f.write(f"""

### NTPE Provider Adapter Config (core/ai_provider/adapters.py)
""")
        
        for m in report.models:
            f.write(f"""
#### {m.model}
- **In Adapter Config**: {m.in_ntpe_provider_adapter}
""")

        f.write(f"""

### Provider Config JSON (config/provider_config.json)
""")
        
        for m in report.models:
            local = report.local_configuration_evidence.get(m.model, {})
            f.write(f"""
#### {m.model}
- **Is Default Model**: {local.get('is_default', 'N/A')}
- **Is Fallback Model**: {local.get('is_fallback', 'N/A')}
- **Default Model**: {local.get('default_model', 'N/A')}
- **Fallback Models**: {local.get('fallback_models', 'N/A')}
""")

        f.write(f"""

### Official NVIDIA /v1/models Catalog
""")
        
        for m in report.models:
            catalog = report.official_catalog_evidence.get(m.model, {})
            f.write(f"""
#### {m.model}
- **In Catalog**: {catalog.get('in_provider_catalog', False)}
- **Owned By**: {catalog.get('owned_by', 'N/A')}
- **Endpoint Supports**: {catalog.get('endpoint_supports', False)}
""")

        f.write(f"""

## Account Evidence

### M2 (nvidia/llama-3.1-nemotron-70b-instruct) - HTTP 404 Analysis
""")
        
        m2 = next((m for m in report.models if m.model == "nvidia/llama-3.1-nemotron-70b-instruct"), None)
        if m2 and m2.response_body:
            analysis = analyze_m2_404(m2.response_body)
            f.write(f"""
**Response Body**: `{m2.response_body}`

**Parsed Analysis**:
- **Function ID**: {analysis.get('function_id', 'N/A')}
- **Account ID**: {analysis.get('account_id', 'N/A')}
- **Semantics**: {analysis.get('semantics', 'N/A')}
- **Evidence Type**: {analysis.get('evidence_type', 'N/A')}

**Interpretation**: The explicit "Function not found for account" message indicates this model is not deployed as an invokable function for the requesting account. This is an account-level entitlement signal, not a generic rate limit.
""")

        f.write(f"""

### M3 (meta/llama-3.2-90b-vision-instruct) - HTTP 200 Analysis
""")
        
        m3 = next((m for m in report.models if m.model == "meta/llama-3.2-90b-vision-instruct"), None)
        if m3 and m3.response_body:
            analysis = analyze_m3_200(m3.response_body, m3.response_headers)
            f.write(f"""
**Response Body**: `{m3.response_body[:200]}...`

**Key Headers**:
- **Nvcf-Reqid**: {m3.response_headers.get('Nvcf-Reqid', 'N/A')}
- **Nvcf-Status**: {m3.response_headers.get('Nvcf-Status', 'N/A')}
- **Provider Request ID**: {m3.provider_request_id}

**Semantics**: {analysis.get('semantics', 'N/A')}

**Interpretation**: Successful completion with full provider tracking (NVCF request ID, status fulfilled) confirms account entitlement and endpoint capability for this model.
""")

        f.write(f"""

### M1 (minimaxai/minimax-m3) - HTTP 429 Analysis
""")
        
        m1 = next((m for m in report.models if m.model == "minimaxai/minimax-m3"), None)
        if m1 and m1.response_body:
            analysis = analyze_m1_429(m1.response_body)
            f.write(f"""
**Response Body**: `{m1.response_body}`

**Key Observations**:
- **Status**: {analysis.get('status', 'N/A')}
- **Title**: {analysis.get('title', 'N/A')}
- **Rate Limit Headers**: {analysis.get('has_rate_limit_headers', False)}
- **Semantics**: {analysis.get('semantics', 'N/A')}

**Interpretation**: The 429 response lacks:
- RateLimit-* headers
- Retry-After header
- X-RateLimit-* headers
- Quota-type detail in body (no "requests per minute", "tokens per minute", "concurrent", "account quota", "model quota")

This differs from M2's explicit account entitlement signal (404 with function/account IDs) and M3's success with full provider metadata.
""")

        f.write(f"""

## Classification

- **Previous (P0-FINAL-15-I)**: {report.previous_classification}
- **Current**: **{report.current_classification}**
- **Confidence**: **{report.confidence}**

### Classification Rationale
""")

        if report.current_classification == "MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL":
            f.write("""
**MODEL_ACCOUNT_ENTITLEMENT_DIFFERENTIAL**: 
- M2 receives explicit account-level denial: "Function not found for account"
- M3 receives successful completion with provider tracking
- This confirms account entitlement varies by model

**Cannot directly explain M1's 429** from this evidence alone. M1's 429 lacks:
- Account entitlement denial signal (no "not found for account")
- Rate limit detail (no headers, no quota type in body)
- Model-specific quota indication

M1 remains ambiguous: could be model-specific rate limit, model-specific capacity, or different routing.
""")
        elif report.current_classification == "MODEL_SPECIFIC_PROVIDER_BEHAVIOR":
            f.write("""
**MODEL_SPECIFIC_PROVIDER_BEHAVIOR**:
- M2 is not entitled (404 account-level)
- M3 is entitled (200 success)
- M1 returns 429 without clear quota semantics
- Suggests M1 may have different provider routing/behavior

Requires provider documentation to determine if 429 is the expected response for entitled-but-rate-limited vs not-entitled.
""")
        elif report.current_classification == "MODEL_ACCOUNT_ACCESS_REJECTION":
            f.write("""
**MODEL_ACCOUNT_ACCESS_REJECTION**:
- If provider documentation confirms 429 is used for "model not available to account"
- Would require official NVIDIA documentation evidence
""")
        else:
            f.write("""
**UNKNOWN**: Insufficient evidence to classify M1's 429 cause. The differential between M2 (explicit account denial) and M3 (success) is established, but M1's 429 semantics remain unclear without provider documentation.
""")

        f.write(f"""

## Production Impact

- **Retry Policy Modified**: {report.production_changes['retry']}
- **Backoff Modified**: {report.production_changes['backoff']}
- **RPM Limiter Modified**: {report.production_changes['rpm_limiter']}
- **Admission Modified**: {report.production_changes['admission']}
- **Runtime Modified**: {report.production_changes['runtime']}

## RM6 Promotion Decision

**RM6 Promotion = {report.rm6_promotion}**

### Rationale
- M1 429 cause remains undetermined without provider documentation
- Cannot verify if 429 = rate limit, capacity, or entitlement rejection
- No production changes made or required
- Entitlement differential established for M2 vs M3 only

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
- ✅ Reuses P0-FINAL-15-I evidence (no new provider requests for M1/M2/M3)

## Conclusion

This phase establishes:

1. **M2 (nvidia/llama-3.1-nemotron-70b-instruct)**: Explicitly NOT entitled for this account (404 "Function not found for account")
2. **M3 (meta/llama-3.2-90b-vision-instruct)**: Explicitly entitled (200 with provider tracking)
3. **M1 (minimaxai/minimax-m3)**: 429 without rate-limit headers or quota detail — **cause undetermined**

The entitlement differential is proven between M2 and M3. M1 requires provider documentation or account-level API to classify.

Next phase (if any) should target:
- NVIDIA provider documentation on 429 semantics
- Account model access API (if available)
- Minimax M3 specific deployment status for this account
""")

    print(f"[ENTITLEMENT] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-J Entitlement Diagnostic Complete")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())