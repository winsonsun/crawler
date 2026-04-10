from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------
# The Canopy: Canonical Universal Schemas
# ---------------------------------------------------------

class Magnet(BaseModel):
    """Leaf Node: Represents the physical file payload for download."""
    link: str = Field(..., description="The magnet link or URL")
    size: str = Field(..., description="Extracted precise file size (e.g., '4.2GB'). Do not infer sizes.")
    date: str = Field(..., description="Upload date, critical for recency sorting")
    title: Optional[str] = Field(None, description="Title of the magnet release if available")
    number: Optional[str] = Field(None, description="The number/ID associated with this magnet release")
    
    model_config = ConfigDict(
        json_schema_extra={
            "llm_constraint": "MUST extract precise file sizes (e.g., 4.2GB) and upload dates if available. Do not infer sizes."
        }
    )


class Performer(BaseModel):
    """Leaf Node: Represents an actor/actress linked to media."""
    id: str = Field(..., description="The unique canonical ID")
    name: str = Field(..., description="The primary canonical name. Prefer Japanese, then English.")

    model_config = ConfigDict(
        json_schema_extra={
            "llm_constraint": "MUST extract the primary canonical name. If multiple languages exist, prefer Japanese, then English."
        }
    )


class UniversalMediaSchema(BaseModel):
    """Trunk Node: Canonical representation of a single release (data/media_detail/)."""
    id: str = Field(..., description="The exact ID format of the site (e.g., ABC-123). Do not strip hyphens.")
    title: str = Field(..., description="Full title of the release")
    date: Optional[str] = Field(None, description="Formatted as YYYY-MM-DD or null. DO NOT hallucinate today's date if missing.")
    cover: Optional[str] = Field(None, description="URL to the primary cover image")
    performers: List[Performer] = Field(default_factory=list, description="List of recognized performers")
    magnets: List[Magnet] = Field(default_factory=list, description="List of physical file releases")

    model_config = ConfigDict(
        json_schema_extra={
            "llm_constraint": "The central hub. Relies on accurate merging of search + detail data."
        }
    )


class UniversalActorSchema(BaseModel):
    """Trunk Node: Canonical JSON representing an actor's aliases and profile (data/actress/)."""
    id: str = Field(..., description="Canonical internal Actor ID")
    name: str = Field(..., description="Primary actor name")
    aliases: List[str] = Field(default_factory=list, description="Flattened list of string aliases. DO NOT include brackets or nested objects. Remove titles.")
    profile_image: Optional[str] = Field(None, description="URL to the actor's avatar/profile image")

    model_config = ConfigDict(
        json_schema_extra={
            "llm_constraint": "MUST be a flattened list of strings for aliases. DO NOT include brackets or nested objects."
        }
    )
