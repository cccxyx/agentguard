from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from backend.models import AuditEvent, Decision, ExecutionResult, ToolRequest
from backend.policy_engine import PolicyEngine
from backend.recovery import CircuitOpenError, RecoveryController

ToolHandler = Callable[[str, Dict[str, Any]], Dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, ToolHandler] = {}

    def register(self, tool_name: str, handler: ToolHandler) -> None:
        if tool_name in self._handlers:
            raise ValueError("tool already registered: {}".format(tool_name))
        self._handlers[tool_name] = handler

    def execute(self, request: ToolRequest) -> Dict[str, Any]:
        handler = self._handlers.get(request.tool_name)
        if handler is None:
            raise KeyError("tool not registered: {}".format(request.tool_name))
        return handler(request.action, request.arguments)


class MCPGateway:
    """The only component allowed to call registered tools."""

    def __init__(
        self,
        engine: PolicyEngine,
        registry: ToolRegistry,
        recovery: Optional[RecoveryController] = None,
    ) -> None:
        self.engine = engine
        self.registry = registry
        self.recovery = recovery
        self.pending: Dict[str, ToolRequest] = {}
        self.audit_events: List[AuditEvent] = []

    def submit(self, request: ToolRequest) -> ExecutionResult:
        decision = self.engine.evaluate(request)
        self._record(request, "POLICY_DECISION", decision.to_dict())

        if decision.decision == Decision.BLOCK:
            return ExecutionResult(
                request.request_id,
                "BLOCKED",
                decision.decision,
                error="; ".join(reason.message for reason in decision.reasons),
            )

        if decision.decision == Decision.CONFIRM:
            self.pending[request.request_id] = request
            self._record(request, "APPROVAL_REQUIRED", {"status": "PENDING"})
            return ExecutionResult(
                request.request_id,
                "PENDING_CONFIRMATION",
                decision.decision,
            )

        return self._execute(request, decision.decision)

    def resolve(self, request_id: str, approved: bool) -> ExecutionResult:
        request = self.pending.pop(request_id, None)
        if request is None:
            raise KeyError("pending request not found: {}".format(request_id))

        self._record(request, "APPROVAL_RESOLVED", {"approved": approved})
        if not approved:
            return ExecutionResult(
                request.request_id,
                "REJECTED",
                Decision.CONFIRM,
                error="用户拒绝了该操作。",
            )
        return self._execute(request, Decision.CONFIRM)

    def _execute(self, request: ToolRequest, decision: Decision) -> ExecutionResult:
        try:
            if self.recovery:
                self.recovery.before_execute(request)
            output = self.registry.execute(request)
            if self.recovery:
                self.recovery.on_success(request)
            self._record(request, "TOOL_EXECUTED", {"output": output})
            return ExecutionResult(request.request_id, "SUCCEEDED", decision, output)
        except CircuitOpenError as exc:
            self._record(
                request,
                "CIRCUIT_REJECTED",
                {"tool_name": request.tool_name, "error": str(exc)},
            )
            return ExecutionResult(
                request.request_id,
                "CIRCUIT_OPEN",
                decision,
                error=str(exc),
            )
        except Exception as exc:  # boundary: tool failures become audit events
            incident = self.recovery.on_failure(request, exc) if self.recovery else None
            payload: Dict[str, Any] = {"error": str(exc)}
            if incident:
                payload["incident"] = incident.to_dict()
                self._record(
                    request,
                    "ROLLBACK_COMPLETED" if incident.restored else "ROLLBACK_SKIPPED",
                    incident.to_dict(),
                )
                if incident.circuit_opened:
                    self._record(
                        request,
                        "CIRCUIT_OPENED",
                        {"tool_name": request.tool_name},
                    )
            self._record(request, "TOOL_FAILED", payload)
            return ExecutionResult(
                request.request_id,
                "RESTORED" if incident and incident.restored else "FAILED",
                decision,
                error=str(exc),
            )

    def events_for_task(self, task_id: str) -> List[AuditEvent]:
        return [event for event in self.audit_events if event.task_id == task_id]

    def _record(
        self, request: ToolRequest, event_type: str, payload: Dict[str, Any]
    ) -> None:
        self.audit_events.append(
            AuditEvent(event_type, request.request_id, request.task_id, payload)
        )
