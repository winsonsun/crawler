import re

with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# 1. Update _extract_and_save_actor_info to use a subdirectory
new_extract_method = """    def _add_to_actor_media_list(self, actor_name: str, scene_id: str, title: str):
        media_list_file = Path("actress") / actor_name / "media_list.json"
        media_list_file.parent.mkdir(parents=True, exist_ok=True)
        media_data = []
        if media_list_file.exists():
            try:
                import json
                with open(media_list_file, 'r', encoding='utf-8') as f:
                    media_data = json.load(f)
            except Exception:
                pass
        if not any(item.get("id") == scene_id for item in media_data):
            media_data.append({"id": scene_id, "title": title})
            try:
                import json
                with open(media_list_file, 'w', encoding='utf-8') as f:
                    json.dump(media_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to update {media_list_file}: {e}")

    async def _extract_and_save_actor_info(self, star_url: str, actor_name: str, web_crawler: AsyncWebCrawler):
        actor_dir = Path("actress") / actor_name
        actor_dir.mkdir(parents=True, exist_ok=True)
        actor_file = actor_dir / f"{actor_name}.json"
        if not self.config.force and actor_file.exists():
            return
            
        print(f"Extracting profile for {actor_name} from {star_url}")
        soup = await self._fetch_soup_safe(star_url, web_crawler)
        info = {"name": actor_name, "url": star_url}
        
        avatar = soup.select_one(".photo-frame img")
        if avatar:
            src = avatar.get("src", "")
            if src and not src.startswith("http"):
                src = "https://www.javbus.com" + src
            info["avatar"] = src
            if avatar.get("title"):
                info["name"] = avatar.get("title", "").strip()
                
        for p in soup.select(".photo-info p"):
            p_text = p.text.strip()
            if ":" in p_text:
                k, v = p_text.split(":", 1)
                info[k.strip()] = v.strip()
        
        try:
            import json
            with open(actor_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            print(f"Saved profile for {actor_name} to {actor_file}")
        except Exception as e:
            print(f"Failed to save profile for {actor_name}: {e}")"""

text = re.sub(
    r"    async def _extract_and_save_actor_info.*?print\(f\"Failed to save profile for \{actor_name\}: \{e\}\"\)",
    new_extract_method,
    text,
    flags=re.DOTALL
)

# 2. Update _scan_star_pages to traverse all pages and add to media_list
new_scan_pages = """    async def _scan_star_pages(self, star_url: str, actor_name: str, web_crawler: AsyncWebCrawler):
        print(f"\\n--- Scanning full list for actor: {actor_name} ---")
        page = 1
        while True:
            page_url = f"{star_url}/{page}" if page > 1 else star_url
            print(f"Scanning {actor_name} page {page}: {page_url}")
            
            star_soup = await self._fetch_soup_safe(page_url, web_crawler)
            boxes = star_soup.select('.movie-box')
            if not boxes:
                print(f"No more media found on page {page} for {actor_name}.")
                break
                
            for box in boxes:
                date_tags = box.select('date')
                scene_id = date_tags[0].text.strip() if date_tags else ""
                span_tag = box.select_one('.photo-info span')
                title = span_tag.text.strip() if span_tag else ""
                if title: title = title.split('\\n')[0].strip()
                media_url = box.get('href', '')
                if media_url and not media_url.startswith('http'):
                    media_url = "https://www.javbus.com" + media_url
                    
                if not scene_id or not media_url: continue
                
                print(f"[{actor_name}] Found '{scene_id}': {title}")
                self._add_to_actor_media_list(actor_name, scene_id, title)
                await self._process_discovered_media(scene_id, title, media_url, web_crawler)
                
            page += 1
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
            await asyncio.sleep(delay)"""

text = re.sub(
    r"    async def _scan_star_pages.*?await asyncio\.sleep\(delay\)",
    new_scan_pages,
    text,
    flags=re.DOTALL
)

# 3. Also inject self._add_to_actor_media_list in run_discovery for matched_actor
discovery_match_old = """                if matched_actor:
                    if not match_prefix:
                        print(f"Matched (actor: {matched_actor}) '{scene_id}': {title}")
                        await self._process_discovered_media(scene_id, title, page_url, web_crawler)"""

discovery_match_new = """                if matched_actor:
                    if not match_prefix:
                        print(f"Matched (actor: {matched_actor}) '{scene_id}': {title}")
                        self._add_to_actor_media_list(matched_actor, scene_id, title)
                        await self._process_discovered_media(scene_id, title, page_url, web_crawler)"""

text = text.replace(discovery_match_old, discovery_match_new)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
