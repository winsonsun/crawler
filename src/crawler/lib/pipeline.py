import asyncio
import os
import json
from typing import List, Dict, Optional, Any, Tuple
from ..adapters.base import BaseSiteAdapter, SearchResult, MediaDetail
from ..adapters.virtual import VirtualAdapter
from ..adapters.knowledge import WikipediaAdapter
from .omni_solver import GeminiOmniSolver, SolverAction
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

class AutonomousOrchestrator:
    """The 'Brain' that manages the unified agentic pipeline."""
    
    def __init__(self, crawler_instance):
        self.crawler = crawler_instance
        self.solver = GeminiOmniSolver()
        self.adapters: Dict[str, BaseSiteAdapter] = {}
        self.enrichers = [WikipediaAdapter()]

    def get_adapter(self, site_key: str) -> BaseSiteAdapter:
        if site_key in self.adapters:
            return self.adapters[site_key]
        
        # In a real scenario, we'd load site-specific subclasses (e.g. JavBusAdapter)
        # For this prototype, we use VirtualAdapter for everything.
        from ..crawler import SITES_CONFIG
        config = SITES_CONFIG.get(site_key, {})
        config["site_key"] = site_key
        adapter = VirtualAdapter(config)
        self.adapters[site_key] = adapter
        return adapter

    async def execute_task(self, scene_name: str, web_crawler: AsyncWebCrawler) -> Optional[MediaDetail]:
        """Unified business procedure: Search -> Extract -> Validate -> Repair."""
        site_key = self.crawler.config.site
        adapter = self.get_adapter(site_key)
        
        # 1. Search Stage
        search_url = adapter.get_search_url(scene_name)
        result = await web_crawler.arun(url=search_url, config=self.crawler.crawl_config, js_code=adapter.get_bypass_js())
        
        # 2. Validation (The 'Critic')
        has_results = await self._run_critic(result.markdown, "search")
        
        if not has_results:
            print(f"Critic detected failure for '{scene_name}' on {site_key}. Attempting repair...")
            # 3. Repair/Autonomous Solving
            b64_img = getattr(result, 'screenshot', None) or getattr(result, 'base64_screenshot', None)
            if b64_img:
                solution = self.solver.solve(b64_img, result.html or "")
                if solution.action == SolverAction.SEARCH:
                    # Execute OmniSolver search and retry extraction
                    pass
                elif solution.action == SolverAction.CLICK:
                    # Execute click and retry
                    pass
        
        # 4. Extraction Stage (Simplified for this example)
        search_results = await adapter.extract_search_results(result.html or "", result.markdown or "")
        target_result = next((r for r in search_results if r.id.upper() == scene_name.upper()), None)
        
        if target_result:
            # Move to Detail Extraction
            detail_res = await web_crawler.arun(url=target_result.page_url, config=self.crawler.crawl_config)
            detail = await adapter.extract_detail(detail_res.html or "", target_result.page_url)
            
            # 5. Detail Validation
            is_valid = await self._run_critic(detail.model_dump_json() if detail else "{}", "detail")
            if not is_valid:
                print(f"Detail validation failed for {scene_name}. Triggering LLM-Vision extraction fallback...")
                # Fallback to LLMExtractionStrategy here
            return detail
            
        return None

    async def _run_critic(self, content: str, stage: str) -> bool:
        """
        An LLM-powered step that evaluates if the extraction was successful.
        """
        if stage == "search":
            return any(line.strip().startswith('[') and "![]" in line for line in content.splitlines())
        elif stage == "detail":
            try:
                data = json.loads(content)
                return bool(data.get("id") and data.get("title"))
            except:
                return False
        return True

    async def enrich_performer(self, name: str, web_crawler: AsyncWebCrawler) -> Dict[str, Any]:
        """
        Iterates through all registered knowledge adapters to enrich performer info.
        """
        results = {}
        for enricher in self.enrichers:
            try:
                info = await enricher.enrich_performer(name, web_crawler)
                if info:
                    results.update(info)
            except Exception as e:
                print(f"Enrichment error with {enricher.__class__.__name__}: {e}")
        return results

    async def profile_site(self, target_url: str, web_crawler: AsyncWebCrawler):
        """
        Full autonomous onboarding of a new site.
        """
        from urllib.parse import urlparse
        parsed_url = urlparse(target_url)
        site_key = parsed_url.netloc.split('.')[-2]
        home_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        print(f"--- Profiling new site: {site_key} ({home_url}) ---")
        
        result = await web_crawler.arun(url=home_url, config=self.crawler.crawl_config)
        b64_img = getattr(result, 'screenshot', None) or getattr(result, 'base64_screenshot', None)
        solution = self.solver.solve(b64_img, result.html or "")
        
        if solution.action != SolverAction.SEARCH:
            print("Failed to find search interface on home page.")
            return

        print(f"Found search interface: {solution.search_input_selector}")
        
        test_query = "ABC-123"
        search_js = f"""
        (async () => {{
            const input = document.querySelector("{solution.search_input_selector}");
            input.value = "{test_query}";
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            const btn = document.querySelector("{solution.search_button_selector or 'button[type=submit]'}") || document.querySelector('input[type=submit]');
            if (btn) btn.click();
            else input.dispatchEvent(new KeyboardEvent('keydown', {{'key': 'Enter'}}));
        }})();
        """
        list_page_res = await web_crawler.arun(url=home_url, config=self.crawler.crawl_config, js_code=search_js)
        await asyncio.sleep(3)
        
        url_template = list_page_res.url.replace(test_query, "{scene_name}")
        print(f"Discovered URL template: {url_template}")
        
        b64_img_list = getattr(list_page_res, 'screenshot', None) or getattr(list_page_res, 'base64_screenshot', None)
        list_profile = self.solver.profile_page(b64_img_list, list_page_res.html or "", "search")
        
        adapter = VirtualAdapter({"selectors": {"search": list_profile.selectors.model_dump()}})
        search_results = await adapter.extract_search_results(list_page_res.html, list_page_res.markdown)
        
        if not search_results:
            print("Failed to extract search results for detail profiling.")
            return
            
        detail_url = search_results[0].page_url
        detail_page_res = await web_crawler.arun(url=detail_url, config=self.crawler.crawl_config)
        
        b64_img_detail = getattr(detail_page_res, 'screenshot', None) or getattr(detail_page_res, 'base64_screenshot', None)
        detail_profile = self.solver.profile_page(b64_img_detail, detail_page_res.html or "", "detail")
        
        new_config = {
            "home_url": home_url,
            "url_template": url_template,
            "selectors": {
                "search": list_profile.selectors.model_dump(exclude_none=True),
                "detail": detail_profile.selectors.model_dump(exclude_none=True)
            }
        }
        
        from ..crawler import CRAW_CONF, SITES_CONFIG
        sites_path = os.path.join(CRAW_CONF, "sites.json")
        try:
            with open(sites_path, 'r', encoding='utf-8') as f:
                all_sites = json.load(f)
            all_sites[site_key] = new_config
            with open(sites_path, 'w', encoding='utf-8') as f:
                json.dump(all_sites, f, indent=2, ensure_ascii=False)
            SITES_CONFIG[site_key] = new_config
            print(f"Successfully onboarded {site_key}")
        except Exception as e:
            print(f"Error persisting site profile: {e}")
