from typing import List, Dict, Optional, Any
from .base import BaseSiteAdapter, SearchResult, MediaDetail
from lxml import html as lxml_html
import re

class VirtualAdapter(BaseSiteAdapter):
    """
    A generic adapter that uses CSS selectors from configuration.
    If selectors are missing, it relies on LLM-based extraction.
    """
    
    async def extract_search_results(self, html: str, markdown: str) -> List[SearchResult]:
        selectors = self.config.get("selectors", {}).get("search", {})
        if not selectors:
            return [] # Rely on LLM fallback in the pipeline
            
        tree = lxml_html.fromstring(html)
        results = []
        
        container_selector = selectors.get("container", ".movie-box")
        containers = tree.cssselect(container_selector)
        
        for container in containers:
            try:
                # Basic CSS-based extraction
                id_el = container.cssselect(selectors.get("id", "date"))
                id_val = id_el[0].text_content().strip() if id_el else ""
                
                title_el = container.cssselect(selectors.get("title", "img"))
                title_val = title_el[0].get("title") or title_el[0].get("alt") if title_el else ""
                
                url_el = container.cssselect(selectors.get("url", "a"))
                url_val = url_el[0].get("href") if url_el else ""
                if url_val and not url_val.startswith("http"):
                    from urllib.parse import urljoin
                    url_val = urljoin(self.home_url, url_val)
                
                if id_val and url_val:
                    results.append(SearchResult(id=id_val, title=title_val, page_url=url_val))
            except Exception:
                continue
        return results

    async def extract_detail(self, html_content: str, url: str) -> Optional[MediaDetail]:
        selectors = self.config.get("selectors", {}).get("detail", {})
        if not selectors:
            return None
            
        tree = lxml_html.fromstring(html_content)
        
        try:
            # Example of how VirtualAdapter can be configured to pull multiple fields
            id_val = tree.cssselect(selectors.get("id", "span:contains('識別碼') + span"))
            title_val = tree.cssselect(selectors.get("title", "h3"))
            
            # This is where the 'Critic' and 'Repair' logic will eventually feed back
            # if these static selectors return None.
            
            detail = MediaDetail(
                id=id_val[0].text_content().strip() if id_val else "",
                title=title_val[0].text_content().strip() if title_val else "",
                page_url=url
            )
            return detail
        except Exception:
            return None
