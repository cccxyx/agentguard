from pathlib import Path
from typing import Tuple

from backend.mcp_gateway import MCPGateway, ToolRegistry
from backend.mock_tools import MockWorkspace, register_workspace_tools
from backend.policy_engine import PolicyEngine, PolicyRepository
from backend.recovery import RecoveryController

ROOT = Path(__file__).resolve().parents[1]


def build_runtime(failure_threshold: int = 3) -> Tuple[MCPGateway, MockWorkspace]:
    repository = PolicyRepository.from_json(ROOT / "config" / "policies.json")
    engine = PolicyEngine(repository)
    registry = ToolRegistry()
    workspace = MockWorkspace()
    register_workspace_tools(registry, workspace)
    recovery = RecoveryController(workspace, failure_threshold=failure_threshold)
    return MCPGateway(engine, registry, recovery), workspace
