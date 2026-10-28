from __future__ import annotations

from typing import Any, Dict

from backend.mock_tools import MockWorkspace


class SnapshotManager:
    def __init__(self, workspace: MockWorkspace) -> None:
        self.workspace = workspace
        self.snapshots: Dict[str, Dict[str, Any]] = {}

    def create(self, task_id: str) -> None:
        self.snapshots[task_id] = self.workspace.snapshot()

    def restore(self, task_id: str) -> bool:
        snapshot = self.snapshots.get(task_id)
        if snapshot is None:
            return False
        self.workspace.restore(snapshot)
        return True

