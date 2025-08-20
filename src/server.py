import asyncio
from dotenv import load_dotenv
from pathlib import Path
from fastmcp import FastMCP
from auth import BearerAuthMiddleware
from query import Query, QueryClasses, buildSelectSQL
import json

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

from db import get_db, run_migrations


mcp = FastMCP(
    "Database connection",
    streamable_http_path='',
    middleware=[BearerAuthMiddleware()]
)


# limitation currently it supports only one table
@mcp.tool()
async def getDataByQuery(query: Query) -> str:
    try:
        pool = await get_db()
        sql = buildSelectSQL(query)
        print(sql)
        
        async with pool.acquire() as conn:
            result = await conn.fetch(sql)  # use fetch, not execute
            rows = [dict(r) for r in result]
            print(rows)
            
            return json.dumps(rows)
    except Exception as e:
        print("Error:", e)
        return json.dumps([])
    

if __name__ == "__main__":
    asyncio.run(run_migrations())
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)