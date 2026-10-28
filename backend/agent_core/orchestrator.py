from __future__ import annotations

from typing import List

from backend.mcp_gateway import MCPGateway
from backend.models import ExecutionResult, ToolRequest, TrustLevel


class DemoOrchestrator:
    """Temporary deterministic adapter; AgentArts will replace planning only."""

    def __init__(self, gateway: MCPGateway) -> None:
        self.gateway = gateway

    def create_activity(self, task_id: str) -> List[ExecutionResult]:
        requests = [
            ToolRequest(
                task_id=task_id,
                agent_id="activity-assistant",
                tool_name="calendar",
                action="create",
                arguments={
                    "title": "公益活动",
                    "starts_at": "2026-11-01T09:00:00+08:00",
                    "location": "社区服务中心",
                },
                source_trust=TrustLevel.USER_CONFIRMED,
            ),
            ToolRequest(
                task_id=task_id,
                agent_id="activity-assistant",
                tool_name="send_notice",
                action="send",
                arguments={
                    "recipient": "participants@example.org",
                    "recipient_count": 40,
                    "content": "活动将于周日上午九点开始。",
                },
                source_trust=TrustLevel.USER_CONFIRMED,
            ),
        ]
        return [self.gateway.submit(request) for request in requests]

