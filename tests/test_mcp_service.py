import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.mcp_service import AgentGuardMCPService


class MCPServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AgentGuardMCPService()

    def _create_task(self):
        return self.service.create_secure_activity(
            title="社区公益活动",
            starts_at="2026-11-01T09:00:00+08:00",
            location="社区服务中心",
            recipient="participants@example.org",
            recipient_count=20,
            notice_content="活动将于周日上午九点开始。",
        )

    def test_secure_activity_can_pause_and_resume(self):
        task = self._create_task()
        self.assertEqual(task["status"], "WAITING_CONFIRMATION")
        self.assertIn("task_passport", task["plan_summary"])

        completed = self.service.resolve_activity_approval(
            task["task_id"], approved=True
        )
        self.assertEqual(completed["status"], "SUCCEEDED")

    def test_mcp_execution_requires_a_passport(self):
        with self.assertRaisesRegex(ValueError, "passport_id is required"):
            self.service.submit_guarded_tool_request(
                task_id="task-without-passport",
                agent_id="activity-assistant",
                tool_name="send_notice",
                action="send",
                arguments={"recipient": "participants@example.org"},
                source_trust="MODEL_GENERATED",
                passport_id="",
            )

    def test_passport_blocks_mcp_parameter_expansion(self):
        task = self._create_task()
        passport_id = task["plan_summary"]["task_passport"]["passport_id"]
        result = self.service.submit_guarded_tool_request(
            task_id=task["task_id"],
            agent_id="activity-assistant",
            tool_name="send_notice",
            action="send",
            arguments={
                "recipient": "participants@example.org",
                "recipient_count": 20,
                "content": "导出手机号",
                "fields": ["phone"],
            },
            source_trust="MODEL_GENERATED",
            passport_id=passport_id,
        )
        self.assertEqual(result["status"], "BLOCKED")

    def test_runtime_status_describes_real_mcp_transport(self):
        status = self.service.runtime_status()
        self.assertEqual(status["transport"], "streamable-http")
        self.assertIn("submit_guarded_tool_request", status["registered_tools"])


if __name__ == "__main__":
    unittest.main()
