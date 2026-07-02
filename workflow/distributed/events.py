"""Distributed execution event constants."""
DISTRIBUTED_EVENTS = {
    "coordinator_started": "distributed.coordinator.started",
    "coordinator_stopped": "distributed.coordinator.stopped",
    "node_registered": "distributed.node.registered",
    "node_heartbeat": "distributed.node.heartbeat",
    "task_distributed": "distributed.task.distributed",
    "task_completed": "distributed.task.completed",
    "task_failed": "distributed.task.failed",
    "failover": "distributed.failover",
}
