from __future__ import annotations

from backend.agent_core.contracts import (
    ActivitySpec,
    AgentEvidence,
    AgentRole,
    OrchestrationPlan,
)
from backend.models import ToolRequest


class DeterministicAgentArtsAdapter:
    """Offline AgentArts-compatible planner for development and competition demos.

    A real AgentArts workflow only needs to return the same OrchestrationPlan. It
    never receives direct tool credentials and cannot bypass the MCP gateway.
    """

    provider = "local-agentarts-compatible"

    def plan_activity(self, task_id: str, spec: ActivitySpec) -> OrchestrationPlan:
        steps = [
            ToolRequest(
                task_id=task_id,
                agent_id="activity-assistant",
                tool_name="calendar",
                action="create",
                arguments={
                    "title": spec.title,
                    "starts_at": spec.starts_at,
                    "location": spec.location,
                },
                source_trust=spec.source_trust,
            ),
            ToolRequest(
                task_id=task_id,
                agent_id="activity-assistant",
                tool_name="shared_file",
                action="update",
                arguments={
                    "path": "/workspace/activities/plan.md",
                    "content": self._build_plan_document(spec),
                },
                source_trust=spec.source_trust,
            ),
            ToolRequest(
                task_id=task_id,
                agent_id="activity-assistant",
                tool_name="send_notice",
                action="send",
                arguments={
                    "recipient": spec.recipient,
                    "recipient_count": spec.recipient_count,
                    "content": spec.notice_content,
                },
                source_trust=spec.source_trust,
            ),
        ]
        evidence = [
            AgentEvidence(
                AgentRole.BUSINESS,
                "已将活动目标拆解为日历、计划文档和通知三个事务步骤。",
                {"required_tools": [item.tool_name for item in steps]},
            ),
            AgentEvidence(
                AgentRole.CONTENT_ISOLATION,
                "输入来源已分级，外部内容不会继承用户授权。",
                {"source_trust": spec.source_trust.value},
            ),
            AgentEvidence(
                AgentRole.BEHAVIOR_GUARD,
                "识别到文件更新与对外通知，交由确定性策略引擎裁决。",
                {"high_impact_steps": ["shared_file.update", "send_notice.send"]},
            ),
        ]
        return OrchestrationPlan(task_id, steps, evidence, self.provider)

    @staticmethod
    def _build_plan_document(spec: ActivitySpec) -> str:
        return "# {}\n\n时间：{}\n地点：{}\n".format(
            spec.title, spec.starts_at, spec.location
        )
