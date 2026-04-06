import re
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Add _fetch_javbus_magnets to Crawler class
magnets_fetcher = """
    async def _fetch_javbus_magnets(self, html: str, page_url: str):
        gid_m = re.search(r"var gid = ([0-9]+);", html)
        uc_m = re.search(r"var uc = ([0-9]+);", html)
        img_m = re.search(r"var img = '([^']+)';", html)
        
        if not (gid_m and uc_m and img_m):
            return []
            
        gid = gid_m.group(1)
        uc = uc_m.group(1)
        img = img_m.group(1)
        
        ajax_url = f"https://www.javbus.com/ajax/uncensored-torrent.php?gid={gid}&lang=zh&img={img}&uc={uc}"
        headers = self._get_http_headers()
        headers["Referer"] = page_url
        headers["X-Requested-With"] = "XMLHttpRequest"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(ajax_url, timeout=10) as resp:
                    if resp.status == 200:
                        ajax_html = await resp.text()
                        soup = BeautifulSoup(ajax_html, "lxml")
                        magnets = []
                        for tr in soup.select("tr"):
                            links = tr.select("a")
                            if len(links) >= 3:
                                magnets.append({
                                    "name": links[0].text.strip(),
                                    "uri": links[0].get("href"),
                                    "total_size": links[1].text.strip(),
                                    "date": links[2].text.strip()
                                })
                        return magnets
            except Exception as e:
                print(f"Failed to fetch javbus magnets: {e}")
        return []
"""
if "_fetch_javbus_magnets" not in content:
    content = content.replace("    async def run_parse", magnets_fetcher + "\n    async def run_parse")

# 2. Update run_parse with direct magnet fetch and improved extraction
run_parse_fix = """
    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        soup = await self._fetch_soup_safe(url, web_crawler)
        html = str(soup)
        
        detail = {}
        if self.config.site == "javbus":
            title_node = soup.select_one(".container h3") or soup.select_one(".header h3")
            detail["title"] = title_node.text.strip() if title_node else ""
            
            for p in soup.select(".photo-info p"):
                if "識別碼" in p.text or "ID" in p.text:
                    if ":" in p.text:
                        detail["id"] = p.text.split(":")[-1].strip()
                        break
            
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
            
            detail["magnet_entries"] = await self._fetch_javbus_magnets(html, url)
        
        if not detail or not detail.get("id") or detail.get("id") == "JavBus":
            try:
                from .sites.javdb import page_parser
                detail = page_parser.parse_from_text(soup.get_text(), id_hint=scene_name)
            except: pass

        if detail:
            if not detail.get("id"): detail["id"] = scene_name
            media_dir = self.media_dir / detail["id"]
            media_dir.mkdir(parents=True, exist_ok=True)
            detail_file = media_dir / f"{detail['id']}.json"
            
            with open(detail_file, 'w', encoding='utf-8') as fh:
                json.dump(detail, fh, ensure_ascii=False, indent=2)
            print(f"Wrote {detail_file}")
            
            self._check_and_save_magnets(detail["id"])
            
            if self.config.merge_detail:
                try:
                    from .lib import merge_detail_into_search as merger
                    merger.merge_detail(detail_file, self.config.site, search_dir=str(self.search_dir))
                except: pass
"""
content = re.sub(
    r"\s+async def run_parse\(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler\):.*?(?=\s+async def run_download)",
    run_parse_fix,
    content,
    flags=re.DOTALL
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
