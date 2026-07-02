"""Web UI model primitives for NTPE 1.0 Beta Stage-13.1.

The Web UI layer is intentionally framework-neutral. It exposes a deterministic
UI shell and render model that can later be connected to FastAPI, Flask,
desktop webviews, or a bundled frontend without coupling to runtime internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

WEB_UI_VERSION = "1.0.0-beta.13.1"
WEB_UI_STAGE = "13.1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class WebUiRoute:
    """A framework-neutral UI route descriptor."""

    path: str
    title: str
    page_id: str
    navigation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        path = str(self.path or "/")
        if not path.startswith("/"):
            path = "/" + path
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "title", str(self.title or self.page_id))
        object.__setattr__(self, "page_id", str(self.page_id or path.strip("/") or "home"))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "page_id": self.page_id,
            "navigation": self.navigation,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class WebUiState:
    """Serializable state passed from REST/Runtime API to the UI shell."""

    rest_api_available: bool
    runtime_api_stage: Optional[str] = None
    external_api_stage: Optional[str] = None
    health: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rest_api_available": self.rest_api_available,
            "runtime_api_stage": self.runtime_api_stage,
            "external_api_stage": self.external_api_stage,
            "health": dict(self.health),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class WebUiPage:
    """A renderable UI page model."""

    route: WebUiRoute
    state: WebUiState
    components: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": WEB_UI_VERSION,
            "stage": WEB_UI_STAGE,
            "route": self.route.to_dict(),
            "state": self.state.to_dict(),
            "components": [dict(component) for component in self.components],
            "created_at": self.created_at,
        }
