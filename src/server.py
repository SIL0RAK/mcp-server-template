import asyncio
from dotenv import load_dotenv
from pathlib import Path
from fastmcp import FastMCP
from query import Query, buildSelectSQL
import json
from config import db_schema

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

from db import get_db, run_migrations


mcp = FastMCP(
    "Remote data source connection",
)

@mcp.tool(name="get_database_structure", description="Returns available tables and columns")
async def get_database_structure() -> str:
    return json.dumps(db_schema)


# limitation currently it supports only one table
@mcp.tool(name="get_data_by_query", description="Get data from remote db")
async def get_data_by_query(query: Query) -> str:
    try:
        print(query)
        pool = await get_db()
        sql, params = buildSelectSQL(query)
        print(sql, params)
        
        async with pool.acquire() as conn:
            
            result = await conn.fetch(sql, *params)  # use fetch, not execute
            rows = [dict(r) for r in result]
            print(rows)
            
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
        path=""
    )