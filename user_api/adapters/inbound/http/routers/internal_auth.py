"""Internal service-to-service endpoint: credential verification.

Consumed only by the external IdP. Never register this router on a
public-facing ingress.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from user_api.adapters.inbound.http.deps import (
    get_verify_credentials_use_case,
    verify_internal_api_key,
)
from user_api.adapters.inbound.http.schemas.auth_schemas import (
    VerifyCredentialsRequest,
    VerifyCredentialsResponse,
)
from user_api.application.use_cases.verify_credentials import VerifyCredentials
from user_api.domain.exceptions import InvalidCredentials, InvalidEmail

router = APIRouter(
    prefix="/internal", tags=["internal"], dependencies=[Depends(verify_internal_api_key)]
)


@router.post("/credentials/verify", response_model=VerifyCredentialsResponse)
async def verify_credentials(
    payload: VerifyCredentialsRequest,
    use_case: VerifyCredentials = Depends(get_verify_credentials_use_case),
) -> VerifyCredentialsResponse:
    try:
        identity = await use_case.execute(payload.email, payload.password)
    except (InvalidCredentials, InvalidEmail) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.") from exc
    return VerifyCredentialsResponse(
        id=identity.id,
        roles=sorted(r.value for r in identity.roles),
        status=identity.status.value,
    )
