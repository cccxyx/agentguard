from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Dict, List

from backend.models import AuditEvent, Decision, ExecutionResult, ToolRequest
from backend.policy_engine import PolicyEngine


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

    def __init__(self, engine: PolicyEngine, registry: ToolRegistry) -> None:
        self.engine = engine
        self.registry = registry
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
            output = self.registry.execute(request)
            self._record(request, "TOOL_EXECUTED", {"output": output})
            return ExecutionResult(request.request_id, "SUCCEEDED", decision, output)
        except Exception as exc:  # boundary: tool failures become audit events
            self._record(request, "TOOL_FAILED", {"error": str(exc)})
            return ExecutionResult(
                request.request_id,
                "FAILED",
                decision,
                error=str(exc),
            )

    def _record(
        self, request: ToolRequest, event_type: str, payload: Dict[str, Any]
    ) -> None:
        self.audit_events.append(
            AuditEvent(event_type, request.request_id, request.task_id, payload)
        )

