
from dotenv import load_dotenv
from pathlib import Path

# Some of packages require a .env file to be loaded
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

import asyncio
from fastmcp import FastMCP
from query import Query, buildSelectSQL
import json
from config import db_schema
from auth import BearerAuthMiddleware
from db import get_db, run_migrations


mcp = FastMCP(
    version="1.0.0",
    name="Remote data source connection", 
    middleware=[BearerAuthMiddleware()],
    instructions="This server provides connection to remote datasets"
)

@mcp.tool(name="get_database_structure", description="Returns available tables and columns")
async def get_database_structure() -> str:
    return json.dumps(db_schema)


# Generic request that can get data from any table in the database
@mcp.tool(name="get_data_by_query", description="Get data from remote db")
async def get_data_by_query(query: Query) -> str:
    try:
        pool = await get_db()
        sql, params = buildSelectSQL(query)
        
        async with pool.acquire() as conn:
            
            result = await conn.fetch(sql, *params)
            rows = [dict(r) for r in result]
            
            return json.dumps(rows)
    except Exception as e:
        print("Error:", e)
        return json.dumps([])
    

if __name__ == "__main__":
    asyncio.run(run_migrations())
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        path="/"
    )