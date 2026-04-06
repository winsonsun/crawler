import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Update run_parse to use _fetch_soup_safe and a robust BS4 parser
run_parse_fix = """
    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        soup = await self._fetch_soup_safe(url, web_crawler)
        
        detail = {}
        if self.config.site == "javbus":
            header = soup.select_one(".header")
            if header:
                detail["id"] = header.text.split(" ")[0].strip()
                detail["title"] = soup.title.text.strip() if soup.title else ""
                cover_img = soup.select_one(".bigImage img")
                if cover_img:
                    detail["cover_image"] = cover_img["src"]
                    if not detail["cover_image"].startswith("http"):
                        detail["cover_image"] = "https://www.javbus.com" + detail["cover_image"]
                
                detail["sample_images"] = []
                for img in soup.select(".sample-box img"):
                    src = img.get("src")
                    if src:
                        if not src.startswith("http"): src = "https://www.javbus.com" + src
                        detail["sample_images"].append(src)
                
                detail["magnet_entries"] = []
                for tr in soup.select("#magnet-table tr"):
                    links = tr.select("a")
                    if len(links) >= 3:
                        detail["magnet_entries"].append({
                            "name": links[0].text.strip(),
                            "uri": links[0].get("href"),
                            "total_size": links[1].text.strip(),
                            "date": links[2].text.strip()
                        })
        
        if not detail or not detail.get("id"):
            # Try javdb fallback
            try:
                from .sites.javdb import page_parser
                # Use result.markdown? No, soup.text or result.markdown.
                # Let's just use the soup.
                detail = page_parser.parse_from_text(soup.get_text(), id_hint=scene_name)
            except: pass

        if detail:
            # Final sanity check on ID
            if not detail.get("id") or detail.get("id") == "JavBus":
                detail["id"] = scene_name
            
            media_dir = self.media_dir / detail["id"]
            media_dir.mkdir(parents=True, exist_ok=True)
            detail_file = media_dir / f"{detail['id']}.json"
            
            with open(detail_file, 'w', encoding='utf-8') as fh:
                json.dump(detail, fh, ensure_ascii=False, indent=2)
            print(f"Wrote {detail_file}")
            
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
