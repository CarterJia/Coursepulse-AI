from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BYOKMiddleware(BaseHTTPMiddleware):
    """Read X-User-API-Key and store it on request.state.user_api_key.

    Empty strings are treated as absent. Value is never logged.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        raw = request.headers.get("X-User-API-Key")
        request.state.user_api_key = raw or None
        return await call_next(request)
