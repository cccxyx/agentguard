from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, Optional, Set

from backend.models import PassportGrant, TaskPassport, ToolRequest


def request_fingerprint(request: ToolRequest) -> str:
    """Fingerprint the authority-relevant, immutable portion of a tool call."""

    payload = {
        "task_id": request.task_id,
        "agent_id": request.agent_id,
        "tool_name": request.tool_name,
        "action": request.action,
        "arguments": request.arguments,
        "source_trust": request.source_trust.value,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def approval_fingerprint(request: ToolRequest) -> str:
    """Bind user approval to both request content and its authority passport."""

    payload = {
        "request_fingerprint": request_fingerprint(request),
        "passport_id": request.passport_id,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PassportRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, TaskPassport] = {}
        self._consumed: Dict[str, Set[str]] = {}
        self._lock = Lock()

    def add(self, passport: TaskPassport) -> None:
        with self._lock:
            self._items[passport.passport_id] = passport
            self._consumed[passport.passport_id] = set()

    def get(self, passport_id: str) -> Optional[TaskPassport]:
        return self._items.get(passport_id)

    def is_consumed(self, passport_id: str, fingerprint: str) -> bool:
        return fingerprint in self._consumed.get(passport_id, set())

    def consume(self, passport_id: str, fingerprint: str) -> bool:
        """Atomically consume a grant so an exact tool call cannot be replayed."""

        with self._lock:
            consumed = self._consumed.get(passport_id)
            if consumed is None or fingerprint in consumed:
                return False
            consumed.add(fingerprint)
            return True


class PassportIssuer:
    """Issues exact, time-bounded capabilities for an already approved task plan."""

    def __init__(self, registry: PassportRegistry, ttl_minutes: int = 30) -> None:
        if ttl_minutes < 1:
            raise ValueError("ttl_minutes must be positive")
        self.registry = registry
        self.ttl_minutes = ttl_minutes

    def issue(self, task_id: str, requests):
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=self.ttl_minutes)
        ).isoformat()
        grants = [
            PassportGrant(
                tool_name=request.tool_name,
                action=request.action,
                authorized_arguments=request.arguments,
                request_fingerprint=request_fingerprint(request),
            )
            for request in requests
        ]
        passport_fingerprint = self._passport_fingerprint(task_id, expires_at, grants)
        passport = TaskPassport(
            task_id=task_id,
            grants=grants,
            expires_at=expires_at,
            fingerprint=passport_fingerprint,
        )
        self.registry.add(passport)
        bound_requests = [
            replace(request, passport_id=passport.passport_id) for request in requests
        ]
        return passport, bound_requests

    @staticmethod
    def _passport_fingerprint(task_id, expires_at, grants):
        payload = {
            "task_id": task_id,
            "expires_at": expires_at,
            "grants": [grant.request_fingerprint for grant in grants],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_passport(
    request: ToolRequest, registry: PassportRegistry
) -> Optional[str]:
    if not request.passport_id:
        return None
    passport = registry.get(request.passport_id)
    if passport is None:
        return "任务护照不存在。"
    if passport.task_id != request.task_id:
        return "任务护照与当前任务不匹配。"
    if datetime.now(timezone.utc) >= datetime.fromisoformat(passport.expires_at):
        return "任务护照已过期。"
    fingerprint = request_fingerprint(request)
    if fingerprint not in {grant.request_fingerprint for grant in passport.grants}:
        return "工具请求超出了任务护照授权范围。"
    if registry.is_consumed(request.passport_id, fingerprint):
        return "任务护照中的该项授权已经使用，禁止重复执行。"
    return None
