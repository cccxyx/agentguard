from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from backend.models import Incident, ToolRequest


class SnapshotWorkspace(Protocol):
    """Minimal workspace contract required by the recovery subsystem."""

    def snapshot(self) -> Dict[str, Any]: ...

    def restore(self, state: Dict[str, Any]) -> None: ...


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class CircuitState:
    failures: int = 0
    is_open: bool = False


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be positive")
        self.failure_threshold = failure_threshold
        self._states: Dict[str, CircuitState] = {}

    def before_call(self, key: str) -> None:
        state = self._states.get(key)
        if state and state.is_open:
            raise CircuitOpenError("circuit is open for tool: {}".format(key))

    def record_success(self, key: str) -> None:
        self._states[key] = CircuitState()

    def record_failure(self, key: str) -> bool:
        state = self._states.setdefault(key, CircuitState())
        state.failures += 1
        if state.failures >= self.failure_threshold:
            state.is_open = True
        return state.is_open

    def reset(self, key: str) -> None:
        self._states[key] = CircuitState()

    def states(self) -> Dict[str, Dict[str, Any]]:
        return {
            key: {"failures": value.failures, "is_open": value.is_open}
            for key, value in self._states.items()
        }


class SnapshotManager:
    def __init__(self, workspace: SnapshotWorkspace) -> None:
        self.workspace = workspace
        self.snapshots: Dict[str, Dict[str, Any]] = {}

    def create(self, task_id: str) -> None:
        self.snapshots[task_id] = self.workspace.snapshot()

    def restore(self, task_id: str) -> bool:
        snapshot = self.snapshots.get(task_id)
        if snapshot is None:
            return False
        self.workspace.restore(snapshot)
        return True

    def discard(self, task_id: str) -> None:
        self.snapshots.pop(task_id, None)


class RecoveryController:
    """Creates a request snapshot, rolls back failures and opens tool circuits."""

    def __init__(
        self, workspace: SnapshotWorkspace, failure_threshold: int = 3
    ) -> None:
        self.snapshots = SnapshotManager(workspace)
        self.breaker = CircuitBreaker(failure_threshold)
        self.incidents: Dict[str, Incident] = {}

    def before_execute(self, request: ToolRequest) -> None:
        self.breaker.before_call(request.tool_name)
        self.snapshots.create(request.request_id)

    def begin_task(self, task_id: str) -> None:
        self.snapshots.create(self._task_snapshot_key(task_id))

    def restore_task(self, task_id: str) -> bool:
        key = self._task_snapshot_key(task_id)
        restored = self.snapshots.restore(key)
        self.snapshots.discard(key)
        return restored

    def complete_task(self, task_id: str) -> None:
        self.snapshots.discard(self._task_snapshot_key(task_id))

    def on_success(self, request: ToolRequest) -> None:
        self.breaker.record_success(request.tool_name)
        self.snapshots.discard(request.request_id)

    def on_failure(self, request: ToolRequest, error: Exception) -> Incident:
        restored = self.snapshots.restore(request.request_id)
        self.snapshots.discard(request.request_id)
        circuit_opened = self.breaker.record_failure(request.tool_name)
        incident = Incident(
            task_id=request.task_id,
            request_id=request.request_id,
            tool_name=request.tool_name,
            error=str(error),
            restored=restored,
            circuit_opened=circuit_opened,
        )
        self.incidents[incident.incident_id] = incident
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)

    @staticmethod
    def _task_snapshot_key(task_id: str) -> str:
        return "task:{}".format(task_id)
