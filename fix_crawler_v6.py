import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Update run_parse to use crawl4ai with a robust JS extractor that handles age gate AND magnets
run_parse_fix = """
    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        # This JS will handle age gate, wait for magnets, and extract everything
        js_extractor = '''
        return (async () => {
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

            // Wait for magnets if it is javbus
            let attempts = 0;
            while (!document.querySelector('#magnet-table tr') && attempts < 20) {
                await new Promise(r => setTimeout(r, 500));
                attempts++;
            }

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
                id: idNode ? idNode.innerText.split(':').pop().trim() : document.title.split(' ')[0],
                title: document.querySelector('.container h3')?.innerText || document.title,
                cover_image: document.querySelector('.bigImage img')?.src,
                sample_images: Array.from(document.querySelectorAll('.sample-box img')).map(img => img.src),
                magnet_entries: magnets
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
        
        if not detail or not detail.get("id") or detail.get("id") == "JavBus":
            # Fallback to BeautifulSoup if JS failed
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.html or "", "lxml")
            if not detail: detail = {}
            detail["id"] = scene_name
            detail["title"] = soup.title.text if soup.title else scene_name
        
        if detail:
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
