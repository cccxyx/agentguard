from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Decision(str, Enum):
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TrustLevel(str, Enum):
    SYSTEM_TRUSTED = "SYSTEM_TRUSTED"
    USER_CONFIRMED = "USER_CONFIRMED"
    INTERNAL_REFERENCE = "INTERNAL_REFERENCE"
    EXTERNAL_UNTRUSTED = "EXTERNAL_UNTRUSTED"
    MODEL_GENERATED = "MODEL_GENERATED"


@dataclass(frozen=True)
class ToolRequest:
    task_id: str
    agent_id: str
    tool_name: str
    action: str
    arguments: Dict[str, Any]
    source_trust: TrustLevel
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RiskEvidence:
    code: str
    message: str
    level: RiskLevel
    field: Optional[str] = None
    observed: Optional[Any] = None
    expected: Optional[Any] = None


@dataclass(frozen=True)
class PolicyDecision:
    request_id: str
    decision: Decision
    risk_level: RiskLevel
    reasons: List[RiskEvidence]
    policy_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        value["risk_level"] = self.risk_level.value
        for reason in value["reasons"]:
            reason["level"] = reason["level"].value
        return value


@dataclass(frozen=True)
class ExecutionResult:
    request_id: str
    status: str
    decision: Decision
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        return value


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    request_id: str
    task_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

