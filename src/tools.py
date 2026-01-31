import functools
import json
from typing import List, Optional, Sequence
from query import FilterNode, Query, buildSelectSQL, generate_schema_description, shape_response
from config import table_name, ProjectTableWithEmbeddings, SelectFieldsLiteral
from db import get_db
from pydantic import ValidationError
from llm import Embeddings

def safe_tool(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            return f"Validation Error: Your payload was malformed. {str(e)}"
        except Exception as e:
            return f"Internal Tool Error: {str(e)}"
    return wrapper


def register_tools(mcp):
    embeddings = Embeddings()

    @mcp.tool(
        name="get_data_by_query",
        description=f"""
Generic tool to extract data from the database using structured filters and semantic search.

Using this tool user should be able to answer questions like:

* List all projects with a specific name
* List all projects with a specific name and a specific description
* List all projects with a specific name and a specific description and a specific industry
* List all projects with a specific name and a specific description and a specific industry and a specific location
* List all projects with a specific name and a specific description and a specific industry and a specific location and a specific start date
* Get detail description of certain project reference


Sample cases:

* Provide solutions that have association with artificial intelligence - 
it should use semantic search to look for similar solution names, description and impact embedded fields.

* Search for projects for client BMW - 
it should search for client names that include BMW, and then use semantic search to look for similar project names, description and impact embedded fields. 

! Important semantic search can only be performed on embedded fields

### Table Schema:

{generate_schema_description(ProjectTableWithEmbeddings)}
        """
    )
    @safe_tool
    async def get_data_by_query(
            filter_tree: Optional[FilterNode] = None,
            limit: Optional[int] = 10,
            offset: Optional[int] = 0,
            select_fields: Optional[List[SelectFieldsLiteral]] = None
        ) -> str:
        try:
            query = Query(
                filter_tree=filter_tree,
                limit=limit,
                offset=offset,
                select_fields=select_fields,
                table_name=table_name
            )

            pool = await get_db()
            queries = buildSelectSQL(query, embeddings)

            async with pool.acquire() as conn:
                result = await conn.fetch(queries["data"]["sql"], *queries["data"]["params"])
                total_count = await conn.fetchval(queries["count"]["sql"], *queries["count"]["params"])
                rows = [dict(r) for r in result]
                response = shape_response(rows, 'project_name', 'Project:')
            
                return f"""
## Query results

{response}

## Query pagination

Loaded {len(rows)} of {total_count}.
Notify user about total records count, and how many records were loaded.
"""
        except Exception as e:
            print("Error:", e)
            return json.dumps({"error": str(e)})