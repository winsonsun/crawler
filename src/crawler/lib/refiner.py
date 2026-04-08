# -*- coding: utf-8 -*-
import os
import json
import asyncio
import re
from typing import Optional
from .ontology import UniversalMediaDetail
import google.generativeai as genai

class MediaRefiner:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def refine(self, detail: UniversalMediaDetail) -> UniversalMediaDetail:
        """Uses LLM to polish and refine the media entity metadata."""
        if not self.model:
            print("Warning: No API key found for Refiner. Skipping LLM refinement.")
            detail.clean_title = detail.title
            return detail

        prompt = f"""
        Refine the following media metadata into a clean, professional entity record.
        
        Original Title: {detail.title}
        Performers: {', '.join([p.name for p in detail.performers])}
        Site: {detail.site}
        
        Tasks:
        1. Clean Title: Remove marketing junk (e.g., 'Hcup', '99cm', 'Exclusive', 'Debut', scene ID if repeated). 
           Keep only the actual semantic title of the work.
        2. Verify Performers: If the title mentions a name not in the performers list, add it.
        3. Identify Primary Name: If multiple names are present for an actor, identify the most common one.

        Respond ONLY in JSON format:
        {{
            "clean_title": "string",
            "performers": [
                {{"name": "string", "primary_name": "string"}}
            ]
        }}

        """

        try:
            # Set safety settings to allow processing of adult content metadata
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = await asyncio.to_thread(self.model.generate_content, prompt, safety_settings=safety_settings)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            
            refined_data = json.loads(text.strip())
            detail.clean_title = refined_data.get("clean_title", detail.title)
            
            refined_performers = refined_data.get("performers", [])
            performer_map = {p["name"]: p.get("primary_name") for p in refined_performers}
            
            for p in detail.performers:
                if p.name in performer_map:
                    p.primary_name = performer_map[p.name]
            
            return detail
        except Exception as e:
            print(f"LLM Refinement failed: {e}. Using regex fallback.")
            # Regex Fallback for cleaning title
            clean = detail.title
            # Remove common marketing junk
            junk = [r'99cm', r'Hcup', r'超美', r'巨乳', r'女子', r'プロレスラー', r'男禁制', r'鮮烈', r'デビュー', r'撮影中', r'処女', r'判明', r'ロストヴァージン', r'性感', r'開発', r'自主トレ', r'初激イキ', r'爆乳', r'初パイズリクラッチ', r'リングで孕ませ', r'初中出し7連発', r'刃流花']
            for pattern in junk:
                clean = re.sub(pattern, '', clean)
            
            # Remove redundant ID if it starts the title
            clean = re.sub(rf'^{re.escape(detail.id)}\s*', '', clean)
            detail.clean_title = clean.strip()
            return detail

async def refine_detail_async(detail: UniversalMediaDetail) -> UniversalMediaDetail:
    refiner = MediaRefiner()
    return await refiner.refine(detail)
