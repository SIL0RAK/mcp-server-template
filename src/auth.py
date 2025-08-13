
import os

API_TOKEN = os.getenv(
    "API_TOKEN",
    None
)


class BearerAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if API_TOKEN is None:
            return await self.app(scope, receive, send)
    
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        headers = dict((k.decode().lower(), v.decode()) for k, v in scope.get("headers", []))
        auth = headers.get("authorization", "")
        ok = False

        if auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
            ok = token and API_TOKEN and (token == API_TOKEN)

        if not ok:
            async def send_unauthorized() -> None:
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b'Bearer realm="mcp", charset="UTF-8"'),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"detail":"Unauthorized"}',
                })
            return await send_unauthorized()

        scope.setdefault("state", {})
        scope["state"]["auth"] = {"token": "provided"}

        return await self.app(scope, receive, send)
