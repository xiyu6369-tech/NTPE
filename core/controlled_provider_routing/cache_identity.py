from __future__ import annotations

import hashlib,json
from .models import ProviderProfile,ProviderRoutingInput,ProviderRoutingPolicy


def _hash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def build_provider_route_identity(item:ProviderRoutingInput,profile:ProviderProfile,policy:ProviderRoutingPolicy)->dict:
    translation={"provider_id":profile.provider_id,"model_id":profile.model_id,"provider_profile_version":profile.profile_version,"provider_profile_fingerprint":profile.fingerprint,"prompt_contract_id":profile.prompt_contract_id,"prompt_contract_version":profile.prompt_contract_version,"quality_contract_id":profile.quality_contract_id,"quality_contract_version":profile.quality_contract_version,"language_profile_fingerprint":item.language_profile_fingerprint}
    routing={**translation,"routing_policy_version":policy.version}
    return {"translation_cache_identity":_hash(translation),"routing_evidence_identity":_hash(routing),"fields":routing}
