from __future__ import annotations
import json
from .classification import FAILURE_TYPES
from .models import SCHEMA_VERSION
from .provider_profiles import PROVIDER_PROFILES
from .validation import reject_unsafe

def validate_provider_routing_state(value:dict)->None:
    if not isinstance(value,dict) or value.get("schema_version")!=SCHEMA_VERSION:raise ValueError("unknown schema")
    if value.get("policy_version")!="1.0":raise ValueError("unknown policy version")
    if "provider_id" in value and value["provider_id"] not in {p.provider_id for p in PROVIDER_PROFILES}:raise ValueError("unknown Provider profile")
    if "failure_type" in value and value["failure_type"] not in FAILURE_TYPES:raise ValueError("unknown failure type")
    if any(isinstance(v,(int,float)) and v<0 for k,v in value.items() if "request" in k or "budget" in k):raise ValueError("negative request count")
    reject_unsafe(value)
def serialize_provider_routing_state(value:dict)->str:
    validate_provider_routing_state(value);return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def deserialize_provider_routing_state(payload:str)->dict:
    try:value=json.loads(payload)
    except (TypeError,json.JSONDecodeError) as exc:raise ValueError("malformed JSON") from exc
    validate_provider_routing_state(value);return value
