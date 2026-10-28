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


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    BLOCKED = "BLOCKED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RESTORED = "RESTORED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ToolRequest:
    task_id: str
    agent_id: str
    tool_name: str
    action: str
    arguments: Dict[str, Any]
    source_trust: TrustLevel
    passport_id: Optional[str] = None
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


@dataclass(frozen=True)
class Incident:
    task_id: str
    request_id: str
    tool_name: str
    error: str
    restored: bool
    circuit_opened: bool
    incident_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskRecord:
    intent: str
    status: TaskStatus
    total_steps: int
    task_id: str = field(default_factory=lambda: str(uuid4()))
    current_step: int = 0
    pending_request_id: Optional[str] = None
    plan_summary: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(frozen=True)
class PassportGrant:
    tool_name: str
    action: str
    authorized_arguments: Dict[str, Any]
    request_fingerprint: str


@dataclass(frozen=True)
class TaskPassport:
    task_id: str
    grants: List[PassportGrant]
    expires_at: str
    fingerprint: str
    passport_id: str = field(default_factory=lambda: str(uuid4()))
    issued_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
