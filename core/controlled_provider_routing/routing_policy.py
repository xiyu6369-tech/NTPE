from __future__ import annotations

from .classification import FAILURE_TYPES
from .models import ProviderRoutingPolicy

DEFAULT_ROUTING_POLICY=ProviderRoutingPolicy("controlled-provider-routing","1.0","nvidia-meta-llama-3.3-70b-instruct",("gemini-2.5-flash",),1,2,2,("connect_timeout","read_timeout","provider_timeout","rate_limit","resource_exhausted","http_5xx","empty_response"),("authentication_failure","invalid_request","http_4xx","quality_failure","semantic_failure","policy_failure","cancelled","unknown_failure"),"bounded_exponential_evidence_only","none_by_default",1,True,"forbidden")
