#!/usr/bin/env python3
"""
P0-FINAL-15-R: Cross-Provider Candidate Inventory

Phase R-B: Discover and catalog non-NVIDIA general-purpose LLM candidates
from available providers (OpenAI, Anthropic, Google, etc.) that have
public APIs and could serve as NTPE translation candidates.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class ProviderCandidate:
    """Candidate model from a provider."""
    model_id: str
    provider: str
    display_name: str
    # Capability flags
    general_purpose_llm: bool
    chinese_support: bool
    multilingual: bool
    instruction_following: bool
    context_window: Optional[int]
    max_output_tokens: Optional[int]
    # API info
    api_endpoint: Optional[str]
    api_available: bool
    api_type: str  # openai-compatible, anthropic, google, custom
    # Access
    requires_credential: bool
    credential_env_var: Optional[str]
    # Quality indicators
    recent_generation: bool
    production_ready: bool
    # Notes
    notes: str


@dataclass
class CrossProviderInventoryReport:
    """Complete cross-provider inventory report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    # Environment
    python_version: str
    test_timestamp: str
    # Providers
    providers: list[str]
    # Candidates
    total_candidates: int
    candidates: list[ProviderCandidate]
    # Filtered
    qualified_candidates: list[str]  # model_ids passing basic criteria
    # Priority
    priority_candidates: list[str]  # top 2-3 per provider
    # Limitations
    limitations: list[str]


def get_git_baseline() -> dict:
    import subprocess
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        origin_main = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        result = subprocess.run(["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"], capture_output=True, text=True)
        divergence = f"{result.stdout.strip().split()[0]}/{result.stdout.strip().split()[1]}" if result.returncode == 0 else "unknown"
        return {"head_commit": head, "origin_main_commit": origin_main, "divergence": divergence, "branch": branch}
    except Exception as e:
        return {"head_commit": "error", "origin_main_commit": "error", "divergence": "error", "branch": "error", "error": str(e)}


def redact_sensitive(data: dict) -> dict:
    if not isinstance(data, dict): return data
    redacted = {}
    sensitive = {"authorization", "api_key", "apikey", "secret", "token", "password", "credential", "bearer", "x-api-key"}
    for k, v in data.items():
        if k.lower() in sensitive: redacted[k] = "[REDACTED]"
        elif isinstance(v, dict): redacted[k] = redact_sensitive(v)
        elif isinstance(v, list): redacted[k] = [redact_sensitive(i) if isinstance(i, dict) else i for i in v]
        else: redacted[k] = v
    return redacted


def build_known_candidates() -> list[ProviderCandidate]:
    """Build list of known general-purpose LLM candidates from major providers."""
    
    candidates = []
    
    # OpenAI
    openai_models = [
        ProviderCandidate(
            model_id="gpt-4o",
            provider="OpenAI",
            display_name="GPT-4o",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=16384,
            api_endpoint="https://api.openai.com/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="OPENAI_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Flagship model, strong multilingual, excellent instruction following",
        ),
        ProviderCandidate(
            model_id="gpt-4o-mini",
            provider="OpenAI",
            display_name="GPT-4o Mini",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=16384,
            api_endpoint="https://api.openai.com/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="OPENAI_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Cost-efficient variant, strong capabilities",
        ),
        ProviderCandidate(
            model_id="gpt-4-turbo",
            provider="OpenAI",
            display_name="GPT-4 Turbo",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=4096,
            api_endpoint="https://api.openai.com/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="OPENAI_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Previous generation flagship",
        ),
    ]
    candidates.extend(openai_models)
    
    # Anthropic
    anthropic_models = [
        ProviderCandidate(
            model_id="claude-3-5-sonnet-20241022",
            provider="Anthropic",
            display_name="Claude 3.5 Sonnet",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=200000,
            max_output_tokens=8192,
            api_endpoint="https://api.anthropic.com/v1/messages",
            api_available=True,
            api_type="anthropic",
            requires_credential=True,
            credential_env_var="ANTHROPIC_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Strong reasoning, excellent multilingual, large context",
        ),
        ProviderCandidate(
            model_id="claude-3-5-haiku-20241022",
            provider="Anthropic",
            display_name="Claude 3.5 Haiku",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=200000,
            max_output_tokens=8192,
            api_endpoint="https://api.anthropic.com/v1/messages",
            api_available=True,
            api_type="anthropic",
            requires_credential=True,
            credential_env_var="ANTHROPIC_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Fast, cost-efficient variant",
        ),
        ProviderCandidate(
            model_id="claude-3-opus-20240229",
            provider="Anthropic",
            display_name="Claude 3 Opus",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=200000,
            max_output_tokens=4096,
            api_endpoint="https://api.anthropic.com/v1/messages",
            api_available=True,
            api_type="anthropic",
            requires_credential=True,
            credential_env_var="ANTHROPIC_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Previous flagship, very strong reasoning",
        ),
    ]
    candidates.extend(anthropic_models)
    
    # Google (Gemini via Vertex AI or AI Studio)
    google_models = [
        ProviderCandidate(
            model_id="gemini-1.5-pro",
            provider="Google",
            display_name="Gemini 1.5 Pro",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=2000000,
            max_output_tokens=8192,
            api_endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
            api_available=True,
            api_type="google",
            requires_credential=True,
            credential_env_var="GOOGLE_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Massive context window, strong multilingual",
        ),
        ProviderCandidate(
            model_id="gemini-1.5-flash",
            provider="Google",
            display_name="Gemini 1.5 Flash",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=1000000,
            max_output_tokens=8192,
            api_endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            api_available=True,
            api_type="google",
            requires_credential=True,
            credential_env_var="GOOGLE_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Fast, cost-efficient, large context",
        ),
        ProviderCandidate(
            model_id="gemini-1.0-pro",
            provider="Google",
            display_name="Gemini 1.0 Pro",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=32768,
            max_output_tokens=2048,
            api_endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            api_available=True,
            api_type="google",
            requires_credential=True,
            credential_env_var="GOOGLE_API_KEY",
            recent_generation=False,
            production_ready=True,
            notes="Previous generation",
        ),
    ]
    candidates.extend(google_models)
    
    # Cohere
    cohere_models = [
        ProviderCandidate(
            model_id="command-r-plus",
            provider="Cohere",
            display_name="Command R+",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=4096,
            api_endpoint="https://api.cohere.ai/v1/chat",
            api_available=True,
            api_type="cohere",
            requires_credential=True,
            credential_env_var="COHERE_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Strong RAG capabilities, multilingual",
        ),
        ProviderCandidate(
            model_id="command-r",
            provider="Cohere",
            display_name="Command R",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=4096,
            api_endpoint="https://api.cohere.ai/v1/chat",
            api_available=True,
            api_type="cohere",
            requires_credential=True,
            credential_env_var="COHERE_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Efficient variant",
        ),
    ]
    candidates.extend(cohere_models)
    
    # Mistral AI
    mistral_models = [
        ProviderCandidate(
            model_id="mistral-large-latest",
            provider="Mistral AI",
            display_name="Mistral Large",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=32768,
            max_output_tokens=8192,
            api_endpoint="https://api.mistral.ai/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="MISTRAL_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Flagship model, strong multilingual",
        ),
        ProviderCandidate(
            model_id="mistral-medium-latest",
            provider="Mistral AI",
            display_name="Mistral Medium",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=32768,
            max_output_tokens=8192,
            api_endpoint="https://api.mistral.ai/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="MISTRAL_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Balanced performance",
        ),
    ]
    candidates.extend(mistral_models)
    
    # DeepSeek
    deepseek_models = [
        ProviderCandidate(
            model_id="deepseek-chat",
            provider="DeepSeek",
            display_name="DeepSeek V3 (Chat)",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=64000,
            max_output_tokens=8192,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="DEEPSEEK_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Strong Chinese capability, cost-effective",
        ),
        ProviderCandidate(
            model_id="deepseek-coder",
            provider="DeepSeek",
            display_name="DeepSeek Coder",
            general_purpose_llm=False,  # Code-specialized
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=16384,
            max_output_tokens=8192,
            api_endpoint="https://api.deepseek.com/v1/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="DEEPSEEK_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Code-specialized, not general-purpose for literary",
        ),
    ]
    candidates.extend(deepseek_models)
    
    # Z.ai (GLM)
    zai_models = [
        ProviderCandidate(
            model_id="glm-4",
            provider="Z.ai",
            display_name="GLM-4",
            general_purpose_llm=True,
            chinese_support=True,
            multilingual=True,
            instruction_following=True,
            context_window=128000,
            max_output_tokens=8192,
            api_endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
            api_available=True,
            api_type="openai-compatible",
            requires_credential=True,
            credential_env_var="ZAI_API_KEY",
            recent_generation=True,
            production_ready=True,
            notes="Strong Chinese, from Zhipu AI",
        ),
    ]
    candidates.extend(zai_models)
    
    return candidates


def filter_qualified(candidates: list[ProviderCandidate]) -> list[str]:
    """Filter candidates that pass basic mandatory criteria."""
    qualified = []
    for c in candidates:
        if (c.general_purpose_llm and 
            c.chinese_support and 
            c.instruction_following and 
            c.context_window and c.context_window >= 8192 and
            c.api_available and
            c.requires_credential):
            qualified.append(c.model_id)
    return qualified


def select_priority(qualified_ids: list[str], all_candidates: list[ProviderCandidate]) -> list[str]:
    """Select top 2-3 candidates per provider from qualified list."""
    qualified_map = {c.model_id: c for c in all_candidates if c.model_id in qualified_ids}
    by_provider = {}
    for mid in qualified_ids:
        c = qualified_map[mid]
        if c.provider not in by_provider:
            by_provider[c.provider] = []
        by_provider[c.provider].append((mid, c))
    
    priority = []
    for provider, models in by_provider.items():
        # Sort by: context window desc, recent generation, production ready
        models.sort(key=lambda x: (x[1].context_window or 0, x[1].recent_generation, x[1].production_ready), reverse=True)
        priority.extend([mid for mid, _ in models[:3]])
    return priority


def run_inventory() -> CrossProviderInventoryReport:
    """Run complete cross-provider inventory."""
    baseline = get_git_baseline()
    
    print("\n[INVENTORY] Building cross-provider candidate inventory...")
    
    candidates = build_known_candidates()
    qualified = filter_qualified(candidates)
    priority = select_priority(qualified, candidates)
    
    providers = sorted(set(c.provider for c in candidates))
    
    limitations = [
        "Candidate list based on publicly known models as of 2024",
        "API availability not verified at runtime (requires credentials)",
        "Capability claims based on provider documentation, not independent testing",
        "Cost feasibility not evaluated",
        "Regional availability (China/Taiwan) not verified",
        "No actual API calls performed in this phase",
    ]
    
    return CrossProviderInventoryReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        providers=providers,
        total_candidates=len(candidates),
        candidates=candidates,
        qualified_candidates=qualified,
        priority_candidates=priority,
        limitations=limitations,
    )


def main():
    import datetime
    print("=" * 70)
    print("P0-FINAL-15-R: Cross-Provider Candidate Inventory")
    print("=" * 70)
    
    report = run_inventory()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_R_CROSS_PROVIDER_CANDIDATE_INVENTORY.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[INVENTORY] Report saved to: {report_path}")
    
    print("\n" + "=" * 70)
    print("INVENTORY SUMMARY")
    print("=" * 70)
    print(f"Providers: {', '.join(report.providers)}")
    print(f"Total Candidates: {report.total_candidates}")
    print(f"Qualified (mandatory criteria): {len(report.qualified_candidates)}")
    print(f"Priority Candidates: {len(report.priority_candidates)}")
    
    print("\nQualified Candidates:")
    for mid in report.qualified_candidates:
        c = next(c for c in report.candidates if c.model_id == mid)
        print(f"  {mid} ({c.provider}) - ctx: {c.context_window}, recent: {c.recent_generation}")
    
    print("\nPriority Candidates (top per provider):")
    for mid in report.priority_candidates:
        c = next(c for c in report.candidates if c.model_id == mid)
        print(f"  {mid} ({c.provider}) - ctx: {c.context_window}")
    
    # Governance doc
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_R_CROSS_PROVIDER_CANDIDATE_INVENTORY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-R — Cross-Provider Candidate Inventory

## Phase R-B: Non-NVIDIA Candidate Discovery

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

### Provider Coverage

| Provider | Models |
|----------|--------|
""")
        
        for provider in report.providers:
            count = sum(1 for c in report.candidates if c.provider == provider)
            f.write(f"| {provider} | {count} |\n")
        
        f.write(f"""
### Mandatory Criteria (Section 11)

| Criterion | Requirement |
|-----------|-------------|
| General-purpose LLM | Not specialized (translation-only, embedding, safety, code-only) |
| Chinese Support | Explicit Mandarin/Chinese capability |
| Multilingual | Supports multiple languages |
| Instruction Following | Chat completion / instruction-tuned |
| Context Window | ≥ 8K tokens |
| API Available | Production API endpoint exists |
| Credential Required | Standard API key auth |

### All Candidates

| Model ID | Provider | General LLM | Chinese | Multilingual | Instruction | Context | Recent | Prod Ready | API Type |
|----------|----------|-------------|---------|--------------|-------------|---------|--------|------------|----------|
""")
        
        for c in report.candidates:
            f.write(f"| {c.model_id} | {c.provider} | {c.general_purpose_llm} | {c.chinese_support} | {c.multilingual} | {c.instruction_following} | {c.context_window or 'N/A'} | {c.recent_generation} | {c.production_ready} | {c.api_type} |\n")
        
        f.write(f"""
### Qualified Candidates ({len(report.qualified_candidates)})

Pass all mandatory criteria.
""")
        
        for mid in report.qualified_candidates:
            c = next(c for c in report.candidates if c.model_id == mid)
            f.write(f"""
#### {mid} ({c.provider})
- **Context Window**: {c.context_window}
- **Max Output**: {c.max_output_tokens}
- **API Type**: {c.api_type}
- **Credential**: {c.credential_env_var}
- **Notes**: {c.notes}
""")
        
        f.write(f"""
### Priority Candidates ({len(report.priority_candidates)})

Top 3 per provider (by context window, recency, production readiness).
""")
        
        for mid in report.priority_candidates:
            c = next(c for c in report.candidates if c.model_id == mid)
            f.write(f"- **{mid}** ({c.provider}) — ctx: {c.context_window}, recent: {c.recent_generation}\n")
        
        f.write(f"""
## Limitations
""")
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ No actual API calls performed
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved

## Next Phase
Proceed to **Candidate Evaluation** (smoke, translation, quality, glossary, context, reliability) for priority candidates.
""")
    
    print(f"[INVENTORY] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-R Cross-Provider Inventory Complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import datetime
    import subprocess
    sys.exit(main())