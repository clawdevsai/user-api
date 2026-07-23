"""Structured (JSON) security audit logger (implements SecurityAuditLogger port)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("user_api.security")


class StructuredSecurityAuditLogger:
    def log_event(self, event_type: str, user_id: str | None, metadata: dict[str, Any]) -> None:
        record = {
            "event_type": event_type,
            "category": "security",
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
            **metadata,
        }
        logger.info(json.dumps(record))
