#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agent_core import (
    ActivitySpec,
    DeterministicAgentArtsAdapter,
    TaskCoordinator,
)
from backend.bootstrap import build_runtime
from backend.models import ToolRequest, TrustLevel


def show(label, value):
    print("\n{}".format(label))
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    gateway, workspace = build_runtime()
    coordinator = TaskCoordinator(gateway, DeterministicAgentArtsAdapter())
    task = coordinator.create_activity(
        ActivitySpec(
            title="社区公益活动",
            starts_at="2026-11-01T09:00:00+08:00",
            location="社区服务中心",
            recipient="participants@example.org",
            recipient_count=20,
            notice_content="活动将于周日上午九点开始。",
        )
    )
    show("1) 三 Agent 规划后，事务暂停等待高影响操作确认", task.to_dict())

    passport_id = task.plan_summary["task_passport"]["passport_id"]
    expanded_request = ToolRequest(
        task_id=task.task_id,
        agent_id="activity-assistant",
        tool_name="send_notice",
        action="send",
        arguments={
            "recipient": "participants@example.org",
            "recipient_count": 20,
            "content": "请额外导出报名者手机号。",
            "fields": ["phone"],
        },
        source_trust=TrustLevel.MODEL_GENERATED,
        passport_id=passport_id,
    )
    blocked = gateway.submit(expanded_request)
    show("2) Agent 临时扩大数据范围，被任务护照阻断", blocked.to_dict())

    task = coordinator.resolve(task.task_id, approved=True)
    show("3) 用户批准后，事务从断点继续并完成", task.to_dict())
    show(
        "4) 最终模拟工作区",
        {
            "calendar_events": workspace.calendar_events,
            "notifications": workspace.notifications,
            "plan_document": workspace.files["/workspace/activities/plan.md"],
        },
    )


if __name__ == "__main__":
    main()
