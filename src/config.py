import os
from typing import Literal, Optional
from pydantic import BaseModel, Field

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT")

# Example schema to let llm know what tables are available

class DataTableFields(BaseModel):
    id: str = Field(None, alias="id", description="index of table")
    name: str = Field(None, alias="key", description="key of data")
    value: str = Field(None, alias="value", description="value of data")

SelectFieldsLiteral = Literal[
    "project_name", 
    "client_name", 
    "industry", 
    "reference_name", 
    "year_of_reference", 
    "project_context", 
    "short_description", 
    "challenge", 
    "solution", 
    "impact", 
    "learnings", 
    "lead_cc", 
    "project_lead_email", 
    "project_lead_prename", 
    "project_lead_surname", 
    "practices_involved_1", 
    "practices_involved_2", 
    "practices_involved_3", 
    "project_status", 
    "project_method", 
    "project_location", 
    "end_to_end", 
    "volume_keuro", 
    "project_start", 
    "project_end", 
    "usage"
]

class ProjectTable(BaseModel):
    id: int = Field(..., description="Unique identifier (int8)")

    # Core Project Info
    project_name: str = Field(..., description="Name of the project (varchar 300)")
    client_name: str = Field(..., description="Name of the client (varchar 255)")
    industry: Optional[str] = Field(None, description="Industry sector")

    reference_name: Optional[str] = Field(None, description="Name of the reference")
    year_of_reference: Optional[str] = Field(None, description="Year of reference creation")

    # Context & Descriptions
    project_context: Optional[str] = Field(None, description="Short internal description of the project TLDR")
    short_description: Optional[str] = Field(None, description="Short presentative description of the project")
    challenge: Optional[str] = Field(None, description="The challenge of the project example: 'Strengthen brand, reach new customers and improve loyalty'")
    solution: Optional[str] = Field(None, description="Steps taken to resolve challenge")
    impact: Optional[str] = Field(None, description="The impact of the project")
    learnings: Optional[str] = Field(None)

    # People & Roles
    lead_cc: Optional[str] = Field(None)
    project_lead_email: Optional[str] = Field(None)
    project_lead_prename: Optional[str] = Field(None)
    project_lead_surname: Optional[str] = Field(None)

    practices_involved_1: Optional[str] = Field(
        None, 
        description="Practices involved in the project for example: 't_microsoft, i_automotive, t_pimcore'"
    )
    practices_involved_2: Optional[str] = Field(
        None,
        description="Practices involved in the project for example: 'c_data-and-ai, i_pharma_ls, i_utilities'"
    )
    practices_involved_3: Optional[str] = Field(
        None,
        description="Practices involved in the project for example: 'i_insurance, t_sap, i_private-equity'"
    )

    # Status & Logistics
    project_status: Optional[Literal["finished", "ongoing", "-"]] = Field(
        default=None,
        description="The current status of the project."
    )
    project_method: Optional[str] = Field(
        None,
        description="The method used to solve the challenge it is comma separated methods for example: 'AI, Agile, SAP'"
    )
    project_location: Optional[str] = Field(
        None,
        description="The location of the project it is comma separated locations for example: 'Berlin, Germany'"
    )
    end_to_end: bool = Field(default=False, description="Boolean flag")
    volume_keuro: Optional[str] = Field(None, description="Financial volume in kEuro")

    # Dates
    project_start: Optional[str] = Field(None, description="The start date of the project format: YYYY-MM-DD")
    project_end: Optional[str] = Field(None, description="The end date of the project format: YYYY-MM-DD")

    usage: Optional[str] = Field(
        None,
        description="""Describes the usage of the data. Examples values: nda, ask-for-approval, free-to-use, internal-use"""
    )

class ProjectTableWithEmbeddings(ProjectTable):
    embedding_challenge: Optional[str] = Field(
        None,
        description="Semantic vector of challenge",
    )
    embedding_impact: Optional[str] = Field(
        None,
        description="Semantic vector of impact",
    )
    embedding_project_context: Optional[str] = Field(
        None,
        description="Semantic vector of project context",
    )
    embedding_project_location: Optional[str] = Field(
        None,
        description="Semantic vector of project location",
    )
    embedding_project_name: Optional[str] = Field(
        None,
        description="Semantic vector of project name",
    )
    embedding_reference_name: Optional[str] = Field(
        None,
        description="Semantic vector of reference name",
    )
    embedding_short_description: Optional[str] = Field(
        None,
        description="Semantic vector of short description",
    )
    embedding_solution: Optional[str] = Field(
        None,
        description="Semantic vector of solution",
    )

table_name = "v_project_table_with_embeddings"