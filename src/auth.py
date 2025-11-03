from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
import os

API_TOKEN = os.getenv(
    "API_TOKEN",
    None
)

class BearerAuthMiddleware(Middleware):
    """
        Checks if authorization header is present and matches API_TOKEN
    """
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        if API_TOKEN is None:
            return await call_next(context)

        authHeader = context.fastmcp_context.get_http_request().headers.get("authorization")

        if authHeader != f"Bearer {API_TOKEN}":
            raise ToolError("Access denied: restricted resource")

        return await call_next(context)
