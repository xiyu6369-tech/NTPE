"""Framework-neutral Web UI pipeline page for NTPE Stage-13.5."""
from __future__ import annotations

from typing import Any, Dict, List

from .pipeline_models import PipelineAction, PipelinePageView, WEB_UI_PIPELINE_STAGE
from .rest_client import WebUiRestClient
from .ui_models import WebUiState


class WebUiPipelinePage:
    """Builds the pipeline page using only REST Pipeline API responses."""

    stage = WEB_UI_PIPELINE_STAGE

    def __init__(self, client: WebUiRestClient | None = None) -> None:
        self.client = client

    def _client(self, client: WebUiRestClient | None = None) -> WebUiRestClient:
        active = client or self.client
        if active is None:
            raise ValueError("WebUiPipelinePage requires a WebUiRestClient")
        return active

    def actions(self) -> List[PipelineAction]:
        return [
            PipelineAction("create", "Create Pipeline", "POST", "/v1/pipelines"),
            PipelineAction("refresh", "Refresh Pipelines", "GET", "/v1/pipelines"),
            PipelineAction("detail", "Open Detail", "GET", "/v1/pipelines/{pipeline_id}"),
            PipelineAction("add_stage", "Add Stage", "POST", "/v1/pipelines/{pipeline_id}/stages"),
            PipelineAction("validate", "Validate", "POST", "/v1/pipelines/{pipeline_id}/validate"),
            PipelineAction("start", "Start", "POST", "/v1/pipelines/{pipeline_id}/start"),
            PipelineAction("pause", "Pause", "POST", "/v1/pipelines/{pipeline_id}/pause"),
            PipelineAction("resume", "Resume", "POST", "/v1/pipelines/{pipeline_id}/resume"),
            PipelineAction("complete", "Complete", "POST", "/v1/pipelines/{pipeline_id}/complete"),
            PipelineAction("fail", "Fail", "POST", "/v1/pipelines/{pipeline_id}/fail"),
            PipelineAction("cancel", "Cancel", "POST", "/v1/pipelines/{pipeline_id}/cancel"),
            PipelineAction("status", "Status", "GET", "/v1/pipelines/{pipeline_id}/status"),
            PipelineAction("summary", "Summary", "GET", "/v1/pipelines/{pipeline_id}/summary"),
        ]

    def build(self, state: WebUiState, client: WebUiRestClient | None = None) -> PipelinePageView:
        active_client = self._client(client)
        pipeline_response = active_client.list_pipelines()
        body: Dict[str, Any] = dict(pipeline_response.get("body") or {})
        data: Dict[str, Any] = dict(body.get("data") or {})
        pipelines = data.get("pipelines") or data.get("items") or []
        if not isinstance(pipelines, list):
            pipelines = []

        return PipelinePageView(
            pipelines=[dict(pipeline) for pipeline in pipelines if isinstance(pipeline, dict)],
            actions=self.actions(),
            metadata={
                "rest_status_code": pipeline_response.get("status_code"),
                "uses_rest_pipeline_api_only": True,
                "uses_frozen_runtime_api_only": state.metadata.get("uses_frozen_runtime_api_only"),
                "rest_api_available": state.rest_api_available,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState, client: WebUiRestClient | None = None) -> Dict[str, Any]:
        view = self.build(state, client).to_dict()
        return {
            "stage": self.stage,
            "pipeline_count": len(view["pipelines"]),
            "action_count": len(view["actions"]),
            "rest_api_available": state.rest_api_available,
            "uses_rest_pipeline_api_only": view["metadata"].get("uses_rest_pipeline_api_only"),
        }
