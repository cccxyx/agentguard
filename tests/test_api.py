import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.bootstrap import build_runtime


class ApiTests(unittest.TestCase):
    def setUp(self):
        gateway, _ = build_runtime()
        self.client = TestClient(create_app(gateway))

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_submit_and_read_trace(self):
        response = self.client.post(
            "/api/tool-requests",
            json={
                "task_id": "api-task-1",
                "agent_id": "activity-assistant",
                "tool_name": "calendar",
                "action": "create",
                "arguments": {
                    "title": "活动",
                    "starts_at": "2026-11-01T09:00:00",
                },
                "source_trust": "USER_CONFIRMED",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "SUCCEEDED")

        events = self.client.get("/api/tasks/api-task-1/events")
        self.assertEqual(events.status_code, 200)
        self.assertEqual(len(events.json()), 2)


if __name__ == "__main__":
    unittest.main()
