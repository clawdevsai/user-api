"""Port: security event logging boundary (FR-014)."""

from __future__ import annotations

from typing import Any, Protocol


class SecurityAuditLogger(Protocol):
    def log_event(self, event_type: str, user_id: str | None, metadata: dict[str, Any]) -> None: ...
