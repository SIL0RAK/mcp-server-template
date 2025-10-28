# Example schema to let llm know what tables are available
from pydantic import BaseModel, Field


class DataTableFields(BaseModel):
    id: str = Field(None, alias="id", description="index of table")
    name: str = Field(None, alias="key", description="key of data")
    value: str = Field(None, alias="value", description="value of data")

class DataTable(BaseModel):
    name: str = Field(None, alias="name", description="name of table")
    fields: list[DataTableFields]

db_schema = {
    "data": DataTable.model_json_schema()
}