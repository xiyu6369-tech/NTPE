"""Framework-neutral Web UI job page for NTPE Stage-13.4."""
from __future__ import annotations

from typing import Any, Dict, List

from .job_models import JobAction, JobPageView, WEB_UI_JOB_STAGE
from .rest_client import WebUiRestClient
from .ui_models import WebUiState


class WebUiJobPage:
    """Builds the job page using only REST Job API responses."""

    stage = WEB_UI_JOB_STAGE

    def __init__(self, client: WebUiRestClient | None = None) -> None:
        self.client = client

    def _client(self, client: WebUiRestClient | None = None) -> WebUiRestClient:
        active = client or self.client
        if active is None:
            raise ValueError("WebUiJobPage requires a WebUiRestClient")
        return active

    def actions(self) -> List[JobAction]:
        return [
            JobAction("create", "Create Job", "POST", "/v1/jobs"),
            JobAction("refresh", "Refresh Jobs", "GET", "/v1/jobs"),
            JobAction("start", "Start", "POST", "/v1/jobs/{job_id}/start"),
            JobAction("pause", "Pause", "POST", "/v1/jobs/{job_id}/pause"),
            JobAction("resume", "Resume", "POST", "/v1/jobs/{job_id}/resume"),
            JobAction("stop", "Stop", "POST", "/v1/jobs/{job_id}/stop"),
            JobAction("cancel", "Cancel", "POST", "/v1/jobs/{job_id}/cancel"),
            JobAction("status", "Status", "GET", "/v1/jobs/{job_id}/status"),
            JobAction("result", "Result", "GET", "/v1/jobs/{job_id}/result"),
        ]

    def build(self, state: WebUiState, client: WebUiRestClient | None = None) -> JobPageView:
        active_client = self._client(client)
        job_response = active_client.list_jobs()
        body: Dict[str, Any] = dict(job_response.get("body") or {})
        data: Dict[str, Any] = dict(body.get("data") or {})
        jobs = data.get("jobs") or data.get("items") or []
        if not isinstance(jobs, list):
            jobs = []

        return JobPageView(
            jobs=[dict(job) for job in jobs if isinstance(job, dict)],
            actions=self.actions(),
            metadata={
                "rest_status_code": job_response.get("status_code"),
                "uses_rest_job_api_only": True,
                "uses_frozen_runtime_api_only": state.metadata.get("uses_frozen_runtime_api_only"),
                "rest_api_available": state.rest_api_available,
                "additive_only": True,
            },
        )

    def summary(self, state: WebUiState, client: WebUiRestClient | None = None) -> Dict[str, Any]:
        view = self.build(state, client).to_dict()
        return {
            "stage": self.stage,
            "job_count": len(view["jobs"]),
            "action_count": len(view["actions"]),
            "rest_api_available": state.rest_api_available,
            "uses_rest_job_api_only": view["metadata"].get("uses_rest_job_api_only"),
        }
