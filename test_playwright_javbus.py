
import asyncio
from playwright.async_api import async_playwright

async def test_javbus():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Navigating to javbus...")
        await page.goto("https://www.javbus.com")
        
        # Check if age gate exists
        if await page.locator("input#submit").is_visible():
            print("Age gate detected, bypassing...")
            await page.check("input[type='checkbox']")
            await page.click("input#submit")
            await page.wait_for_load_state("networkidle")
            print(f"Landed on: {page.url}")
        
        # Now try to find search
        search_input = page.locator("input#search-input")
        if await search_input.is_visible():
            print("Search input found!")
            await search_input.fill("ABC-123")
            await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle")
            print(f"Search result URL: {page.url}")
        else:
            print("Search input NOT found via ID, searching broader...")
            # Try finding any visible search input
            all_inputs = await page.locator("input").all()
            for inp in all_inputs:
                placeholder = await inp.get_attribute("placeholder") or ""
                if "search" in placeholder.lower() or "搜尋" in placeholder:
                    print(f"Found search input via placeholder: {placeholder}")
                    await inp.fill("ABC-123")
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle")
                    print(f"Search result URL: {page.url}")
                    break
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_javbus())
