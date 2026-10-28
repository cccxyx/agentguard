import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.bootstrap import build_runtime
from backend.models import ToolRequest, TrustLevel


class RecoveryRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.gateway, self.workspace = build_runtime(failure_threshold=2)

    def _failing_update(self, task_id):
        request = ToolRequest(
            task_id=task_id,
            agent_id="activity-assistant",
            tool_name="shared_file",
            action="update",
            arguments={
                "path": "/workspace/activities/plan.md",
                "content": "损坏的中间状态",
                "simulate_failure": True,
            },
            source_trust=TrustLevel.USER_CONFIRMED,
        )
        pending = self.gateway.submit(request)
        self.assertEqual(pending.status, "PENDING_CONFIRMATION")
        return self.gateway.resolve(request.request_id, approved=True)

    def test_failed_mutation_is_rolled_back(self):
        original = self.workspace.files["/workspace/activities/plan.md"]
        result = self._failing_update("task-recovery-1")

        self.assertEqual(result.status, "RESTORED")
        self.assertEqual(
            self.workspace.files["/workspace/activities/plan.md"], original
        )
        event_types = [event.event_type for event in self.gateway.audit_events]
        self.assertIn("ROLLBACK_COMPLETED", event_types)

    def test_repeated_failures_open_circuit(self):
        self._failing_update("task-recovery-2")
        self._failing_update("task-recovery-3")
        states = self.gateway.recovery.breaker.states()
        self.assertTrue(states["shared_file"]["is_open"])

        request = ToolRequest(
            task_id="task-recovery-4",
            agent_id="activity-assistant",
            tool_name="shared_file",
            action="update",
            arguments={
                "path": "/workspace/activities/plan.md",
                "content": "不会被执行",
            },
            source_trust=TrustLevel.USER_CONFIRMED,
        )
        pending = self.gateway.submit(request)
        result = self.gateway.resolve(pending.request_id, approved=True)
        self.assertEqual(result.status, "CIRCUIT_OPEN")


if __name__ == "__main__":
    unittest.main()
