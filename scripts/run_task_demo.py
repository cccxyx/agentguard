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

    task = coordinator.resolve(task.task_id, approved=True)
    show("2) 用户批准后，事务从断点继续并完成", task.to_dict())
    show(
        "3) 最终模拟工作区",
        {
            "calendar_events": workspace.calendar_events,
            "notifications": workspace.notifications,
            "plan_document": workspace.files["/workspace/activities/plan.md"],
        },
    )


if __name__ == "__main__":
    main()
