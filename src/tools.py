import json
from query import Query, buildSelectSQL
from config import db_schema
from db import get_db

def register_tools(mcp):
    """
        Define a function that takes mcp and registers tools by using FastMCP decorator
    """


    # Using FastMCP decorator to register tools
    @mcp.tool(
        name="get_data_value",
        description="Returns value from table data where id matches provided value"
    )
    async def get_data_value(id: int) -> str:
        """
            Example of dedicated tool for specific operation.
            Currently this is best approach to get consistent results form LLM.
        """
        try:
            pool = await get_db()
            async with pool.acquire() as conn:
                result = await conn.fetch("SELECT value FROM data WHERE id = $1", id)
                rows = [dict(r) for r in result]
                return json.dumps(rows)
        except Exception as e:
            print("Error:", e)
            return json.dumps([])


    @mcp.tool(
        name="get_data_by_query",
        description="Get data from remote db"
    )
    async def get_data_by_query(query: Query) -> str:
        """
            Example of generic tool that can be used to extract data from remote db.
            It is powerful tool but requires LLM to understand database structure.
            Some LLM may get lost using this approach
        """
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
    

    @mcp.tool(
        name="get_database_structure",
        description="Returns available tables and columns"
    )
    async def get_database_structure() -> str:
        """
            Returns data structures defined in db_schema to let LLM know what tables are available.
        """
        return json.dumps(db_schema)
        
    
    return [
        get_database_structure,
        get_data_by_query,
        get_data_value,
    ]
