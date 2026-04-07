import asyncio
import os
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
try:
    from crawl4ai.models import LLMConfig # Adjust import based on crawl4ai version
except ImportError:
    pass
from pydantic import BaseModel, Field

class ActressProfile(BaseModel):
    name: str = Field(description="Name of the actress")
    birthday: str = Field(description="Birthday in YYYY-MM-DD format", default="")
    age: str = Field(description="Age as an integer string", default="")
    height: str = Field(description="Height in cm", default="")
    birthplace: str = Field(description="Place of birth", default="")
    hobbies: str = Field(description="Hobbies or special skills", default="")
    bust: str = Field(description="Bust size in cm", default="")
    waist: str = Field(description="Waist size in cm", default="")
    hip: str = Field(description="Hip size in cm", default="")

async def main():
    # Load .env manually for this test
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip('"\'')
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No API key")
        return

    instruction = "Extract the actress profile information from the Wikipedia page. Only use metric measurements (cm) for height and sizes, ignoring any imperial (inches) tables."
    from crawl4ai import LLMConfig
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider="gemini/gemini-2.5-flash", api_token=api_key),
        instruction=instruction,
        schema=ActressProfile.model_json_schema(),
        extraction_type="schema",
        force_json_response=True
    )

    url = "https://ja.wikipedia.org/wiki/%E8%91%89%E5%B1%B1%E3%81%95%E3%82%86%E3%82%8A"
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun(url=url, config=config)
        print(result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
