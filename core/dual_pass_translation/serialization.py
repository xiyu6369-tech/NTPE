from __future__ import annotations
import json,re
from pathlib import PurePath
from dataclasses import asdict,is_dataclass
from enum import Enum
from .models import SCHEMA_VERSION,TranslationMode,VerificationStatus
from .validation import DualPassValidationError
def _plain(value):
    if isinstance(value,Enum):return value.value
    if is_dataclass(value):return {k:_plain(v) for k,v in asdict(value).items()}
    if isinstance(value,dict):return {str(k):_plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_plain(x) for x in value]
    return value
def serialize_dual_pass_state(state):
    payload=_plain(state);payload={"schema_version":SCHEMA_VERSION,**payload} if "schema_version" not in payload else payload;validate_dual_pass_state(payload);return json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def deserialize_dual_pass_state(payload):
    try:data=json.loads(payload)
    except (json.JSONDecodeError,UnicodeDecodeError) as exc:raise DualPassValidationError("invalid dual-pass JSON") from exc
    validate_dual_pass_state(data);return data
def validate_dual_pass_state(data):
    if not isinstance(data,dict) or data.get("schema_version")!=SCHEMA_VERSION:raise DualPassValidationError("unknown schema version")
    if "mode" in data:
        try:TranslationMode(data["mode"])
        except ValueError as exc:raise DualPassValidationError("invalid mode") from exc
    if "verification_status" in data:
        try:VerificationStatus(data["verification_status"])
        except ValueError as exc:raise DualPassValidationError("invalid verification status") from exc
    for key in ("request_count","estimated_requests","maximum_requests"):
        if key in data and (not isinstance(data[key],int) or isinstance(data[key],bool) or data[key]<0):raise DualPassValidationError("negative request count")
    for key,value in data.items():
        if "path" in str(key).lower() and isinstance(value,str) and (PurePath(value).is_absolute() or ".." in PurePath(value).parts):raise DualPassValidationError("path traversal rejected")
    text=json.dumps(data,ensure_ascii=False)
    if re.search(r"nvapi-[A-Za-z0-9._-]{16,}|Bearer\s+[A-Za-z0-9._-]{12,}|Authorization\s*:\s*\S+|-----BEGIN .*PRIVATE KEY-----",text,re.I):raise DualPassValidationError("secret-like state")
    return {"valid":True,"schema_version":SCHEMA_VERSION}
