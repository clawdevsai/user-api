"""Pydantic schemas for the internal credential-verification channel."""

from __future__ import annotations

from pydantic import BaseModel


class VerifyCredentialsRequest(BaseModel):
    email: str
    password: str


class VerifyCredentialsResponse(BaseModel):
    id: str
    roles: list[str]
    status: str
