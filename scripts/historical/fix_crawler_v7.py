import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Update run_parse to be extremely aggressive with age-gate and wait
run_parse_fix = """
    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        # Aggressive JS extractor with polling and age-gate bypass
        js_extractor = '''
        return (async () => {
            const poll = (fn, timeout = 10000) => {
                const start = Date.now();
                return new Promise((resolve, reject) => {
                    const check = () => {
                        const res = fn();
                        if (res) resolve(res);
                        else if (Date.now() - start > timeout) resolve(null);
                        else setTimeout(check, 500);
                    };
                    check();
                });
            };

            const clickAgeGate = () => {
                const btn = Array.from(document.querySelectorAll('button, a')).find(b => b.innerText.includes('成年') || b.innerText.includes('確認'));
                if (btn) {
                    const check = document.querySelector('input[type="checkbox"]');
                    if (check) check.click();
                    btn.click();
                    return true;
                }
                return false;
            };

            if (clickAgeGate()) {
                await new Promise(r => setTimeout(r, 2000));
            }

            // Poll for real content
            await poll(() => document.querySelector('.bigImage, .container h3, #magnet-table'));

            const magnets = Array.from(document.querySelectorAll('#magnet-table tr')).map(tr => {
                const links = tr.querySelectorAll('a');
                if (links.length >= 3) {
                    return {
                        name: links[0].innerText.trim(),
                        uri: links[0].href,
                        total_size: links[1].innerText.trim(),
                        date: links[2].innerText.trim()
                    };
                }
                return null;
            }).filter(m => m !== null);

            const idNode = Array.from(document.querySelectorAll('.photo-info p')).find(p => p.innerText.includes('識別碼') || p.innerText.includes('ID'));
            
            return {
                id: idNode ? idNode.innerText.split(':').pop().strip() : document.title.split(' ')[0],
                title: document.querySelector('.container h3')?.innerText || document.title,
                cover_image: document.querySelector('.bigImage img')?.src,
                sample_images: Array.from(document.querySelectorAll('.sample-box img')).map(img => img.src),
                magnet_entries: magnets,
                cookie: document.cookie
            };
        })();
        '''
        
        result = await web_crawler.arun(
            url=url, 
            config=self.crawl_config, 
            headers=self._get_http_headers(), 
            js_code=js_extractor
        )
        
        js_out = getattr(result, 'js_execution_result', None) or {}
        results_arr = js_out.get('results', [])
        detail = results_arr[0] if results_arr and isinstance(results_arr[0], dict) else {}
        
        if detail and detail.get("cookie"):
            self.dynamic_cookie = detail.get("cookie")

        if not detail or not detail.get("id") or detail.get("id") == "JavBus" or "Age Verification" in detail.get("title", ""):
            # Last resort: if JS failed, maybe it's just the cookies. Update them and try soup.
            soup = await self._fetch_soup_safe(url, web_crawler)
            from bs4 import BeautifulSoup
            if not detail: detail = {}
            # Re-extract from soup manually here if needed
            header = soup.select_one(".container h3") or soup.select_one(".header h3")
            if header:
                detail["title"] = header.text.strip()
                for p in soup.select(".photo-info p"):
                    if "識別碼" in p.text or "ID" in p.text:
                        detail["id"] = p.text.split(":")[-1].strip()
                        break
                detail["cover_image"] = soup.select_one(".bigImage img")["src"] if soup.select_one(".bigImage img") else ""
                detail["sample_images"] = [img["src"] for img in soup.select(".sample-box img")]
                detail["magnet_entries"] = []
                for tr in soup.select("#magnet-table tr"):
                    links = tr.select("a")
                    if len(links) >= 3:
                        detail["magnet_entries"].append({
                            "name": links[0].text.strip(), "uri": links[0].get("href"),
                            "total_size": links[1].text.strip(), "date": links[2].text.strip()
                        })

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
