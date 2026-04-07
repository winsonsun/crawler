# -*- coding: utf-8 -*-
import os
import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from pathlib import Path
import urllib.parse

# Mapping Wikipedia fields to JSON keys
FIELD_MAPPING = {
    "生年月日": "生日",
    "現年齢": "年齡",
    "身長": "身高",
    "出身地": "出生地",
    "趣味": "愛好",
    "特技": "愛好"
}

def fetch_wikipedia_info(name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    }
    
    def try_fetch(n):
        quoted = urllib.parse.quote(n)
        url = f"https://ja.wikipedia.org/wiki/{quoted}"
        try:
            time.sleep(random.uniform(0.5, 1.5))
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.text
            return None
        except:
            return None

    # Try name, then (AV女優), then (女優)
    html = try_fetch(name)
    if not html:
        html = try_fetch(f"{name} (AV女優)")
    if not html:
        html = try_fetch(f"{name} (女優)")
    
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    infobox = soup.select_one(".infobox") or soup.select_one(".vcard")
    if not infobox:
        return None
    
    info = {}
    
    # Get the main rows of the infobox
    # Sometimes they are direct children of infobox, sometimes inside a tbody
    rows = []
    tbody = infobox.find("tbody", recursive=False)
    if tbody:
        rows = tbody.find_all("tr", recursive=False)
    else:
        rows = infobox.find_all("tr", recursive=False)

    for tr in rows:
        # Skip rows that contain nested infoboxes (like imperial units)
        if tr.find("table", class_="infobox"):
            continue
            
        th = tr.find("th", recursive=False)
        td = tr.find("td", recursive=False)
        
        if not th or not td:
            # Some infoboxes use multiple th/td in one row, but standard is th + td
            continue

        key = th.get_text(strip=True)
        # Handle cases where value might be complex (links, spans, etc)
        # Use a copy of td to remove some elements if needed (like references)
        val_td = td
        for ref in val_td.select("sup.reference"):
            ref.decompose()
        
        val = val_td.get_text(" ", strip=True)
        
        if key in FIELD_MAPPING:
            json_key = FIELD_MAPPING[key]
            if json_key == "生日":
                match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', val)
                if match:
                    val = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
            elif json_key == "年齡":
                match = re.search(r'(\d+)', val)
                if match:
                    val = match.group(1)
            elif json_key == "身高":
                match = re.search(r'(\d+)\s*cm', val, re.I)
                if match:
                    val = f"{match.group(1)}cm"
                else:
                    # Try just digits if it says something like "170"
                    match = re.search(r'^(\d+)$', val)
                    if match:
                        val = f"{match.group(1)}cm"
            elif json_key == "愛好":
                if "愛好" in info:
                    info["愛好"] = f"{info['愛好']}/{val}"
                    continue
            
            info[json_key] = val
        
        elif "スリーサイズ" in key:
            # Try to match metric first (usually has cm or large numbers)
            match = re.search(r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)', val)
            if match:
                b, w, h = int(match.group(1)), int(match.group(2)), int(match.group(3))
                # Heuristic: metric sizes are typically > 50
                if b > 50:
                    info["胸圍"] = f"{b}cm"
                    info["腰圍"] = f"{w}cm"
                    info["臀圍"] = f"{h}cm"
    
    return info

def process_actress(actress_dir):
    name = actress_dir.name
    json_file = actress_dir / f"{name}.json"
    
    if not json_file.exists():
        return

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return

    # Check if needs backfill
    needs_backfill = False
    if len(data.keys()) < 10 or "生日" not in data:
        needs_backfill = True
    else:
        # Even if it looks complete, check if sizes are suspiciously small (likely inches)
        for k in ["胸圍", "腰圍", "臀圍"]:
            val = data.get(k, "")
            match = re.search(r'(\d+)', str(val))
            if match and int(match.group(1)) < 50:
                needs_backfill = True
                break
    
    if not needs_backfill:
        return

    print(f"Backfilling {name}...")
    
    names_to_try = [name]
    if "（" in name and "）" in name:
        match = re.search(r'(.+?)（(.+?)）', name)
        if match:
            names_to_try.extend([match.group(1), match.group(2)])
    elif "(" in name and ")" in name:
        match = re.search(r'(.+?)\((.+?)\)', name)
        if match:
            names_to_try.extend([match.group(1), match.group(2)])

    wiki_info = None
    for n in names_to_try:
        wiki_info = fetch_wikipedia_info(n)
        if wiki_info:
            break
    
    if wiki_info:
        # Define fields we want to allow overwriting from Wikipedia for better accuracy
        profile_fields = ["生日", "年齡", "身高", "出生地", "胸圍", "腰圍", "臀圍", "愛好"]
        
        for k, v in wiki_info.items():
            if v:
                if k in profile_fields:
                    # Allow overwrite if current data is missing or looks like imperial units (e.g., 36cm instead of 90cm)
                    # Heuristic: if it's less than 50 and it's a size, it might be inches
                    is_small_size = False
                    if k in ["胸圍", "腰圍", "臀圍"]:
                        match = re.search(r'(\d+)', str(data.get(k, "")))
                        if match and int(match.group(1)) < 50:
                            is_small_size = True
                    
                    if k not in data or not data[k] or is_small_size:
                        data[k] = v
                elif k not in data or not data[k]:
                    data[k] = v
        
        # Ensure name is first
        ordered_data = {"name": name}
        ordered_data.update({k: v for k, v in data.items() if k != "name"})
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ordered_data, f, ensure_ascii=False, indent=2)
        print(f"  Successfully updated {name}.json")
    else:
        print(f"  No Wikipedia info found for {name}")

def main():
    actress_base_dir = Path("data/actress")
    dirs = [d for d in actress_base_dir.iterdir() if d.is_dir()]
    for d in dirs:
        process_actress(d)

if __name__ == "__main__":
    main()
