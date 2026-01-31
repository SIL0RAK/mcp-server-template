from typing import List, Optional, TypedDict, Union, Dict, Any, Literal, Tuple, get_args
from pydantic import BaseModel, Field
from config import SelectFieldsLiteral
from llm import Embeddings

class RangeValue(BaseModel):
    min: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max: Optional[float] = Field(None, description="Maximum value (inclusive)")

class SemanticValue(BaseModel):
    query: str = Field(..., description="The natural language string to search for semantically. Try to match structure of field to get best semantic results. It should always be in EN language")
    threshold: Optional[float] = Field(0.7, description="Distance threshold.")

class NumericCondition(BaseModel):
    field: str
    op: Literal["eq", "neq", "gt", "gte", "lt", "lte"]
    value: Union[int, float] = Field(..., description="Numeric value for comparison")

class StringCondition(BaseModel):
    field: str
    op: Literal["starts_with", "ends_with", "contains"]
    value: str = Field(..., description="String pattern to match")

class ListCondition(BaseModel):
    field: str
    op: Literal["contains_all", "contains_any"] 
    value: List[Union[str, int]] = Field(..., description="List of values to match against an array column")

class RangeCondition(BaseModel):
    field: str
    op: Literal["between", "not_between"]
    value: RangeValue

class SemanticCondition(BaseModel):
    field: str = Field(
        ..., 
        description="The database column name to perform a semantic search on."
    )
    op: Literal["semantic"]
    value: SemanticValue

class NullCondition(BaseModel):
    field: str
    op: Literal["is_null", "is_not_null"]
    value: Optional[None] = Field(None, description="No value needed for null checks")

LeafCondition = Union[
    NumericCondition,
    StringCondition,
    ListCondition,
    RangeCondition,
    SemanticCondition,
    NullCondition
]

class BooleanNode(BaseModel):
    op: Literal["and", "or", "not"]
    children: List["FilterNode"] = Field(..., description="Nested conditions or groups")


FilterNode = Union[LeafCondition, BooleanNode]

class Query(BaseModel):
    filter_tree: Optional[FilterNode] = Field(None, description="Nested boolean tree with leaf conditions.")
    limit: Optional[int] = Field(10, description="Max rows to return. Omit if no limit.")
    select_fields: Optional[List[str]] = Field(None, description="List of fields to select. Omit if no selection.")
    offset: Optional[int] = Field(0, description="Offset for pagination.")
    table_name: str


def buildWhereSQL(node: FilterNode, embeddings: Embeddings) -> Tuple[str, Dict[str, Any]]:
    """
        Builds a SQL where clause from a boolean tree.
    """

    params: Dict[str, Any] = {}

    def _leaf(n: Dict[str, Any], pnum: List[int]) -> str:
        field, op = str(n["field"]), str(n["op"])
        col = '"' + field.replace('"', '""') + '"'
        val = n.get("value", None)

        def _p(val_any) -> str:
            k = f"p{pnum[0]}"; pnum[0] += 1
            params[k] = val_any
            return f":{k}"
    
    
        # Comparisons
        if op == "eq":        return f"{col} = {_p(val)}"
        if op == "neq":       return f"{col} <> {_p(val)}"
        if op == "gt":        return f"{col} > {_p(val)}"
        if op == "gte":       return f"{col} >= {_p(val)}"
        if op == "lt":        return f"{col} < {_p(val)}"
        if op == "lte":       return f"{col} <= {_p(val)}"

        # semantic
        if op == "semantic":
            vector_val = embeddings.embed(val["query"])
            threshold_val = val["threshold"]
            p_vector = _p(f"""[{", ".join(map(str, vector_val))}]""")
            p_threshold = _p(threshold_val)
            return f"{col} <=> {p_vector} <= {p_threshold}"
        
        # List matching
        if op == "contains_any":
            return f"{col} && {_p(val)}"
        if op == "contains_all":
            return f"{col} @> {_p(val)}"
        

        if op in ["ilike", "contains", "starts_with", "ends_with"]:
            escaped_input = str(val).replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
                  # 2. Add the wildcards AFTER escaping
            if op == "contains": 
                final_val = f"%{escaped_input}%"
            elif op == "starts_with": 
                final_val = f"{escaped_input}%"
            elif op == "ends_with": 
                final_val = f"%{escaped_input}"

            return f"{col} ILIKE {_p(final_val)} ESCAPE '\\'"

        # IN / NOT IN
        if op in {"in", "not_in"}:
            base_idx = pnum[0]; pnum[0] += 1  # reserve a base index
            placeholders = []
            for i, v in enumerate(val):
                k = f"p{base_idx}_{i}"
                params[k] = v
                placeholders.append(f":{k}")
            kw = "IN" if op == "in" else "NOT IN"
            return f"{col} {kw} ({', '.join(placeholders)})"

        # NULL checks
        if op == "is_null":     return f"{col} IS NULL"
        if op == "is_not_null": return f"{col} IS NOT NULL"

        # BETWEEN / NOT BETWEEN (inclusive)
        if op in {"between", "not_between"}:
            k1 = f"p{pnum[0]}"; pnum[0] += 1
            k2 = f"p{pnum[0]}"; pnum[0] += 1
            params[k1], params[k2] = n["value"]["from"], n["value"]["to"]
            kw = "BETWEEN" if op == "between" else "NOT BETWEEN"
            return f"{col} {kw} :{k1} AND :{k2}"

        # RANGE (open/half-open)
        if op == "range":
            parts = []
            rng = n["value"]
            if "from" in rng and rng["from"] is not None:
                parts.append(f"{col} >= {_p(rng['from'])}")
            if "to" in rng and rng["to"] is not None:
                parts.append(f"{col} <= {_p(rng['to'])}")
            return "(" + " AND ".join(parts) + ")"

        raise ValueError(f"Unhandled operator: {op}")


    def _build(n: Dict[str, Any], pnum: List[int]) -> str:
        if "field" in n:
            return _leaf(n, pnum)

        op = n["op"]
        children = n.get("children") or []

        if op == "not":
            return f"NOT ({_build(children[0], pnum)})"

        joiner = " AND " if op == "and" else " OR "
        return "(" + joiner.join(_build(c, pnum) for c in children) + ")"


    sql = _build(node, [0])
    return sql, params


def convert_named_params_for_asyncpg(sql: str, params: dict):
    """Convert :name params to asyncpg's $1, $2... style"""
    values = []
    for i, (key, val) in enumerate(params.items(), start=1):
        sql = sql.replace(f":{key}", f"${i}")
        values.append(val)
    return sql, values

class QueryPayload(TypedDict):
    sql: str
    params: List[Any]

class SQLResponse(TypedDict):
    data: QueryPayload
    count: QueryPayload

def buildSelectSQL(query: Query, embeddings: Embeddings) -> SQLResponse:
    limit_str = f" LIMIT {query.limit}" if query.limit is not None else ""
    offset_str = f" OFFSET {query.offset}" if query.offset is not None else ""
    
    if query.filter_tree is None:
        where_clause = ""
        params = []
    else:
        where_clause, params = buildWhereSQL(query.filter_tree.model_dump(), embeddings)
        where_clause, params = convert_named_params_for_asyncpg(where_clause, params)
        where_clause = f" WHERE {where_clause}"

    fields_tuple = get_args(SelectFieldsLiteral)
    fields_string = ", ".join(fields_tuple)

    select_cols = ", ".join(query.select_fields) if query.select_fields else fields_string
    data_sql = f"SELECT {select_cols} FROM {query.table_name}{where_clause}{limit_str}{offset_str}"
    count_sql = f"SELECT COUNT(*) as total FROM {query.table_name}{where_clause}"

    return {
        "data": {"sql": data_sql, "params": params},
        "count": {"sql": count_sql, "params": params}
    }


def generate_schema_description(table_model: type[BaseModel]) -> str:
    """Generates a human-readable (LLM-readable) schema for the tool description."""
    lines = ["Available Table Fields:"]
    for name, field in table_model.model_fields.items():     
        f_type = str(field.annotation).replace("typing.", "")
        desc = field.description or "No description provided."
        lines.append(f"- **{name}** ({f_type}): {desc}")
    
    return "\n".join(lines)

def shape_response(
    data: List[Dict[str, Any]],
    indicator_field: str,
    indicator_namespace: str
) -> str:
    """
    Converts a list of dictionaries into a readable Markdown format.
    """
    if not data:
        return "No records found."

    formatted_blocks = []
    
    for record in data:
        # Get the value for the header, default to 'Record' if field missing
        header_value = record.get(indicator_field, "Record")
        
        # Build the lines for this specific record
        lines = [f"### {indicator_namespace} {header_value}"]
        
        for key, value in record.items():
            if key == indicator_field:
                continue

            if value is None:
                continue
            
            lines.append(f"{key}: {value}")
        
        formatted_blocks.append("\n".join(lines))

    return "\n\n".join(formatted_blocks)
    
