"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from user_api.adapters.inbound.http.routers import internal_auth, users

app = FastAPI(title="User API")

app.include_router(users.router)
app.include_router(internal_auth.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ok"}
