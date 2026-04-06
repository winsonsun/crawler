import urllib.request
import json
import os
import re
from bs4 import BeautifulSoup
from pathlib import Path

cookie = "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1"
ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

items = [
    {"id": "SORA-631", "page_url": "https://www.javbus.com/SORA-631"},
    {"id": "GVH-832", "page_url": "https://www.javbus.com/GVH-832"},
    {"id": "JUFE-618", "page_url": "https://www.javbus.com/JUFE-618"},
    {"id": "MIRD-282", "page_url": "https://www.javbus.com/MIRD-282"},
    {"id": "MIMK-273", "page_url": "https://www.javbus.com/MIMK-273"},
    {"id": "MIDA-574", "page_url": "https://www.javbus.com/MIDA-574"},
    {"id": "MIDA-576", "page_url": "https://www.javbus.com/MIDA-576"},
    {"id": "MIDA-578", "page_url": "https://www.javbus.com/MIDA-578"},
    {"id": "MIDA-581", "page_url": "https://www.javbus.com/MIDA-581"},
    {"id": "MIDA-586", "page_url": "https://www.javbus.com/MIDA-586"},
    {"id": "ADN-721", "page_url": "https://www.javbus.com/ADN-721"},
    {"id": "ADN-771", "page_url": "https://www.javbus.com/ADN-771"},
    {"id": "ADN-773", "page_url": "https://www.javbus.com/ADN-773"},
    {"id": "LULU-431", "page_url": "https://www.javbus.com/LULU-431"},
    {"id": "WAAA-636", "page_url": "https://www.javbus.com/WAAA-636"},
    {"id": "WAAA-635", "page_url": "https://www.javbus.com/WAAA-635"},
    {"id": "CAWD-940", "page_url": "https://www.javbus.com/CAWD-940"}
]

def parse_size_gb(s):
    s = s.upper().strip()
    try:
        if 'GB' in s: return float(s.replace('GB', '').strip())
        if 'MB' in s: return float(s.replace('MB', '').strip()) / 1024.0
        if 'KB' in s: return float(s.replace('KB', '').strip()) / 1048576.0
    except:
        pass
    return 0.0

for item in items:
    scene_id = item['id']
    url = item['page_url']
    print(f"Processing {scene_id}...")
    
    req = urllib.request.Request(url, headers={'Cookie': cookie, 'User-Agent': ua, 'Referer': 'https://www.javbus.com/'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        continue
        
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.select_one('h3')
    if not header: continue
    title = header.text.strip()
    
    # get variables for ajax
    gid_m = re.search(r"var gid = (\d+);", html)
    uc_m = re.search(r"var uc = (\d+);", html)
    img_m = re.search(r"var img = '([^']+)';", html)
    
    magnets = []
    if gid_m and uc_m and img_m:
        gid, uc, img = gid_m.group(1), uc_m.group(1), img_m.group(1)
        ajax_url = f"https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid={gid}&lang=zh&img={img}&uc={uc}&floor=456"
        
        ajax_req = urllib.request.Request(ajax_url, headers={'Cookie': cookie, 'User-Agent': ua, 'Referer': url})
        try:
            ajax_html = urllib.request.urlopen(ajax_req, timeout=10).read().decode('utf-8')
            ajax_soup = BeautifulSoup(ajax_html, 'html.parser')
            for tr in ajax_soup.select('tr'):
                links = tr.select('a')
                if len(links) >= 3:
                    magnets.append({
                        'name': links[0].text.strip(),
                        'uri': links[0]['href'],
                        'total_size': links[1].text.strip(),
                        'date': links[2].text.strip()
                    })
        except Exception as e:
            print("Ajax failed:", e)

    # Load existing JSON if possible to retain sample images we already downloaded
    json_path = f"media_detail/{scene_id}/{scene_id}.json"
    data = {}
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
    data['id'] = scene_id
    data['title'] = title
    data['magnet_entries'] = magnets
    data['page_url'] = url
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    for mag in magnets:
        gb = parse_size_gb(mag['total_size'])
        if gb > 1.2:
            with open('to-be-downloaded.txt', 'a', encoding='utf-8') as mf:
                mf.write(mag['uri'] + '\n')
            print(f" Saved magnet (>1.2GB): {gb:.2f}GB")
