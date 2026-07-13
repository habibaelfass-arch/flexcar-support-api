"""
Simple bearer-token auth middleware for the internal Lovable API.
Set API_SECRET_KEY in your environment.
"""
from __future__ import annotations

import os
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)


async def require_auth(request: Request, call_next):
    """Middleware that rejects requests without a valid bearer token."""
    public_paths = {"/", "/health"}
    if request.url.path in public_paths:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    secret = os.environ.get("API_SECRET_KEY", "")

    if not secret:
        return await call_next(request)

    if not auth_header.startswith("Bearer ") or auth_header[7:] != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

    return await call_next(request)
