from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    id: str
    title: str = ""
    page_url: str
    cover_image: Optional[str] = None
    release_date: Optional[str] = None
    performers: List[str] = Field(default_factory=list)

class MediaDetail(BaseModel):
    id: str
    title: str
    page_url: str
    cover_image: Optional[str] = None
    release_date: Optional[str] = None
    performers: List[Dict[str, str]] = Field(default_factory=list) # [{'name': '...', 'url': '...'}]
    magnets: List[Dict[str, Any]] = Field(default_factory=list)
    samples: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseSiteAdapter:
    """Unified interface for site-specific crawling logic."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.site_key = config.get("site_key")
        self.home_url = config.get("home_url")
        self.url_template = config.get("url_template")

    def get_search_url(self, query: str) -> str:
        if self.url_template:
            from urllib.parse import quote_plus
            return self.url_template.format(scene_name=quote_plus(query))
        return self.home_url

    def get_bypass_js(self) -> str:
        """Standard age-gate/anti-bot bypass JS."""
        return """
        (() => {
            const ageCheck = document.querySelector('input[type="checkbox"]');
            if (ageCheck) ageCheck.click();
            const buttons = Array.from(document.querySelectorAll('button, a'));
            const submitBtn = buttons.find(b => b.innerText.includes('成年') || b.innerText.includes('18歳以上') || b.innerText.includes('確認'));
            if (submitBtn) submitBtn.click();
            return { cookie: document.cookie, userAgent: navigator.userAgent };
        })();
        """

    async def extract_search_results(self, html: str, markdown: str) -> List[SearchResult]:
        raise NotImplementedError

    async def extract_detail(self, html: str, url: str) -> Optional[MediaDetail]:
        raise NotImplementedError
