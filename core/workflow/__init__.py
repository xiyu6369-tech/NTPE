# =====================================================
# NTPE 1.2 Professional
# Stage-17.1 Translation Workflow Engine
# =====================================================

try:
    from .workflow_context import WorkflowContext
    from .workflow_engine import TranslationWorkflowEngine
    from .workflow_events import (
        WORKFLOW_COMPLETED,
        WORKFLOW_FAILED,
        WORKFLOW_STARTED,
        WORKFLOW_STEP_COMPLETED,
        WORKFLOW_STEP_STARTED,
        WorkflowEvent,
        WorkflowEventBus,
    )
    from .workflow_exceptions import WorkflowError, WorkflowInputError, WorkflowStepError
    from .workflow_metrics import build_workflow_metrics
    from .workflow_pipeline import WorkflowPipeline
    from .workflow_registry import WorkflowRegistry
    from .workflow_result import WorkflowResult, WorkflowStepResult
    from .workflow_state import WorkflowState
    from .workflow_step import WorkflowStep

    from .resource_bridge import optimize_workflow_resources
    from .resource_context import ResourceContext
    from .resource_events import (
        RESOURCE_BUDGET_WARNING,
        RESOURCE_OPTIMIZATION_COMPLETED,
        RESOURCE_OPTIMIZATION_STARTED,
        ResourceEvent,
        ResourceEventBus,
    )
    from .resource_exceptions import ResourceBudgetError, ResourceOptimizerError
    from .resource_optimizer import ResourceOptimizer
    from .resource_policy import ResourceOptimizationPolicy
    from .resource_profile import ResourceProfile
    from .resource_registry import ResourceProfileRegistry
    from .resource_result import ResourceOptimizationResult, ResourcePlan
except Exception:
    WorkflowContext = None
    TranslationWorkflowEngine = None
    WorkflowEvent = None
    WorkflowEventBus = None
    WorkflowError = None
    WorkflowInputError = None
    WorkflowStepError = None
    WorkflowPipeline = None
    WorkflowRegistry = None
    WorkflowResult = None
    WorkflowStepResult = None
    WorkflowState = None
    WorkflowStep = None
    build_workflow_metrics = None

    ResourceContext = None
    ResourceEvent = None
    ResourceEventBus = None
    ResourceOptimizer = None
    ResourceOptimizerError = None
    ResourceBudgetError = None
    ResourceOptimizationPolicy = None
    ResourceOptimizationResult = None
    ResourcePlan = None
    ResourceProfile = None
    ResourceProfileRegistry = None
    optimize_workflow_resources = None
    RESOURCE_BUDGET_WARNING = "ResourceBudgetWarning"
    RESOURCE_OPTIMIZATION_COMPLETED = "ResourceOptimizationCompleted"
    RESOURCE_OPTIMIZATION_STARTED = "ResourceOptimizationStarted"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    WORKFLOW_FAILED = "WorkflowFailed"
    WORKFLOW_STARTED = "WorkflowStarted"
    WORKFLOW_STEP_COMPLETED = "WorkflowStepCompleted"
    WORKFLOW_STEP_STARTED = "WorkflowStepStarted"

__all__ = [

    "RESOURCE_BUDGET_WARNING",
    "RESOURCE_OPTIMIZATION_COMPLETED",
    "RESOURCE_OPTIMIZATION_STARTED",
    "ResourceBudgetError",
    "ResourceContext",
    "ResourceEvent",
    "ResourceEventBus",
    "ResourceOptimizationPolicy",
    "ResourceOptimizationResult",
    "ResourceOptimizer",
    "ResourceOptimizerError",
    "ResourcePlan",
    "ResourceProfile",
    "ResourceProfileRegistry",
    "optimize_workflow_resources",
    "WORKFLOW_COMPLETED",
    "WORKFLOW_FAILED",
    "WORKFLOW_STARTED",
    "WORKFLOW_STEP_COMPLETED",
    "WORKFLOW_STEP_STARTED",
    "TranslationWorkflowEngine",
    "WorkflowContext",
    "WorkflowError",
    "WorkflowEvent",
    "WorkflowEventBus",
    "WorkflowInputError",
    "WorkflowPipeline",
    "WorkflowRegistry",
    "WorkflowResult",
    "WorkflowState",
    "WorkflowStep",
    "WorkflowStepError",
    "WorkflowStepResult",
    "build_workflow_metrics",
]
