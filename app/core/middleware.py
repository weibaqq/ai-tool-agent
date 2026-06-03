import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger('ai_tool_agent')

async def request_context_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.2f", request_id, request.method, request.url.path, duration_ms)
        raise
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-Id"] = request_id
    logger.info("request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.2f", request_id, request.method, request.url.path, response.status_code, duration_ms)

    return response