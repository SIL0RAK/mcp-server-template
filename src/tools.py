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
        name="search_project_references",
        description=f"""
This tool combines structured SQL-style filtering with vector-based semantic search.

Capabilities:
Structured Filtering: Use the 'filters' object for exact or partial matches on metadata fields (Project Name, Client, Industry, Location, Start Date).

Semantic Search: Use the 'semantic_query' parameter to search for meaning, concepts, or intent within the project's Description, Impact, and Solution fields.

Constraints:
Semantic Search Limitation: Semantic/vector search is ONLY performed on embedded text fields (Description, Impact, Solutions). It cannot be used for dates or numeric values.

Client Search: When searching for a specific client (e.g., 'BMW'), always use the 'client_name' filter first.

Combined Queries: If a user asks for "AI solutions for BMW," populate 'client_name' with "BMW" and 'semantic_query' with "artificial intelligence."

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