from typing import List, Optional, Union, Dict, Any, Literal, Tuple, ForwardRef
from pydantic import BaseModel, Field, create_model
from enum import Enum

 # fields should match the ones in the database
class FieldName(str, Enum):
    id = "id"
    name = "name"
    value = "value"


class RangeValue(BaseModel):
    from_: Optional[str] = Field(None, alias="from", description="Start of range (YYYY-MM-DD)")
    to: Optional[str] = Field(None, description="End of range (YYYY-MM-DD)")


class BetweenValue(BaseModel):
    from_: str = Field(..., alias="from", description="Start date (YYYY-MM-DD)")
    to: str = Field(..., description="End date (YYYY-MM-DD)")


class LeafCondition(BaseModel):
    field: FieldName
    # custom operators can be injected
    op: Literal[
        "eq", "neq", "contains", "starts_with", "ends_with", "ilike",
        "in", "not_in", "is_null", "is_not_null",
        "gt", "gte", "lt", "lte",
        "range", "between", "not_between", "semantic"
    ]
    value: Union[
        str,
        int,
        List[Union[str, int]],
        RangeValue,
        BetweenValue,
        "LeafCondition",
    ]


class BooleanNode(BaseModel):
    op: Literal["and", "or", "not"]
    children: List["FilterNode"] = Field(..., description="Nested conditions or groups")


FilterNode = Union[LeafCondition, BooleanNode]

class Query(BaseModel):
    filter_tree: Optional[FilterNode] = Field(None, description="Nested boolean tree with leaf conditions.")
    table_name: str = Field(..., description="Name of database table")
    limit: Optional[int] = Field(None, description="Max rows to return. Omit if no limit.")
    select_fields: Optional[List[FieldName]] = Field(None, description="List of fields to select. Omit if no selection.")

# Building pedantic schema for llm


def create_table_queries(db_schema: Dict[str, Dict[str, str]]):
    query_classes = {}

    for table_name, fields in db_schema.items():
        # Allowed fields for filter/select
        field_literals = Literal[tuple(fields.keys())]

        # --- LeafCondition ---
        leaf_class_name = f"{table_name.capitalize()}LeafCondition"
        LeafRef = ForwardRef(leaf_class_name)

        leaf_class = create_model(
            leaf_class_name,
            field=(field_literals, ...),
            op=(Literal[
                "eq", "neq", "contains", "starts_with", "ends_with", "ilike",
                "in", "not_in", "is_null", "is_not_null",
                "gt", "gte", "lt", "lte",
                "range", "between", "not_between"
            ], ...),
            value=(Union[
                str,
                int,
                float,
                List[Union[str, int, float]],
                RangeValue,
                BetweenValue,
                LeafRef
            ], ...)
        )

        # --- BooleanNode ---
        BooleanNode = create_model(
            f"{table_name.capitalize()}BooleanNode",
            op=(Literal["and", "or", "not"], ...),
            children=(List[Union[leaf_class, "BooleanNode"]], ...)
        )

        # Resolve forward references
        BooleanNode.model_rebuild()
        leaf_class.model_rebuild()

        FilterNode = Union[leaf_class, BooleanNode]

        # --- Table-specific Query class ---
        query_class_name = f"{table_name.capitalize()}Query"
        query_class = create_model(
            query_class_name,
            filter_tree=(FilterNode, ...),
            table_name=(Literal[table_name], ...),
            limit=(Optional[int], None),
            select_fields=(Optional[List[field_literals]], None)
        )

        query_classes[table_name] = query_class

    # Union of all Query classes
    QueryUnion = Union[tuple(query_classes.values())]

    return QueryUnion, query_classes



# Example schema
db_schema = {
    "data": {"id": "int", "name": "str", "value": "str"},
    "user": {"id": "int", "username": "str", "email": "str"}
}

QueryUnion, QueryClasses = create_table_queries(db_schema)


# Building sql from schema

def buildWhereSQL(node: FilterNode) -> Tuple[str, Dict[str, Any]]:
    params: Dict[str, Any] = {}

    def _leaf(n: Dict[str, Any], pnum: List[int]) -> str:
        field, op = str(n["field"]), str(n["op"])
        col = '"' + field.replace('"', '""') + '"'
        val = n.get("value", None)

        def _p(val_any) -> str:
            k = f"p{pnum[0]}"; pnum[0] += 1
            params[k] = val_any
            return f":{k}"
        
        def _escape_like(s: str) -> str:
           p = s.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
           return f"{_p(p)} ESCAPE '\\\\'"

        # Comparisons
        if op == "eq":        return f"{col} = {_p(val)}"
        if op == "neq":       return f"{col} <> {_p(val)}"
        if op == "gt":        return f"{col} > {_p(val)}"
        if op == "gte":       return f"{col} >= {_p(val)}"
        if op == "lt":        return f"{col} < {_p(val)}"
        if op == "lte":       return f"{col} <= {_p(val)}"

        # Text matching
        if op == "contains":
            pattern = _escape_like(f"%{val}%")
            return f"{col} ILIKE {pattern}"

        if op == "starts_with":
            pattern = _escape_like(f"{val}%")
            return f"{col} ILIKE {pattern}"

        if op == "ends_with":
            pattern = _escape_like(f"%{val}")
            return f"{col} ILIKE {pattern}"

        if op == "ilike":
            pattern = _escape_like(val if isinstance(val, str) else str(val))
            return f"{col} ILIKE {pattern}"

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

def buildSelectSQL(query: Query) -> str:
    limit = f" LIMIT {query.limit}" if query.limit is not None else ""

    if query.filter_tree is None:
        return f"SELECT * FROM {query.table_name}{limit}"

    sql, params = buildWhereSQL(query.filter_tree)

    if len(query.select_fields) > 0:
        return f"SELECT {', '.join(query.select_fields)} FROM {query.table_name} WHERE {sql}{limit}"
    
    return f"SELECT * FROM {query.table_name} WHERE {sql}{limit}"
