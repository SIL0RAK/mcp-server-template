
from dotenv import load_dotenv
from pathlib import Path

# Some of packages require a .env file to be loaded
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

import asyncio
from fastmcp import FastMCP
from auth import BearerAuthMiddleware
from db import run_migrations
from tools import register_tools


mcp = FastMCP(
    version="1.0.0",
    name="Remote data source connection", 
    middleware=[BearerAuthMiddleware()],
    instructions="This server provides connection to remote datasets",
)

register_tools(mcp)


if __name__ == "__main__":
    asyncio.run(run_migrations())
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/"
    )