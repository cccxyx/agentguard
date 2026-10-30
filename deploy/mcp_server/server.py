from __future__ import annotations

from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http_manager import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.mcp_service import AgentGuardMCPService

service = AgentGuardMCPService()
mcp = FastMCP(
    "agentguard-trusted-execution",
    streamable_http_path="/mcp",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def create_secure_activity(
    title: str,
    starts_at: str,
    location: str,
    recipient: str,
    recipient_count: int,
    notice_content: str,
    source_trust: str = "USER_CONFIRMED",
) -> Dict[str, Any]:
    """Create a passport-bound activity transaction and return its current state."""

    return service.create_secure_activity(
        title,
        starts_at,
        location,
        recipient,
        recipient_count,
        notice_content,
        source_trust,
    )


@mcp.tool()
def resolve_activity_approval(task_id: str, approved: bool) -> Dict[str, Any]:
    """Resume or reject a task waiting for a user confirmation."""

    return service.resolve_activity_approval(task_id, approved)


@mcp.tool()
def cancel_activity_task(task_id: str) -> Dict[str, Any]:
    """Cancel an unfinished task and restore its pre-task snapshot."""

    return service.cancel_activity_task(task_id)


@mcp.tool()
def get_activity_task(task_id: str) -> Dict[str, Any]:
    """Read a task state, task passport, plan and execution results."""

    return service.get_activity_task(task_id)


@mcp.tool()
def get_task_trace(task_id: str) -> Dict[str, Any]:
    """Read policy, approval, execution, rollback and circuit events for a task."""

    return service.get_task_trace(task_id)


@mcp.tool()
def submit_guarded_tool_request(
    task_id: str,
    agent_id: str,
    tool_name: str,
    action: str,
    arguments: Dict[str, Any],
    source_trust: str,
    passport_id: str,
) -> Dict[str, Any]:
    """Submit a passport-bound tool request to the deterministic policy gateway."""

    return service.submit_guarded_tool_request(
        task_id,
        agent_id,
        tool_name,
        action,
        arguments,
        source_trust,
        passport_id,
    )


@mcp.tool()
def runtime_status() -> Dict[str, Any]:
    """Return MCP runtime health, policy mode, tools and circuit states."""

    return service.runtime_status()


@mcp.custom_route("/ping", methods=["GET"])
async def ping(_request: Request) -> JSONResponse:
    return JSONResponse(service.runtime_status())


app = mcp.streamable_http_app()
