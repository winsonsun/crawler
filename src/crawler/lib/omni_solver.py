import os
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class SolverAction(str, Enum):
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    SOLVED = "solved"
    FAILED = "failed"
    SEARCH = "search"

class CaptchaSolution(BaseModel):
    action: SolverAction = Field(description="The action to take: 'click', 'type', 'wait', 'solved', 'failed', or 'search' (if a search input is detected)")
    target_selector: Optional[str] = Field(description="A CSS selector to interact with, if available", default=None)
    target_text: Optional[str] = Field(description="The exact text of the button or element to click", default=None)
    reasoning: Optional[str] = Field(description="Brief explanation of why this action was chosen", default=None)
    search_input_selector: Optional[str] = Field(description="CSS selector for the search input field", default=None)
    search_button_selector: Optional[str] = Field(description="CSS selector for the search submit button", default=None)

class PageSelectors(BaseModel):
    container: Optional[str] = Field(description="CSS selector for the repeating item container (for search lists)", default=None)
    id: Optional[str] = Field(description="CSS selector for the unique ID/code", default=None)
    title: Optional[str] = Field(description="CSS selector for the item title", default=None)
    url: Optional[str] = Field(description="CSS selector for the link to the detail page", default=None)
    release_date: Optional[str] = Field(description="CSS selector for the release date", default=None)
    performers: Optional[str] = Field(description="CSS selector for the list of performers", default=None)
    cover_image: Optional[str] = Field(description="CSS selector for the main cover image", default=None)
    samples: Optional[str] = Field(description="CSS selector for sample images/gallery", default=None)

class SiteProfile(BaseModel):
    page_type: str = Field(description="'search' or 'detail'")
    selectors: PageSelectors
    reasoning: str

class BaseOmniSolver:
    """Generic abstraction for an Omni LLM Solver."""
    def solve(self, screenshot_base64: str, html_context: str = "") -> CaptchaSolution:
        """
        Takes a base64 encoded screenshot and optional HTML context.
        Returns a CaptchaSolution containing instructions on how to bypass it.
        """
        raise NotImplementedError("Subclasses must implement solve()")

    def solve_from_html(self, html_context: str) -> CaptchaSolution:
        """
        Takes only HTML context.
        Returns a CaptchaSolution.
        """
        raise NotImplementedError("Subclasses must implement solve_from_html()")

    def profile_page(self, screenshot_base64: str, html_context: str, page_type: str) -> SiteProfile:
        """
        Analyzes a page to discover its structural CSS selectors.
        """
        raise NotImplementedError("Subclasses must implement profile_page()")

class GeminiOmniSolver(BaseOmniSolver):
    """Implementation of OmniSolver using Google's google-genai SDK."""
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
            
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def solve_from_html(self, html_context: str) -> CaptchaSolution:
        """
        Attempts to determine the next action using only the HTML context.
        This is faster and cheaper than vision-based solving.
        """
        from google import genai
        prompt = (
            "You are an expert at navigating web interfaces. Examine the provided HTML context of a web page. "
            "Your task is to determine the best next step to take: "
            "1. If there is a checkbox or button for age verification or anti-bot (e.g., '18+', 'Confirm', 'I am human'), return action='click' and provide the 'target_text' and 'target_selector'. "
            "2. If you see a prominent search input field, return action='search' and provide 'search_input_selector' and 'search_button_selector'. "
            "3. If the page is already at its target (movie listings or details), return action='solved'. "
            "4. If you cannot be certain without a screenshot, return action='failed'. "
            "Return the solution matching the provided JSON schema."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                f"Page context snippet: {html_context[:5000]}"
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CaptchaSolution,
                temperature=0.1
            ),
        )
        return CaptchaSolution.model_validate_json(response.text)

    def solve(self, screenshot_base64: str, html_context: str = "") -> CaptchaSolution:
        from google import genai
        
        # Prepare the image part
        image_bytes = base64.b64decode(screenshot_base64)
        
        prompt = (
            "You are an expert at solving complex anti-bot mechanisms, knowledge-based CAPTCHAs, and navigating web interfaces. "
            "Your persona is 'The Logical Auditor' who can solve any visual or text-based challenge. "
            "Examine the provided screenshot and HTML context of a web page. "
            "Your task is to determine the best next step to take: "
            "1. If it is an automatic verification with NO interactive elements (e.g., just 'Verifying you are human' text with no checkbox), return action='wait'. "
            "2. If you see a Cloudflare Turnstile checkbox (often looks like a small box with 'Verify you are human'), or any other checkbox/button (e.g. 'I am 18', 'Confirm', 'Enter'), return action='click'. "
            "   For Cloudflare Turnstile, provide target_text='Verify you are human' or a relevant selector if you can deduce it. "
            "   Choose the LOGICALLY CORRECT answer if a multiple choice question is asked. "
            "3. If you see a prominent search input field on a landing page, return action='search' and provide 'search_input_selector' and 'search_button_selector'. "
            "4. If the page is already at its target (e.g. shows movie lists, movie details, or is clearly the home page), return action='solved'. "
            "5. Otherwise, return action='failed'. "
            "Include your reasoning, specifically explaining why you chose a particular target. "
            "Return the solution matching the provided JSON schema."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                f"Page context snippet: {html_context[:1000]}"
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CaptchaSolution,
                temperature=0.1
            ),
        )
        
        return CaptchaSolution.model_validate_json(response.text)

    def profile_page(self, screenshot_base64: str, html_context: str, page_type: str) -> SiteProfile:
        from google import genai
        image_bytes = base64.b64decode(screenshot_base64)
        
        if page_type == "search":
            task_desc = (
                "This is a search result page. Identify the CSS selectors for the repeating item containers, "
                "and for each item's ID (code), Title, and Detail Link URL."
            )
        else:
            task_desc = (
                "This is a detail page. Identify the CSS selectors for the item's ID (code), Title, "
                "Release Date, Performers (list of name+link), Main Cover Image, and Sample Gallery Images."
            )

        prompt = (
            "You are an expert web scraper and frontend engineer. "
            "Examine the screenshot and HTML context. Your goal is to map the visual elements "
            "to stable CSS selectors (preferring IDs, semantic classes, or text-based nth-child/contains if necessary). "
            f"{task_desc} "
            "Return the selectors matching the provided JSON schema. Include your reasoning for choosing these selectors."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                f"HTML Snippet: {html_context[:10000]}" # More context for structural mapping
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SiteProfile,
                temperature=0.1
            ),
        )
        return SiteProfile.model_validate_json(response.text)
