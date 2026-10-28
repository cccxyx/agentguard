from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from backend.mcp_gateway import ToolRegistry


class MockWorkspace:
    """In-memory sandbox. It intentionally contains no real personal data."""

    def __init__(self) -> None:
        self.calendar_events: List[Dict[str, Any]] = []
        self.notifications: List[Dict[str, Any]] = []
        self.files: Dict[str, str] = {
            "/workspace/activities/plan.md": "活动计划 v1",
            "/workspace/activities/roster.csv": "name,role\n用户A,志愿者",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "calendar_events": deepcopy(self.calendar_events),
            "notifications": deepcopy(self.notifications),
            "files": deepcopy(self.files),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self.calendar_events = deepcopy(snapshot["calendar_events"])
        self.notifications = deepcopy(snapshot["notifications"])
        self.files = deepcopy(snapshot["files"])

    def calendar_tool(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if action != "create":
            raise ValueError("unsupported calendar action: {}".format(action))
        event = {
            "title": arguments["title"],
            "starts_at": arguments["starts_at"],
            "location": arguments.get("location"),
        }
        self.calendar_events.append(event)
        return {"created": True, "event": event}

    def notice_tool(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if action != "send":
            raise ValueError("unsupported notice action: {}".format(action))
        notice = {
            "recipient": arguments["recipient"],
            "recipient_count": arguments.get("recipient_count", 1),
            "content": arguments["content"],
        }
        self.notifications.append(notice)
        return {"sent": True, "notice": notice}

    def file_tool(self, action: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        path = arguments["path"]
        if action == "read":
            return {"path": path, "content": self.files[path]}
        if action == "update":
            self.files[path] = arguments["content"]
            return {"updated": True, "path": path}
        if action == "delete":
            self.files.pop(path, None)
            return {"deleted": True, "path": path}
        raise ValueError("unsupported file action: {}".format(action))


def register_workspace_tools(registry: ToolRegistry, workspace: MockWorkspace) -> None:
    registry.register("calendar", workspace.calendar_tool)
    registry.register("send_notice", workspace.notice_tool)
    registry.register("shared_file", workspace.file_tool)

