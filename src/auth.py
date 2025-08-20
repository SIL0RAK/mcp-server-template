from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ResourceError
import os

API_TOKEN = os.getenv(
    "API_TOKEN",
    None
)

class BearerAuthMiddleware(Middleware):
    async def __call__(self, context: MiddlewareContext, call_next):
        if API_TOKEN is None:
            return call_next(context)

        authHeader = context.fastmcp_context.get_http_request().headers.get("authorization")

        try:
            if authHeader is None:
                raise ResourceError("Access denied: restricted resource")

            if authHeader != f"Bearer {API_TOKEN}":
                raise ResourceError("Access denied: restricted resource")

        except Exception:
            pass

        return  call_next(context)
