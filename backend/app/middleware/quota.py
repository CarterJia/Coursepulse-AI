from __future__ import annotations

import threading
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_counter: dict[str, tuple[int, str]] = {}
_lock = threading.Lock()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_counter_for_tests() -> None:
    with _lock:
        _counter.clear()


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class QuotaMiddleware(BaseHTTPMiddleware):
    """Limit POSTs to a guarded path to N per IP per UTC day.

    BYOK bypass: when ``request.state.user_api_key`` is truthy (set by BYOKMiddleware),
    the quota check is skipped. Register BYOKMiddleware BEFORE QuotaMiddleware so the
    attribute is populated in time.
    """

    def __init__(self, app, *, limit: int, guarded_path: str):
        super().__init__(app)
        self.limit = limit
        self.guarded_path = guarded_path

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.method != "POST" or request.url.path != self.guarded_path:
            return await call_next(request)

        if getattr(request.state, "user_api_key", None):
            return await call_next(request)

        ip = _client_ip(request)
        today = _today_utc()

        with _lock:
            count, day = _counter.get(ip, (0, today))
            if day != today:
                count = 0
                day = today
            if count >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Daily quota exhausted", "use_byok": True},
                )
            count += 1
            _counter[ip] = (count, day)
            remaining = max(self.limit - count, 0)

        response = await call_next(request)
        response.headers["X-Quota-Remaining"] = str(remaining)
        return response
