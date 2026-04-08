# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup

async def extract_javbus_detail(soup: BeautifulSoup, scene_name: str, page_url: str, crawler_instance) -> dict:
    """Extracts media details from a JavBus page soup."""
    detail = {}
    title_node = soup.select_one(".container h3") or soup.select_one(".header h3")
    detail["title"] = title_node.text.strip() if title_node else ""
    
    info_block = soup.select_one(".col-md-3.info") or soup.select_one(".info")
    if info_block:
        for p in info_block.select("p"):
            text = p.get_text(separator=' ', strip=True)
            if "識別碼:" in text or "ID:" in text:
                detail["id"] = text.split(":")[-1].strip()
            elif "發行日期:" in text:
                detail["release_date"] = text.split(":")[-1].strip()
            elif "長度:" in text:
                detail["length"] = text.split(":")[-1].strip()
            elif "導演:" in text:
                detail["director"] = text.split(":")[-1].strip()
            elif "製作商:" in text:
                detail["studio"] = text.split(":")[-1].strip()
            elif "發行商:" in text:
                detail["label"] = text.split(":")[-1].strip()
        
        genres = [span.text.strip() for span in info_block.select("span.genre a[href*='/genre/']")]
        if genres:
            detail["genres"] = genres
            
        detail["performers"] = []
        seen = set()
        for a in info_block.select("a[href*='/star/']"):
            p_name = a.text.strip()
            p_url = a.get('href', '')
            if p_name and p_url and p_url not in seen:
                if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
                primary_name, credited_as = crawler_instance._resolve_actor_name(p_name)
                p_data = {"name": primary_name, "url": p_url}
                if credited_as: p_data["credited_as"] = credited_as
                detail["performers"].append(p_data)
                seen.add(p_url)
    else:
        # Fallback extraction
        id_p = next((p for p in soup.select("p") if "識別碼" in p.text or "ID" in p.text), None)
        if id_p and ":" in id_p.text:
            detail["id"] = id_p.text.split(":")[-1].strip()

    if not detail.get("id"): detail["id"] = scene_name
    
    cover_img = soup.select_one(".bigImage img")
    if cover_img:
        src = cover_img["src"]
        if not src.startswith("http"): src = "https://www.javbus.com" + src
        detail["cover_image"] = src
    
    detail["sample_images"] = []
    for img in soup.select(".sample-box img"):
        src = img.get("src")
        if src:
            if not src.startswith("http"): src = "https://www.javbus.com" + src
            detail["sample_images"].append(src)

    detail["magnet_entries"] = await crawler_instance._fetch_javbus_magnets(str(soup), page_url)
    return detail
