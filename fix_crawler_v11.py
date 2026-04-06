import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

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
        
        endpoints = [
            "https://www.javbus.com/ajax/uncledatoolsbyajax.php"
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
                                tds = tr.select("td")
                                if len(tds) >= 3:
                                    a_tags = tds[0].select("a")
                                    if not a_tags: continue
                                    uri = a_tags[0].get("href", "")
                                    if not uri.startswith("magnet"): continue
                                    name = " ".join(tds[0].text.strip().split())
                                    size = tds[1].text.strip()
                                    date = tds[2].text.strip()
                                    magnets.append({
                                        "name": name,
                                        "uri": uri,
                                        "total_size": size,
                                        "date": date
                                    })
                            if magnets: return magnets
                except Exception as e:
                    print(f"Failed to fetch javbus magnets from {endpoint}: {e}")
        return []
"""

pattern = re.compile(r"    async def _fetch_javbus_magnets\(self, html: str, page_url: str\):.*?\n\s+return \[\]\n", re.DOTALL)
if pattern.search(content):
    content = pattern.sub(magnets_fetcher + "\n", content)
else:
    # Try alternate pattern
    pattern2 = re.compile(r"    async def _fetch_javbus_magnets.*?return \[\]", re.DOTALL)
    content = pattern2.sub(magnets_fetcher.strip(), content)

content = content.replace("@to-be-download.txt", "to-be-downloaded.txt")

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
