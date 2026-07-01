AI_PROVIDER_MANIFEST = {
    "name": "NTPE AI Provider",
    "stage": "NTPE 1.0 Beta Stage-03",
    "version": "1.0-beta-stage-03",
    "features": ["contract", "manager", "registry", "router", "retry", "rate_limit", "fallback", "health", "metrics", "runtime_bridge"],
}

def build_ai_provider_manifest(extra=None):
    data = dict(AI_PROVIDER_MANIFEST)
    if extra:
        data.update(extra)
    return data
