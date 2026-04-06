import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def test():
    with open('sites.json', 'r') as f:
        cfg = json.load(f)
    js = cfg['javbus']['detail_js_extractor']
    
    browser_conf = BrowserConfig(headless=True, extra_args=['--no-sandbox'])
    run_conf = CrawlerRunConfig(magic=True, js_code=js)
    
    async with AsyncWebCrawler(config=browser_conf) as c:
        res = await c.arun('https://www.javbus.com/SORA-631', config=run_conf, headers={'Cookie': 'PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1'})
        print("JS Result:", getattr(res, 'js_execution_result', 'NONE'))

asyncio.run(test())
