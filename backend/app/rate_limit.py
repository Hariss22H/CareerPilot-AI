from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from .config import get_settings

_requests: dict[str, deque[datetime]] = defaultdict(deque)


async def enforce_rate_limit(request: Request):
    settings = get_settings()
    key = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=settings.rate_limit_window_seconds)
    bucket = _requests[key]
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_requests:
        raise HTTPException(status_code=429, detail={"success": False, "message": "Too many requests. Please try again shortly.", "error_code": "RATE_LIMITED"})
    bucket.append(now)

