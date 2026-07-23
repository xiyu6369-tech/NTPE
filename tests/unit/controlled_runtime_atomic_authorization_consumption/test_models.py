from dataclasses import FrozenInstanceError, replace

import pytest

from core.controlled_runtime_atomic_authorization_consumption import (
    AtomicAuthorizationConsumptionClaimRequest,
)
from . import build_context


def test_request_is_frozen_and_deterministic(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    with pytest.raises(FrozenInstanceError):
        request.claim_id = "changed"
    assert replace(request).request_fingerprint == request.request_fingerprint


def test_request_rejects_bool_unit_count(tmp_path):
    request = build_context(tmp_path)["request"]
    values = {name: getattr(request, name) for name in request.__dataclass_fields__ if name != "request_fingerprint"}
    values["requested_unit_count"] = True
    with pytest.raises(TypeError):
        AtomicAuthorizationConsumptionClaimRequest(**values)
