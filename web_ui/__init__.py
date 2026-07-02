"""NTPE Web UI Layer public surface for Stage-13.1."""
from .dashboard import WebUiDashboard
from .session_models import WEB_UI_SESSION_STAGE, SessionAction, SessionPageView
from .session_page import WebUiSessionPage
from .job_models import WEB_UI_JOB_STAGE, JobAction, JobPageView
from .job_page import WebUiJobPage
from .pipeline_models import WEB_UI_PIPELINE_STAGE, PipelineAction, PipelinePageView
from .event_models import WEB_UI_EVENT_STAGE, EventAction, EventPageView
from .resource_models import WEB_UI_RESOURCE_STAGE, ResourceAction, ResourcePageView
from .pipeline_page import WebUiPipelinePage
from .event_page import WebUiEventPage
from .resource_page import WebUiResourcePage
from .dashboard_models import DashboardMetric, DashboardSection, DashboardView, WEB_UI_DASHBOARD_STAGE
from .ui_models import WEB_UI_STAGE, WEB_UI_VERSION, WebUiPage, WebUiRoute, WebUiState
from .ui_shell import WebUiShell
from .rest_client import WebUiRestClient
from .web_app import WebUiApp, create_web_ui_app

from .web_ui_freeze import (
    WEB_UI_FREEZE_STAGE,
    WEB_UI_FROZEN_PAGES,
    WEB_UI_REQUIRED_ROUTES,
    WebUiFreezeReport,
    create_web_ui_freeze_report,
    validate_web_ui_freeze,
)
__all__ = [
    "WEB_UI_STAGE",
    "WEB_UI_VERSION",
    "WEB_UI_DASHBOARD_STAGE",
    "WEB_UI_SESSION_STAGE",
    "WEB_UI_JOB_STAGE",
    "WEB_UI_PIPELINE_STAGE",
    "WEB_UI_EVENT_STAGE",
    "WEB_UI_RESOURCE_STAGE",
    "DashboardMetric",
    "DashboardSection",
    "DashboardView",
    "WebUiDashboard",
    "SessionAction",
    "SessionPageView",
    "WebUiSessionPage",
    "JobAction",
    "JobPageView",
    "WebUiJobPage",
    "PipelineAction",
    "PipelinePageView",
    "WebUiPipelinePage",
    "EventAction",
    "EventPageView",
    "WebUiEventPage",
    "ResourceAction",
    "ResourcePageView",
    "WebUiResourcePage",
    "WebUiPage",
    "WebUiRoute",
    "WebUiState",
    "WebUiShell",
    "WebUiRestClient",
    "WebUiApp",
    "WEB_UI_FREEZE_STAGE",
    "WEB_UI_FROZEN_PAGES",
    "WEB_UI_REQUIRED_ROUTES",
    "WebUiFreezeReport",
    "create_web_ui_freeze_report",
    "validate_web_ui_freeze",
    "create_web_ui_app",
]
