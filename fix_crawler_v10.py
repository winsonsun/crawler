import re
import json

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Update _fetch_javbus_magnets to Crawler class (More robust)
magnets_fetcher = r"""
    async def _fetch_javbus_magnets(self, html: str, page_url: str):
        gid_m = re.search(r"gid\s*=\s*([0-9]+)", html)
        uc_m = re.search(r"uc\s*=\s*([0-9]+)", html)
        img_m = re.search(r"img\s*=\s*'([^']+)'", html)
        
        if not (gid_m and uc_m and img_m):
            print("Failed to find javbus variables in HTML")
            return []
            
        gid = gid_m.group(1)
        uc = uc_m.group(1)
        img = img_m.group(1)
        
        # Try both censored and uncensored AJAX endpoints
        endpoints = [
            "https://www.javbus.com/ajax/uncensored-torrent.php",
            "https://www.javbus.com/ajax/torrent.php"
        ]
        
        headers = self._get_http_headers()
        headers["Referer"] = page_url
        headers["X-Requested-With"] = "XMLHttpRequest"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            for endpoint in endpoints:
                ajax_url = f"{endpoint}?gid={gid}&lang=zh&img={img}&uc={uc}"
                try:
                    async with session.get(ajax_url, timeout=10) as resp:
                        if resp.status == 200:
                            ajax_html = await resp.text()
                            if not ajax_html.strip(): continue
                            from bs4 import BeautifulSoup
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
                            if magnets: return magnets
                except Exception as e:
                    print(f"Failed to fetch javbus magnets from {endpoint}: {e}")
        return []
"""

# Find the function and replace it
import re as py_re
pattern = py_re.compile(r"    async def _fetch_javbus_magnets\(self, html: str, page_url: str\):.*?\n\s+return \[\]", py_re.DOTALL)
if pattern.search(content):
    content = pattern.sub(magnets_fetcher, content)
else:
    content = content.replace("    async def run_parse", magnets_fetcher + "\n    async def run_parse")

# Also fix _check_and_save_magnets to append to to-be-downloaded.txt? 
# No, user wants @to-be-download.txt
content = content.replace("to-be-downloaded.txt", "@to-be-download.txt")

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
