from pydantic import BaseModel, Field
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from fastmcp import FastMCP

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)


from db import get_db, run_migrations


mcp = FastMCP("Database connection")

class GetFieldValueInput(BaseModel):
    table_name: str = Field(..., description="Name of database table")
    field_name: str = Field(..., description="Name of database table column")
    value: str = Field(..., description="Value of database table column")


@mcp.tool()
async def getFieldValue(params: GetFieldValueInput) -> int:
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetch(f"SELECT * FROM {params.table_name} WHERE {params.field_name} = '{params.value}'")
        return result


@mcp.tool()
async def getDatabaseSchema():
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema='public'
        """)
        schema = {}
        for row in rows:
            schema.setdefault(row["table_name"], []).append(row["column_name"])
        return schema


if __name__ == "__main__":
    asyncio.run(run_migrations())
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)