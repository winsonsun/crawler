import asyncio
import os
import sys
import base64
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawler.lib.omni_solver import GeminiOmniSolver, SolverAction

async def diagnostic():
    config = CrawlerConfig(site="javbus")
    c = Crawler(config)
    
    browser_conf = BrowserConfig(
        headless=True,
        user_data_dir=os.path.join(os.getcwd(), "config", "browser_profile_diag"),
        use_managed_browser=True,
        extra_args=["--no-sandbox"]
    )
    
    run_conf = CrawlerRunConfig(
        screenshot=True,
        magic=True
    )

    async with AsyncWebCrawler(config=browser_conf) as w:
        url = "https://www.javbus.com"
        print(f"Step 1: Fetching {url}...")
        result = await w.arun(url=url, config=run_conf)
        
        def save_ss(res, name):
            b64 = getattr(res, 'screenshot', None) or getattr(res, 'base64_screenshot', None)
            if b64:
                with open(f"diag_{name}.jpg", "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"Saved screenshot: diag_{name}.jpg")

        save_ss(result, "initial")
        
        solver = GeminiOmniSolver()
        
        # Action 1: Check if age gate is present
        solution = solver.solve(getattr(result, 'screenshot', ""), result.html or "")
        print(f"Omni Diagnostic 1: Action={solution.action}, Reasoning={solution.reasoning}")
        
        if solution.action == SolverAction.CLICK:
            print(f"Step 2: Performing click: {solution.target_selector or solution.target_text}")
            
            # Use a more realistic click script that handles the sequence
            js_click = f"""
            return (async () => {{
                const delay = (ms) => new Promise(r => setTimeout(r, ms));
                const checkbox = document.querySelector('input[type="checkbox"]');
                if (checkbox && !checkbox.checked) {{
                    console.log("Checking box...");
                    checkbox.click();
                    await delay(1000);
                }}
                
                const btns = Array.from(document.querySelectorAll('button, a'));
                const btn = btns.find(b => b.innerText.includes('確認') || b.innerText.includes('成年'));
                if (btn) {{
                    console.log("Clicking confirm...");
                    btn.click();
                    await delay(3000);
                }}
                return {{ cookie: document.cookie, title: document.title, html: document.body.innerHTML }};
            }})();
            """
            
            result = await w.arun(url=url, config=run_conf, js_code=js_click)
            save_ss(result, "after_click")
            
            # Check if we are still at the gate
            html = result.html or ""
            if "你是否已經成年" in html or "確認" in html:
                print("FAILED: Age gate still present after sequence.")
                # Look deeper into the cookie state
                js_res = getattr(result, 'js_execution_result', None) or {}
                print(f"Cookie state: {js_res.get('cookie', 'None')}")
            else:
                print("SUCCESS: Gate cleared.")

if __name__ == "__main__":
    asyncio.run(diagnostic())
