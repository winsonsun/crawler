# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Performer(BaseModel):
    name: str
    url: Optional[str] = None
    credited_as: Optional[str] = None
    primary_name: Optional[str] = None # For alias resolution

class MagnetEntry(BaseModel):
    uri: str
    name: Optional[str] = None
    size_gb: Optional[float] = None
    date: Optional[str] = None
    file_count: Optional[int] = None

class UniversalMediaDetail(BaseModel):
    id: str
    title: str
    clean_title: Optional[str] = None # Polished title without marketing junk
    release_date: Optional[str] = None 
    duration_minutes: Optional[int] = None
    cover_image: Optional[str] = None
    sample_images: List[str] = Field(default_factory=list)
    performers: List[Performer] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    studio: Optional[str] = None
    label: Optional[str] = None
    director: Optional[str] = None
    series: Optional[str] = None
    magnets: List[MagnetEntry] = Field(default_factory=list)
    page_url: Optional[str] = None
    site: str

class MediaFossil(BaseModel):
    """The 'Fossil Record' of the raw scrape to be stored separately."""
    id: str
    site: str
    scraped_at: str
    raw_data: Dict[str, Any]
