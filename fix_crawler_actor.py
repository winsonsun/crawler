import re
with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

actor_extraction_method = """    async def _extract_and_save_actor_info(self, star_url: str, actor_name: str, web_crawler: AsyncWebCrawler):
        actor_file = Path(self.config.active_scan_file).parent / f"{actor_name}.json"
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
            text = p.text.strip()
            if ":" in text:
                k, v = text.split(":", 1)
                info[k.strip()] = v.strip()
        
        actor_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            import json
            with open(actor_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            print(f"Saved profile for {actor_name} to {actor_file}")
        except Exception as e:
            print(f"Failed to save profile for {actor_name}: {e}")

    async def _scan_star_pages"""

# Replace `    async def _scan_star_pages` with the new method + original method signature
text = text.replace("    async def _scan_star_pages", actor_extraction_method)

# Inject into run_discovery:
# find: print(f"Updated active_scan JSON with URL for {matched_actor}: {star_url}")
inject_discovery = """                                print(f"Updated active_scan JSON with URL for {matched_actor}: {star_url}")
                                await self._extract_and_save_actor_info(star_url, matched_actor, web_crawler)"""
text = text.replace('print(f"Updated active_scan JSON with URL for {matched_actor}: {star_url}")', inject_discovery)

# Inject into run_collection_scan:
inject_scan = """        for actor_name, star_url in active_scan_data.items():
            if not star_url:
                continue
            await self._extract_and_save_actor_info(star_url, actor_name, web_crawler)
            await self._scan_star_pages(star_url, actor_name, web_crawler)"""
text = re.sub(
    r"        for actor_name, star_url in active_scan_data\.items\(\):\n            if not star_url:\n                continue\n            await self\._scan_star_pages\(star_url, actor_name, web_crawler\)",
    inject_scan,
    text
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
