"""JWT validation adapter: verifies signature (via JWKS), exp, iss, aud.

Never issues tokens — only validates tokens issued by the external IdP.
"""

from __future__ import annotations

import jwt
from jwt import PyJWKClient


class InvalidToken(Exception):
    """Token is missing, malformed, expired, or fails signature/claims validation."""


class JwtValidator:
    def __init__(self, jwks_url: str, issuer: str, audience: str) -> None:
        self._jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=300)
        self._issuer = issuer
        self._audience = audience

    def validate(self, token: str) -> dict[str, object]:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc
        return claims
