"""Small in-memory sliding-window limiter for the costly LLM/API-backed endpoints (per client IP).
Single-process only; use a shared store (e.g. Redis) if you run multiple workers."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict = defaultdict(deque)


def limit(max_calls: int, per_seconds: int = 60):
    def dependency(request: Request):
        key = (request.client.host if request.client else "unknown", request.url.path)
        now = time.time()
        q = _hits[key]
        while q and now - q[0] > per_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(429, "Too many requests - please wait a moment and try again.")
        q.append(now)

    return dependency
