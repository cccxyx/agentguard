from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.bootstrap import build_runtime
from backend.mcp_gateway import MCPGateway
from backend.models import ToolRequest, TrustLevel


class ToolRequestBody(BaseModel):
    task_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    action: str = Field(min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    source_trust: TrustLevel


class ApprovalBody(BaseModel):
    approved: bool


def create_app(gateway: Optional[MCPGateway] = None) -> FastAPI:
    runtime_gateway = gateway or build_runtime()[0]
    app = FastAPI(
        title="御界 AgentGuard API",
        version="0.2.0",
        description="工具型智能体可信执行、审批、审计与恢复接口",
    )
    app.state.gateway = runtime_gateway

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "service": "agentguard"}

    @app.post("/api/tool-requests")
    def submit_tool_request(body: ToolRequestBody) -> Dict[str, Any]:
        request = ToolRequest(
            task_id=body.task_id,
            agent_id=body.agent_id,
            tool_name=body.tool_name,
            action=body.action,
            arguments=body.arguments,
            source_trust=body.source_trust,
        )
        return runtime_gateway.submit(request).to_dict()

    @app.post("/api/approvals/{request_id}/decision")
    def resolve_approval(request_id: str, body: ApprovalBody) -> Dict[str, Any]:
        try:
            return runtime_gateway.resolve(request_id, body.approved).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/tasks/{task_id}/events")
    def task_events(task_id: str) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in runtime_gateway.events_for_task(task_id)]

    @app.get("/api/incidents/{incident_id}")
    def incident(incident_id: str) -> Dict[str, Any]:
        recovery = runtime_gateway.recovery
        value = recovery.get_incident(incident_id) if recovery else None
        if value is None:
            raise HTTPException(status_code=404, detail="incident not found")
        return value.to_dict()

    @app.get("/api/runtime/circuits")
    def circuits() -> Dict[str, Dict[str, Any]]:
        if not runtime_gateway.recovery:
            return {}
        return runtime_gateway.recovery.breaker.states()

    return app


app = create_app()
