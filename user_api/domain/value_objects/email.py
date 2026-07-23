"""Email value object: format-validated, lowercase-normalized."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from user_api.domain.exceptions import InvalidEmail

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str = field(compare=True)

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise InvalidEmail(f"Malformed email: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
