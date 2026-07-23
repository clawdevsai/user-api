"""UserId value object: UUID wrapper, equality by value."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserId:
    value: uuid.UUID

    @classmethod
    def new(cls) -> UserId:
        return cls(uuid.uuid4())

    def __str__(self) -> str:
        return str(self.value)
