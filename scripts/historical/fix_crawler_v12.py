with open("src/crawler/crawler.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("    async def _fetch_javbus_magnets(self, html: str, page_url: str):"):
        skip = True
        new_lines.append(line)
        new_lines.append('        import re as local_re\n')
        new_lines.append('        gid_m = local_re.search(r"gid\\s*=\\s*([0-9]+)", html)\n')
        new_lines.append('        uc_m = local_re.search(r"uc\\s*=\\s*([0-9]+)", html)\n')
        new_lines.append('        img_m = local_re.search(r"img\\s*=\\s*\\\'([^\\\']+)\\\'", html)\n')
        new_lines.append('        if not (gid_m and uc_m and img_m): return []\n')
        new_lines.append('        gid, uc, img = gid_m.group(1), uc_m.group(1), img_m.group(1)\n')
        new_lines.append('        headers = self._get_http_headers()\n')
        new_lines.append('        headers["Referer"] = page_url\n')
        new_lines.append('        headers["X-Requested-With"] = "XMLHttpRequest"\n')
        new_lines.append('        ajax_url = f"https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid={gid}&lang=zh&img={img}&uc={uc}"\n')
        new_lines.append('        async with aiohttp.ClientSession(headers=headers) as session:\n')
        new_lines.append('            try:\n')
        new_lines.append('                async with session.get(ajax_url, timeout=10) as resp:\n')
        new_lines.append('                    if resp.status == 200:\n')
        new_lines.append('                        ajax_html = await resp.text()\n')
        new_lines.append('                        if not ajax_html.strip(): return []\n')
        new_lines.append('                        from bs4 import BeautifulSoup\n')
        new_lines.append('                        soup = BeautifulSoup(ajax_html, "lxml")\n')
        new_lines.append('                        magnets = []\n')
        new_lines.append('                        for tr in soup.select("tr"):\n')
        new_lines.append('                            tds = tr.select("td")\n')
        new_lines.append('                            if len(tds) >= 3:\n')
        new_lines.append('                                a_tags = tds[0].select("a")\n')
        new_lines.append('                                if not a_tags: continue\n')
        new_lines.append('                                uri = a_tags[0].get("href", "")\n')
        new_lines.append('                                if not uri.startswith("magnet"): continue\n')
        new_lines.append('                                name = " ".join(tds[0].text.strip().split())\n')
        new_lines.append('                                size = tds[1].text.strip()\n')
        new_lines.append('                                date = tds[2].text.strip()\n')
        new_lines.append('                                magnets.append({"name": name, "uri": uri, "total_size": size, "date": date})\n')
        new_lines.append('                        return magnets\n')
        new_lines.append('            except Exception as e: pass\n')
        new_lines.append('        return []\n')
        continue
    
    if skip:
        if line.startswith("    async def run_parse("):
            skip = False
            new_lines.append(line)
        continue
    
    new_lines.append(line.replace("@to-be-download.txt", "to-be-downloaded.txt"))

with open("src/crawler/crawler.py", "w") as f:
    f.writelines(new_lines)
