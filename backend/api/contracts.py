from typing import Any, Dict, Iterable, List

from backend.models import AuditEvent


def serialize_events(events: Iterable[AuditEvent]) -> List[Dict[str, Any]]:
    """Stable contract shared by API, frontend mocks and evaluation runners."""
    return [event.to_dict() for event in events]

