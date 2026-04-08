import os
import re
import asyncio
import json
import requests
from urllib.parse import quote_plus
from typing import Optional, List, Dict, Any
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMExtractionStrategy

class BaseKnowledgeAdapter:
    """Interface for global knowledge sources (Wikipedia, Google, etc.)"""
    async def enrich_performer(self, name: str, web_crawler: AsyncWebCrawler) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class WikipediaAdapter(BaseKnowledgeAdapter):
    """Enriches actor information using Wikipedia and LLM-based extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    async def enrich_performer(self, name: str, web_crawler: AsyncWebCrawler) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            print("GEMINI_API_KEY not found, skipping Wikipedia enrichment.")
            return None

        print(f"WikipediaAdapter: Enriching profile for {name}...")
        
        valid_url = await self._find_valid_url(name)
        if not valid_url:
            print(f"WikipediaAdapter: No valid Wikipedia page found for {name}.")
            return None

        # We import ActressProfileSchema here to avoid circular dependencies
        from ..crawler import ActressProfileSchema
        
        instruction = (
            "Extract the actress profile information from the Wikipedia page. "
            "Only use metric measurements (cm) for height and sizes, ignoring any imperial (inches) tables. "
            "Capture any additional relevant biographical details (like debut date, social media handles, or career highlights) "
            "into the 'metadata' dictionary field."
        )

        try:
            from crawl4ai import LLMConfig
            strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(provider="gemini/gemini-2.5-flash", api_token=self.api_key),
                instruction=instruction,
                schema=ActressProfileSchema.model_json_schema(),
                extraction_type="schema",
                force_json_response=True
            )
            config = CrawlerRunConfig(extraction_strategy=strategy)
            result = await web_crawler.arun(url=valid_url, config=config)
            
            if result.extracted_content:
                data = json.loads(result.extracted_content)
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                elif isinstance(data, dict):
                    return data
            return None
        except Exception as e:
            print(f"WikipediaAdapter extraction failed: {e}")
            return None

    async def _find_valid_url(self, actor_name: str) -> Optional[str]:
        names_to_try = [actor_name, f"{actor_name} (AV女優)", f"{actor_name} (女優)"]
        if "（" in actor_name and "）" in actor_name:
            match = re.search(r'(.+?)（(.+?)）', actor_name)
            if match:
                names_to_try.extend([match.group(1), match.group(2)])
        elif "(" in actor_name and ")" in actor_name:
            match = re.search(r'(.+?)\((.+?)\)', actor_name)
            if match:
                names_to_try.extend([match.group(1), match.group(2)])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }

        def check_urls():
            for name in names_to_try:
                url = f"https://ja.wikipedia.org/wiki/{quote_plus(name)}"
                try:
                    resp = requests.head(url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        return url
                    elif resp.status_code == 405:
                        resp = requests.get(url, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            return url
                except Exception:
                    pass
            return None

        return await asyncio.to_thread(check_urls)
