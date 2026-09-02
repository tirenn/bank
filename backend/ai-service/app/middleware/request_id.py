import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.logger import request_id_ctx, trace_id_ctx

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("traceparent") or req_id

        token_req = request_id_ctx.set(req_id)
        token_trace = trace_id_ctx.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            request_id_ctx.reset(token_req)
            trace_id_ctx.reset(token_trace)

