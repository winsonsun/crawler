import requests
from bs4 import BeautifulSoup
import json

headers = {"Cookie": "existmag=all; age=verified"}
html = requests.get("https://www.javbus.com/MKMP-713", headers=headers).text
soup = BeautifulSoup(html, "lxml")

detail = {}
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
    
    genres = []
    for span in info_block.select("span.genre a[href*='/genre/']"):
        genres.append(span.text.strip())
    if genres:
        detail["genres"] = genres
        
    performers = []
    seen = set()
    for a in info_block.select("a[href*='/star/']"):
        p_name = a.text.strip()
        p_url = a.get('href', '')
        if p_name and p_url and p_url not in seen:
            if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
            performers.append({"name": p_name, "url": p_url})
            seen.add(p_url)
    detail["performers"] = performers
    
print(json.dumps(detail, indent=2, ensure_ascii=False))
