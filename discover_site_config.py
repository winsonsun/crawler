
import asyncio
import os
import base64
import json
from src.crawler.crawler import CrawlerConfig, AsyncWebCrawler, Crawler, SITES_CONFIG
from src.crawler.lib.omni_solver import GeminiOmniSolver, SolverAction, CaptchaSolution
from crawl4ai import *
from typing import Optional

async def discover_search_pattern(site_key: str):
    config = CrawlerConfig(site=site_key, verbose=True)
    home_url = SITES_CONFIG.get(site_key, {}).get('home_url')
    if not home_url:
        print(f"Error: No home_url for {site_key}")
        return

    print(f"--- Discovering search pattern for {site_key} starting from {home_url} ---")
    
    async with AsyncWebCrawler() as web_crawler:
        session_id = f"discovery_{site_key}"
        crawl_config = CrawlerRunConfig(
            screenshot=True,
            wait_for_images=True,
            process_iframes=True,
            session_id=session_id
        )
        
        # 1. Go to home page with bypass
        js_bypass = """
        (() => {
            const checkbox = document.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
            
            const submitBtn = document.querySelector('input#submit') || document.querySelector('input[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.click();
            }
        })();
        """
        result = await web_crawler.arun(url=home_url, config=crawl_config, js_code=js_bypass)
        await asyncio.sleep(3) # Wait for navigation after bypass
        
        # Refresh state after bypass
        result = await web_crawler.arun(url=result.url, config=crawl_config)
        
        solver = GeminiOmniSolver()
        
        max_steps = 5
        current_step = 0
        
        while current_step < max_steps:
            current_step += 1
            print(f"Step {current_step}: analyzing {result.url}")
            
            b64_img = getattr(result, 'screenshot', None) or getattr(result, 'base64_screenshot', None)
            if not b64_img:
                print("No screenshot available")
                break
                
            # Customize prompt for search discovery
            prompt = (
                "You are an interface expert. Examine the screenshot and HTML. "
                "1. Is there an anti-bot or age gate? (click/wait) "
                "2. If no anti-bot, find the main search input field. "
                "Return action='search', search_input_selector, and search_button_selector. "
                "3. If you see a search result page, return action='solved'. "
                "Include reasoning."
            )
            
            # Using the existing solve but with a more targeted prompt internally if needed.
            # For now, let's just use the updated solve() we just modified.
            solution = solver.solve(b64_img, result.html or "")
            print(f"OmniSolver Action: {solution.action}")
            print(f"OmniSolver Reasoning: {solution.reasoning}")
            
            if solution.action == SolverAction.CLICK:
                print(f"Clicking {solution.target_text or solution.target_selector}")
                js_click = f"""
                (() => {{
                    const selector = "{solution.target_selector or ""}";
                    const text = "{solution.target_text or ""}";
                    let btn;
                    if (selector) btn = document.querySelector(selector);
                    if (!btn && text) {{
                        const elements = Array.from(document.querySelectorAll('button, a, span, div, img, input[type="button"], input[type="submit"]'));
                        btn = elements.find(el => (el.innerText && el.innerText.includes(text)) || (el.alt && el.alt.includes(text)) || (el.value && el.value.includes(text)));
                    }}
                    if (btn) btn.click();
                }})();
                """
                result = await web_crawler.arun(url=result.url, config=crawl_config, js_code=js_click)
                await asyncio.sleep(2)
                
            elif solution.action == SolverAction.SEARCH:
                print(f"Search input detected: {solution.search_input_selector}")
                # Try to perform a test search to discover the URL pattern
                test_query = "ABC-123"
                search_js = f"""
                (async () => {{
                    const input = document.querySelector("{solution.search_input_selector}");
                    if (input) {{
                        input.value = "{test_query}";
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        const btnSelector = "{solution.search_button_selector or ""}";
                        let btn = btnSelector ? document.querySelector(btnSelector) : null;
                        if (!btn) btn = document.querySelector('button[type="submit"]') || document.querySelector('input[type="submit"]');
                        if (btn) btn.click();
                        else input.dispatchEvent(new KeyboardEvent('keydown', {{'key': 'Enter'}}));
                    }}
                }})();
                """
                result = await web_crawler.arun(url=result.url, config=crawl_config, js_code=search_js)
                await asyncio.sleep(3)
                
                final_url = result.url
                print(f"Search result URL: {final_url}")
                
                # Infer pattern
                if test_query in final_url:
                    pattern = final_url.replace(test_query, "{scene_name}")
                    print(f"Inferred URL Pattern: {pattern}")
                    return pattern
                else:
                    # Maybe it's a POST or weird JS search
                    print("Could not infer URL pattern from final URL.")
                    return None
                    
            elif solution.action == SolverAction.SOLVED:
                print("Target page or search already visible.")
                break
            else:
                print("Unhandled action or failed.")
                break
                
    return None

async def update_sites_json(site_key, new_pattern):
    sites_path = os.path.join(os.environ.get("CRAW_CONF", "./config"), "sites.json")
    with open(sites_path, 'r') as f:
        data = json.load(f)
    
    if site_key in data:
        old_pattern = data[site_key].get("url_template")
        if old_pattern != new_pattern:
            print(f"Updating {site_key} url_template: {old_pattern} -> {new_pattern}")
            data[site_key]["url_template"] = new_pattern
            with open(sites_path, 'w') as f:
                json.dump(data, f, indent=2)
            print("sites.json updated successfully.")
        else:
            print("No change needed.")

if __name__ == "__main__":
    import sys
    site = sys.argv[1] if len(sys.argv) > 1 else "javbus"
    pattern = asyncio.run(discover_search_pattern(site))
    if pattern:
        asyncio.run(update_sites_json(site, pattern))
