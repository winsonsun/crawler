# -*- coding: utf-8 -*-
import re
from typing import Dict, Any, Optional
from .ontology import UniversalMediaDetail, Performer, MagnetEntry

def parse_size_to_gb(size_str: Optional[str]) -> Optional[float]:
    """Converts size strings like '989MB', '1.3GB' into float GB."""
    if not size_str: return None
    match = re.search(r'([0-9.]+)\s*(GB|MB|KB|B)', size_str, re.I)
    if not match: return None
    
    val = float(match.group(1))
    unit = match.group(2).upper()
    
    if unit == "MB": return round(val / 1024, 3)
    if unit == "KB": return round(val / (1024 * 1024), 3)
    if unit == "B": return round(val / (1024**3), 6)
    return round(val, 3) # Already GB

def normalize_detail(raw_data: Dict[str, Any], site: str) -> UniversalMediaDetail:
    """Converts site-specific raw dicts into a UniversalMediaDetail."""
    
    # 1. Base mapping
    data = {
        "id": raw_data.get("id", ""),
        "title": raw_data.get("title", ""),
        "cover_image": raw_data.get("cover_image"),
        "page_url": raw_data.get("page_url"),
        "site": site
    }

    # 2. Site-Specific Normalization
    if site == "javdb":
        data["release_date"] = raw_data.get("released_date")
        data["duration_minutes"] = raw_data.get("duration_minutes")
        data["studio"] = raw_data.get("maker", {}).get("name") if isinstance(raw_data.get("maker"), dict) else None
        data["label"] = raw_data.get("publisher", {}).get("name") if isinstance(raw_data.get("publisher"), dict) else None
        
        # Unify Performers
        data["performers"] = [
            Performer(name=p["name"], url=p.get("url")) 
            for p in raw_data.get("actors", [])
        ]
        
        # Unify Tags
        data["tags"] = [t["name"] for t in raw_data.get("tags", []) if isinstance(t, dict)]
        
        # Unify Magnets (Canonical Size)
        data["magnets"] = []
        for m in raw_data.get("magnet_entries", []):
            m_data = m.copy()
            # Calculate canonical GB and remove raw string
            raw_size = m_data.pop("total_size", None)
            m_data["size_gb"] = parse_size_to_gb(raw_size)
            data["magnets"].append(MagnetEntry(**m_data))
        
    elif site == "javbus":
        data["release_date"] = raw_data.get("release_date")
        duration = raw_data.get("length", "")
        match = re.search(r'(\d+)', str(duration))
        data["duration_minutes"] = int(match.group(1)) if match else None
        
        data["studio"] = raw_data.get("studio")
        data["label"] = raw_data.get("label")
        data["director"] = raw_data.get("director")
        
        # Unify Performers
        data["performers"] = [
            Performer(name=p["name"], url=p.get("url"), credited_as=p.get("credited_as"))
            for p in raw_data.get("performers", [])
        ]
        
        data["tags"] = raw_data.get("genres", [])
        data["sample_images"] = raw_data.get("sample_images", [])
        
        # Unify Magnets (Canonical Size)
        data["magnets"] = []
        for m in raw_data.get("magnet_entries", []):
            m_data = m.copy()
            raw_size = m_data.pop("total_size", None)
            m_data["size_gb"] = parse_size_to_gb(raw_size)
            data["magnets"].append(MagnetEntry(**m_data))

    # 3. Clean up Title (Remove trailing performer name if redundant)
    if data["performers"] and data["title"]:
        first_performer = data["performers"][0].name
        if data["title"].endswith(first_performer):
            data["title"] = data["title"][:-(len(first_performer))].strip()

    return UniversalMediaDetail(**data)
