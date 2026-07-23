"""Domain errors. No framework imports — pure Python exceptions."""


class DomainError(Exception):
    """Base class for all domain errors."""


class InvalidEmail(DomainError):
    """Email format is invalid."""


class WeakPassword(DomainError):
    """Password does not meet the minimum complexity policy."""


class EmailAlreadyRegistered(DomainError):
    """A user with this email already exists."""


class InvalidCredentials(DomainError):
    """Email/password combination is invalid, or user does not exist/is inactive.

    Deliberately generic (FR-016): callers must not distinguish
    "user not found" from "wrong password" from "inactive user".
    """


class UserNotFound(DomainError):
    """No user exists with the given identifier."""


class UserInactive(DomainError):
    """User exists but is deactivated; operation is rejected."""


class Forbidden(DomainError):
    """Caller is not authorized to perform this operation."""
