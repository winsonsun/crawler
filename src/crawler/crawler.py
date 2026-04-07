# -*- coding: utf-8 -*-

import time 
import asyncio
import aiohttp
try:
    from aiohttp_client_cache import CachedSession, SQLiteBackend
except ImportError:
    CachedSession = SQLiteBackend = None
import requests
import base64
import sys
import os
import datetime
import hashlib
from crawl4ai import *
from crawl4ai.extraction_strategy import LLMExtractionStrategy
try:
    from crawl4ai.models import LLMConfig
except ImportError:
    pass
from pydantic import BaseModel, Field

class ActressProfileSchema(BaseModel):
    name: str = Field(description="Name of the actress")
    birthday: str = Field(description="Birthday in YYYY-MM-DD format", default="")
    age: str = Field(description="Age as an integer string", default="")
    height: str = Field(description="Height in cm (e.g., '160cm')", default="")
    birthplace: str = Field(description="Place of birth", default="")
    hobbies: str = Field(description="Hobbies or special skills", default="")
    bust: str = Field(description="Bust size in cm (e.g., '90cm')", default="")
    waist: str = Field(description="Waist size in cm (e.g., '60cm')", default="")
    hip: str = Field(description="Hip size in cm (e.g., '88cm')", default="")


import re
import pprint
import json
import importlib
from urllib.parse import quote_plus
from typing import Callable, Dict, Tuple, List
import glob
import random

from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .lib.exceptions import SearchFailedError, PageParseError, DownloadHttpError, DownloadUrlError

CRAW_CONF = os.environ.get("CRAW_CONF", "./config")
CRAW_DATA = os.environ.get("CRAW_DATA", "./data")

# Load site configurations from config/sites.json
try:
    with open(os.path.join(CRAW_CONF, 'sites.json'), 'r') as f:
        SITES_CONFIG = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading {os.path.join(CRAW_CONF, 'sites.json')}: {e}", file=sys.stderr)
    SITES_CONFIG = {}

def load_parser(site_key: str) -> Callable:
    """Dynamically loads a parser function for a given site."""
    if site_key not in SITES_CONFIG:
        return None
    
    config = SITES_CONFIG[site_key]
    module_name = config.get("parser_module")
    function_name = config.get("parser_function")

    if not module_name or not function_name:
        return None

    try:
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    except (ImportError, AttributeError) as e:
        print(f"Error loading parser for site '{site_key}': {e}", file=sys.stderr)
        return None

def build_url(site_key: str, scene_name: str = None) -> str:
    """Builds a URL for the given site and scene using templates from sites.json."""
    if site_key not in SITES_CONFIG:
        raise ValueError(f"Site '{site_key}' not found in sites.json")

    config = SITES_CONFIG[site_key]
    if scene_name:
        return config["url_template"].format(scene_name=quote_plus(scene_name))
    return config["home_url"]

from dataclasses import dataclass, field

@dataclass
class CrawlerConfig:
    scenes: List[str] = field(default_factory=list)
    site: str = "javdb"
    merge_detail: bool = False
    download_image: bool = False
    run_search: bool = False
    run_parse: bool = False
    run_download: bool = False
    force: bool = False
    media_dir: str = os.path.join(CRAW_DATA, "media_detail")
    actress_dir: str = os.path.join(CRAW_DATA, "actress")
    search_dir: str = "search_site"
    logdir: str = "."
    retry_limit: int = 1
    min_delay: float = 10.0
    max_delay: float = 90.0
    user_data_dir: str = None
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    dry_run: bool = False
    verbose: bool = False
    discover: bool = False
    collection_scan: bool = False
    discover_start_page: int = 1
    discover_pages: int = 3
    discover_prefixes: List[str] = field(default_factory=list)
    ain_list_file: str = None
    active_scan_file: str = os.path.join(CRAW_CONF, "active_scan.json")
    magnet_output_file: str = os.path.join(CRAW_DATA, "output", "to-be-downloaded.txt")
    stash_url: str = "http://localhost:9999/graphql"
    sync_to_stash: str = ""
    sync_type: str = "performer"
    native_fetch: bool = False
    rebuild_host: str = "winsonsun@192.168.20.24"
    rebuild_path: str = "/mnt/cig/video/{category}"
    llm_enrich: bool = False

def parse_size_to_gb(size_str: str) -> float:
    if not size_str: return 0.0
    size_str = size_str.upper().strip()
    try:
        if 'GB' in size_str:
            return float(size_str.replace('GB', '').strip())
        elif 'MB' in size_str:
            return float(size_str.replace('MB', '').strip()) / 1024.0
        elif 'KB' in size_str:
            return float(size_str.replace('KB', '').strip()) / (1024.0 * 1024.0)
    except ValueError:
        return 0.0
    return 0.0

class Crawler:
    """Encapsulates parsing and web crawling logic."""

    def __init__(self, config: CrawlerConfig):
        self._stash_cache = {}
        # Load .env variables
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        try:
                            k, v = line.strip().split("=", 1)
                            os.environ[k] = v.strip('"\'')
                        except ValueError:
                            pass

        self.config = config
        self.cookie_domain = SITES_CONFIG.get(config.site, {}).get("cookie_domain")
        self.parser = load_parser(config.site)
        self.media_dir = Path(config.media_dir)
        self.actress_dir = Path(config.actress_dir)
        self.search_dir = Path(config.search_dir)
        self.logdir = Path(config.logdir)
        self.dynamic_cookie = "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1"
        self.dynamic_user_agent = self.config.user_agent
        self.session_id = f"session_{random.randint(1000, 9999)}"
        self.crawl_config = CrawlerRunConfig(
            session_id=self.session_id,
            magic=True,
            user_agent=self.dynamic_user_agent
        )
        self.search_lock = asyncio.Lock()
        
        # Load Global Aliases
        self.alias_map = {}
        alias_file = Path(os.environ.get("CRAW_CONF", "config")) / "actress_aliases.json"
        if alias_file.exists():
            try:
                with open(alias_file, 'r', encoding='utf-8') as f:
                    self.alias_map = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load alias map: {e}")

    def _inject_meta(self, data: dict) -> dict:
        import json
        data_copy = {k: v for k, v in data.items() if k != "_meta"}
        content_str = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.md5(content_str.encode('utf-8')).hexdigest()
        
        if "_meta" not in data:
            data["_meta"] = {}
            
        data["_meta"]["scraped_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data["_meta"]["hash"] = content_hash
        return data

    def _resolve_actor_name(self, name: str) -> Tuple[str, str]:
        """Resolves an actor name using the global alias map. Returns (primary_name, credited_as_or_None)."""
        primary = self.alias_map.get(name)
        if primary:
            return primary, name
        return name, None

    def _get_http_headers(self):
        """Constructs a standard set of HTTP headers for requests."""
        return {
            "User-Agent": self.dynamic_user_agent, 
            "Cookie": self.dynamic_cookie or "existmag=all; age=verified"
        }

    def _get_client_session(self, headers: dict):
        if CachedSession and self.config.ain_list_file:
            cache_name = os.path.join(os.environ.get("CRAW_DATA", "./data"), "http_cache")
            cache = SQLiteBackend(
                cache_name=cache_name,
                expire_after=86400, # 24 hours
                allowed_methods=('GET',),
                allowed_codes=(200, 301, 302)
            )
            return CachedSession(cache=cache, headers=headers)
        return aiohttp.ClientSession(headers=headers)

    async def _save_search_result(self, scene_name, data):
        self.search_dir.mkdir(exist_ok=True)
        filename = self.search_dir / f"{self.config.site}_search.json"
        
        async with self.search_lock:
            def sync_save():
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                existing_data[scene_name] = data
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
            await asyncio.to_thread(sync_save)
            print(f"Saved search result for '{scene_name}' to '{filename}'")

    def parse_line(self, line):
        if self.parser:
            try:
                m, data = self.parser(line)
                if m:
                    return m, data
            except Exception:
                pass
        
        from .sites.javdb.parser import parse_line_generic
        return parse_line_generic(line)

    def _is_complete(self, scene_name: str) -> bool:
        """Check if the output directory for a scene appears to be complete."""
        from .lib.download_samples import is_scene_complete
        
        detail_file = self.media_dir / scene_name / f"{scene_name}.json"
        
        if not self.config.download_image:
            return detail_file.is_file()
            
        return is_scene_complete(detail_file, media_dir=str(self.media_dir))

    async def run_search(self, scene_name: str, web_crawler: AsyncWebCrawler):
        headers = self._get_http_headers()
        url_to_fetch = build_url(self.config.site, scene_name)
        
        js_bypass = """
        return (() => {
            const ageCheck = document.querySelector('input[type="checkbox"]');
            if (ageCheck) ageCheck.click();
            
            const buttons = Array.from(document.querySelectorAll('button, a'));
            const submitBtn = buttons.find(b => b.innerText.includes('成年') || b.innerText.includes('18歳以上') || b.innerText.includes('確認'));
            if (submitBtn) submitBtn.click();
            
            return {
                cookie: document.cookie,
                userAgent: navigator.userAgent
            };
        })();
        """
        
        result1 = await web_crawler.arun(url=url_to_fetch, config=self.crawl_config, headers=headers, js_code=js_bypass)
        
        # Check if we landed directly on a detail page (common for IDs on javbus)
        current_url = result1.url.rstrip("/")
        if self.config.site == "javbus" and current_url.split("/")[-1].upper() == scene_name.upper():
            res = {"id": scene_name, "page_url": result1.url}
            await self._save_search_result(scene_name, res)
            return res

        lines_output = str(result1.markdown)

        js_out = getattr(result1, 'js_execution_result', None) or {}
        results_arr = js_out.get('results', [])
        if isinstance(results_arr, list) and results_arr:
            res = results_arr[0]
            if isinstance(res, dict):
                self.dynamic_cookie = res.get('cookie', self.dynamic_cookie)
                self.dynamic_user_agent = res.get('userAgent', self.dynamic_user_agent)

        if self.config.verbose:
            my_file = self.logdir / f"my_file_{scene_name}.txt"
            try:
                my_file.parent.mkdir(parents=True, exist_ok=True)
                my_file.write_text(lines_output)
            except Exception as e:
                print(f"Warning: could not write demo file: {e}", file=sys.stderr)

        for line in lines_output.splitlines():
            if line.strip().startswith('[') and "![]" in line:
                st, result = self.parse_line(line)
                if result and scene_name and result.get("id") == scene_name:
                    await self._save_search_result(scene_name, result)
                    return result
        raise SearchFailedError(f"Could not find a valid search result for '{scene_name}' in the page output.")

    async def _fetch_javbus_magnets(self, html: str, page_url: str):
        import re as local_re
        gid_m = local_re.search(r"gid\s*=\s*([0-9]+)", html)
        uc_m = local_re.search(r"uc\s*=\s*([0-9]+)", html)
        img_m = local_re.search(r"img\s*=\s*\'([^\']+)\'", html)
        if not (gid_m and uc_m and img_m): return []
        gid, uc, img = gid_m.group(1), uc_m.group(1), img_m.group(1)
        headers = self._get_http_headers()
        headers["Referer"] = page_url
        headers["X-Requested-With"] = "XMLHttpRequest"
        ajax_url = f"https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid={gid}&lang=zh&img={img}&uc={uc}"
        async with self._get_client_session(headers=headers) as session:
            try:
                async with session.get(ajax_url, timeout=10) as resp:
                    if resp.status == 200:
                        ajax_html = await resp.text()
                        if not ajax_html.strip(): return []
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(ajax_html, "lxml")
                        magnets = []
                        for tr in soup.select("tr"):
                            tds = tr.select("td")
                            if len(tds) >= 3:
                                a_tags = tds[0].select("a")
                                if not a_tags: continue
                                uri = a_tags[0].get("href", "")
                                if not uri.startswith("magnet"): continue
                                name = " ".join(tds[0].text.strip().split())
                                size = tds[1].text.strip()
                                date = tds[2].text.strip()
                                magnets.append({"name": name, "uri": uri, "total_size": size, "date": date})
                        return magnets
            except Exception as e: pass
        return []

    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        soup = await self._fetch_soup_safe(url, web_crawler)
        detail = {}
        
        if soup:
            # Manual extraction using BeautifulSoup (Fast Path)
            if self.config.site == "javbus":
                title_node = soup.select_one(".container h3") or soup.select_one(".header h3")
                detail["title"] = title_node.text.strip() if title_node else ""
                
                info_block = soup.select_one(".col-md-3.info") or soup.select_one(".info")
                if info_block:
                    for p in info_block.select("p"):
                        text = p.get_text(separator=' ', strip=True)
                        if "識別碼:" in text or "ID:" in text:
                            detail["id"] = text.split(":")[-1].strip()
                        elif "發行日期:" in text:
                            detail["release_date"] = text.split(":")[-1].strip()
                        elif "長度:" in text:
                            detail["length"] = text.split(":")[-1].strip()
                        elif "導演:" in text:
                            detail["director"] = text.split(":")[-1].strip()
                        elif "製作商:" in text:
                            detail["studio"] = text.split(":")[-1].strip()
                        elif "發行商:" in text:
                            detail["label"] = text.split(":")[-1].strip()
                    
                    genres = []
                    for span in info_block.select("span.genre a[href*='/genre/']"):
                        genres.append(span.text.strip())
                    if genres:
                        detail["genres"] = genres
                        
                    # HARVEST PERFORMERS
                    detail["performers"] = []
                    seen = set()
                    for a in info_block.select("a[href*='/star/']"):
                        p_name = a.text.strip()
                        p_url = a.get('href', '')
                        if p_name and p_url and p_url not in seen:
                            if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
                            
                            primary_name, credited_as = self._resolve_actor_name(p_name)
                            p_data = {"name": primary_name, "url": p_url}
                            if credited_as:
                                p_data["credited_as"] = credited_as
                                
                            detail["performers"].append(p_data)
                            seen.add(p_url)
                else:
                    for p in soup.select(".photo-info p") or soup.select("p"):
                        if "識別碼" in p.text or "ID" in p.text:
                            if ":" in p.text:
                                detail["id"] = p.text.split(":")[-1].strip()
                                break
                    # HARVEST PERFORMERS (Fallback)
                    detail["performers"] = []
                    for a in soup.select('a[href*="/star/"]'):
                        p_name = a.text.strip()
                        p_url = a.get('href', '')
                        if p_name and p_url:
                            if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
                            
                            primary_name, credited_as = self._resolve_actor_name(p_name)
                            p_data = {"name": primary_name, "url": p_url}
                            if credited_as:
                                p_data["credited_as"] = credited_as
                                
                            detail["performers"].append(p_data)
                
                if not detail.get("id"): detail["id"] = scene_name
                
                cover_img = soup.select_one(".bigImage img")
                if cover_img:
                    src = cover_img["src"]
                    if not src.startswith("http"): src = "https://www.javbus.com" + src
                    detail["cover_image"] = src
                
                detail["sample_images"] = []
                for img in soup.select(".sample-box img"):
                    src = img.get("src")
                    if src:
                        if not src.startswith("http"): src = "https://www.javbus.com" + src
                        detail["sample_images"].append(src)

                detail["magnet_entries"] = await self._fetch_javbus_magnets(str(soup), url)
        
        # Fallback to Javascript Extractor if soup failed or manual parse was incomplete
        if not detail or (self.config.site == "javbus" and not detail.get("magnet_entries")):
            extractor_js = SITES_CONFIG.get(self.config.site, {}).get("detail_js_extractor")
            if extractor_js:
                 result = await web_crawler.arun(url=url, config=self.crawl_config, headers=self._get_http_headers(), js_code=extractor_js)
                 js_out = getattr(result, 'js_execution_result', None) or {}
                 results_arr = js_out.get('results', [])
                 if isinstance(results_arr, list) and results_arr:
                     detail = results_arr[0]
                     if isinstance(detail, dict):
                         self.dynamic_cookie = detail.get('cookie', self.dynamic_cookie)
                         self.dynamic_user_agent = detail.get('userAgent', self.dynamic_user_agent)

        if not detail or not detail.get("id") or detail.get("id") == "JavBus":
            try:
                from .sites.javdb import page_parser
                if soup:
                    detail = page_parser.parse_from_text(soup.get_text(), id_hint=scene_name)
            except: pass

        if detail:
            if not detail.get("id"): detail["id"] = scene_name
            media_dir = self.media_dir / detail["id"]
            media_dir.mkdir(parents=True, exist_ok=True)
            detail_file = media_dir / f"{detail['id']}.json"
            
            detail = self._inject_meta(detail)
            
            with open(detail_file, 'w', encoding='utf-8') as fh:
                json.dump(detail, fh, ensure_ascii=False, indent=2)
            print(f"Wrote {detail_file}")
            
            if self.config.merge_detail:
                try:
                    from .lib import merge_detail_into_search as merger
                    merger.merge_detail(detail_file, self.config.site, search_dir=str(self.search_dir))
                except: pass
            return detail
        return None

    async def run_download(self, scene_name: str):
        detail_file = self.media_dir / scene_name / f"{scene_name}.json"
        if self.config.download_image:
            try:
                from .lib import download_samples as downloader
                
                headers = {
                    'Cookie': self.dynamic_cookie,
                    'User-Agent': self.dynamic_user_agent,
                    'Referer': SITES_CONFIG.get(self.config.site, {}).get("home_url", "") + "/"
                }
                
                res = await downloader.process_detail_file_async(detail_file, media_dir=str(self.media_dir), headers=headers)
                if res and isinstance(res, dict):
                    for dl in res.get('downloaded', []):
                        print(f"Downloaded image: {dl}")
                    for fl in res.get('failed', []):
                        print(f"Failed to download image: {fl}")
                    if not res.get('downloaded') and not res.get('failed') and res.get('skipped'):
                        print("Images already exist, skipping download.")
                return res
            except Exception as e:
                print(f"Download step failed: {e}")
                return None
        else:
            print("Download skipped (use --download-image to enable)")
            return None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((SearchFailedError, PageParseError, DownloadHttpError, DownloadUrlError))
    )
    async def _process_single_scene(self, scene: str, web_crawler: AsyncWebCrawler, run_search: bool, run_parse: bool, run_download: bool):
        """Wrapper function to process a single scene with retry logic."""
        search_result = {}
        if run_search:
            search_result = await self.run_search(scene, web_crawler)
        
        if run_parse:
            if not search_result: # If search was skipped, load the result
                try:
                    with open(self.search_dir / f"{self.config.site}_search.json", 'r') as f:
                        search_data = json.load(f)
                        search_result = search_data.get(scene)
                        if not search_result:
                            print(f"No search result found for '{scene}' in {self.search_dir}", file=sys.stderr)
                            return # Don't retry if search result is missing
                except (FileNotFoundError, json.JSONDecodeError):
                    print(f"Could not load search results for '{scene}'", file=sys.stderr)
                    return # Don't retry if search file is missing

            await self.run_parse(scene, search_result, web_crawler)
        
        if run_download:
            return await self.run_download(scene)

    async def _fetch_soup_safe(self, url: str, web_crawler: AsyncWebCrawler):
        from bs4 import BeautifulSoup
        
        # Fast path: Try lightweight aiohttp first
        async with self._get_client_session(headers=self._get_http_headers()) as session:
            try:
                async with session.get(url, timeout=10, allow_redirects=True) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        if "你是否已經成年" not in html and "確認" not in html and "18歳以上" not in html:
                            soup = BeautifulSoup(html, 'lxml')
                            if soup.select('.movie-box') or soup.select('.bigImage') or soup.select('.photo-info'):
                                return soup
            except Exception:
                pass

        # Slow path: Fallback to crawl4ai for age-gate bypass
        js_bypass = '''
        return (() => {
            const ageCheck = document.querySelector('input[type="checkbox"]');
            if (ageCheck) ageCheck.click();
            const btns = Array.from(document.querySelectorAll('button, a'));
            const btn = btns.find(b => 
                b.innerText.includes('成年') || 
                b.innerText.includes('確認') || 
                b.innerText.includes('18歳以上') ||
                b.innerText.includes('Enter')
            );
            if (btn) btn.click();
            return { cookie: document.cookie, userAgent: navigator.userAgent };
        })();
        '''
        
        for attempt in range(2):
            result = await web_crawler.arun(
                url=url, 
                config=self.crawl_config, 
                headers=self._get_http_headers(), 
                js_code=js_bypass,
                wait_for=".movie-box, .bigImage, .photo-info, button:has-text('成年'), button:has-text('確認')"
            )
            
            # Update cookies
            js_out = getattr(result, 'js_execution_result', None) or {}
            results_arr = js_out.get('results', [])
            if isinstance(results_arr, list) and results_arr:
                res = results_arr[0]
                if isinstance(res, dict):
                    self.dynamic_cookie = res.get('cookie', self.dynamic_cookie)
                    self.dynamic_user_agent = res.get('userAgent', self.dynamic_user_agent)

            html = result.html or ""
            if "你是否已經成年" not in html and "確認" not in html and "18歳以上" not in html:
                return BeautifulSoup(html, 'lxml')
            
            print(f"Age gate still present after attempt {attempt+1}, retrying...")
            await asyncio.sleep(1)

        return BeautifulSoup(html, 'lxml')

    def _check_and_save_magnets(self, scene_id: str):
        detail_file = self.media_dir / scene_id / f"{scene_id}.json"
        if detail_file.exists():
            try:
                import os, json
                
                with open(detail_file, 'r', encoding='utf-8') as df:
                    ddata = json.load(df)
                    
                    existing_lines = []
                    magnet_file = self.config.magnet_output_file
                    if os.path.exists(magnet_file):
                        with open(magnet_file, 'r', encoding='utf-8') as mf:
                            existing_lines = mf.read().splitlines()
                            
                    for mag in ddata.get('magnet_entries', []):
                        size_gb = parse_size_to_gb(mag.get('total_size', ''))
                        if size_gb > 1.2:
                            uri = mag.get('uri')
                            if uri not in existing_lines:
                                os.makedirs(os.path.dirname(magnet_file), exist_ok=True)
                                with open(magnet_file, 'a', encoding='utf-8') as mf:
                                    mf.write(uri + "\n")
                                existing_lines.append(uri)
                                print(f"Saved magnet (>1.2GB) for {scene_id}: {size_gb:.2f}GB")
            except Exception as e:
                print(f"Failed to check magnets for {scene_id}: {e}", file=sys.stderr)

    def _load_active_scan(self) -> Dict[str, str]:
        as_path = Path(self.config.active_scan_file)
        if as_path.exists():
            try:
                with open(as_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading active scan JSON: {e}")
        return {}

    def _save_active_scan(self, data: Dict[str, str]):
        as_path = Path(self.config.active_scan_file)
        as_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(as_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save active scan JSON: {e}")

    async def _harvest_performers(self, detail_data: dict, web_crawler: AsyncWebCrawler):
        performers = detail_data.get('performers', [])
        if not performers:
            return
            
        # Junk names to ignore
        junk_names = {"画像を拡大する", "画像を拡大", "拡大する", "画像"}
        
        active_scan_data = self._load_active_scan()
        updated = False
        for p in performers:
            name = p.get('name', '').strip()
            url = p.get('url')
            if name and url and name not in junk_names:
                # Basic cleaning: remove trailing punctuation sometimes found in links
                if name.endswith('（'): name = name[:-1]
                
                # Check if we need to extract full profile
                # If it's not in active_scan, OR if the actress file is missing/incomplete
                actor_file = self.actress_dir / name / f"{name}.json"
                is_incomplete = False
                if actor_file.exists():
                    try:
                        with open(actor_file, 'r', encoding='utf-8') as f:
                            a_data = json.load(f)
                            # If it only has basic keys, it's incomplete
                            if len(a_data.keys()) <= 3:
                                is_incomplete = True
                    except: is_incomplete = True

                if name not in active_scan_data or is_incomplete:
                    if name not in active_scan_data:
                        active_scan_data[name] = url
                        updated = True
                    
                    print(f"Harvesting full profile for: {name}")
                    await self._extract_and_save_actor_info(url, name, web_crawler)
                
        if updated:
            self._save_active_scan(active_scan_data)

    async def _process_discovered_media(self, scene_id: str, title: str, page_url: str, web_crawler: AsyncWebCrawler):
        if not self.config.force and self._is_complete(scene_id):
            print(f"Skipping '{scene_id}' as it appears complete. Use --force to re-process.")
            # Still harvest actors from complete scenes to keep active_scan updated
            detail_file = self.media_dir / scene_id / f"{scene_id}.json"
            if detail_file.exists():
                try:
                    with open(detail_file, 'r', encoding='utf-8') as f:
                        await self._harvest_performers(json.load(f), web_crawler)
                except Exception: pass
        else:
            detail = await self.run_parse(scene_id, {'page_url': page_url}, web_crawler)
            if detail:
                await self._harvest_performers(detail, web_crawler)
            if self.config.download_image:
                await self.run_download(scene_id)
        self._check_and_save_magnets(scene_id)

    def _add_to_actor_media_list(self, actor_name: str, scene_id: str, title: str):
        primary_name, _ = self._resolve_actor_name(actor_name)
        media_list_file = self.actress_dir / primary_name / "media_list.json"
        media_list_file.parent.mkdir(parents=True, exist_ok=True)
        media_data = []
        if media_list_file.exists():
            try:
                import json
                with open(media_list_file, 'r', encoding='utf-8') as f:
                    media_data = json.load(f)
            except Exception:
                pass
        if not any(item.get("id") == scene_id for item in media_data):
            media_data.append({"id": scene_id, "title": title})
            try:
                import json
                with open(media_list_file, 'w', encoding='utf-8') as f:
                    json.dump(media_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to update {media_list_file}: {e}")

    async def _extract_and_save_actor_info(self, star_url: str, actor_name: str, web_crawler: AsyncWebCrawler):
        primary_name, _ = self._resolve_actor_name(actor_name)
        actor_dir = self.actress_dir / primary_name
        actor_dir.mkdir(parents=True, exist_ok=True)
        actor_file = actor_dir / f"{primary_name}.json"
        
        # If not force, and file exists and is complete, skip
        if not self.config.force and actor_file.exists():
            try:
                with open(actor_file, 'r', encoding='utf-8') as f:
                    if len(json.load(f).keys()) > 3:
                        return
            except: pass
            
        print(f"Extracting profile for {actor_name} (Primary: {primary_name}) from {star_url}")
        soup = await self._fetch_soup_safe(star_url, web_crawler)
        if not soup:
            print(f"Failed to fetch profile for {actor_name}")
            return

        info = {"name": primary_name, "url": star_url}
        
        photo_info = soup.select_one(".photo-info")
        if not photo_info:
            print(f"Warning: .photo-info not found for {actor_name}. Might be an age gate issue or missing data.")
        
        avatar = soup.select_one(".photo-frame img")
        if avatar:
            src = avatar.get("src", "")
            if src and not src.startswith("http"):
                src = "https://www.javbus.com" + src
            info["avatar"] = src
            # Only override name if we don't have a primary mapping
            if avatar.get("title") and primary_name == actor_name:
                info["name"] = avatar.get("title", "").strip()
                
        if photo_info:
            for p in photo_info.select("p"):
                p_text = p.get_text(strip=True)
                if ":" in p_text:
                    k, v = p_text.split(":", 1)
                    info[k.strip()] = v.strip()
                    
        if self.config.llm_enrich:
            needs_enrich = False
            if len(info.keys()) < 10 or "生日" not in info:
                needs_enrich = True
            else:
                for k in ["胸圍", "腰圍", "臀圍"]:
                    val = info.get(k, "")
                    match = re.search(r'(\d+)', str(val))
                    if match and int(match.group(1)) < 50:
                        needs_enrich = True
                        break
            
            if needs_enrich:
                llm_info = await self._enrich_actor_info_llm(primary_name, web_crawler)
                if llm_info:
                    key_mapping = {
                        "birthday": "生日",
                        "age": "年齡",
                        "height": "身高",
                        "birthplace": "出生地",
                        "hobbies": "愛好",
                        "bust": "胸圍",
                        "waist": "腰圍",
                        "hip": "臀圍"
                    }
                    for en_k, ch_k in key_mapping.items():
                        v = llm_info.get(en_k)
                        if v:
                            # Suffix 'cm' to sizes if Gemini returned only numbers
                            if ch_k in ["身高", "胸圍", "腰圍", "臀圍"] and re.match(r'^\d+$', str(v)):
                                v = f"{v}cm"
                                
                            is_small_size = False
                            if ch_k in ["胸圍", "腰圍", "臀圍"]:
                                match = re.search(r'(\d+)', str(info.get(ch_k, "")))
                                if match and int(match.group(1)) < 50:
                                    is_small_size = True
                            if ch_k not in info or not info[ch_k] or is_small_size:
                                info[ch_k] = v

        # Ensure name, url, avatar are at the top
        final_info = {"name": info.get("name", primary_name)}
        if "url" in info: final_info["url"] = info["url"]
        if "avatar" in info: final_info["avatar"] = info["avatar"]
        if "aliases" in info: final_info["aliases"] = info["aliases"]
        elif primary_name != actor_name:
            # Auto-register this specific search alias if not present
            final_info["aliases"] = [actor_name]

        final_info.update({k: v for k, v in info.items() if k not in ["name", "url", "avatar", "aliases"]})
        
        final_info = self._inject_meta(final_info)

        try:
            with open(actor_file, 'w', encoding='utf-8') as f:
                json.dump(final_info, f, ensure_ascii=False, indent=2)
            print(f"Saved profile for {actor_name} to {actor_file}")
        except Exception as e:
            print(f"Failed to save profile for {actor_name}: {e}")

    async def _enrich_actor_info_llm(self, actor_name: str, web_crawler: AsyncWebCrawler) -> dict:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY not found in environment, skipping LLM enrichment.")
            return None
            
        print(f"Enriching profile for {actor_name} using LLM via Wikipedia...")
        
        # Helper to check URL validity quickly without spinning up full crawl
        def find_valid_url(name_variants):
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
            for name in name_variants:
                url = f"https://ja.wikipedia.org/wiki/{quote_plus(name)}"
                try:
                    resp = requests.head(url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        return url
                    elif resp.status_code == 405:
                        # Some servers block HEAD, try GET
                        resp = requests.get(url, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            return url
                except Exception as e:
                    pass
            return None
            
        names_to_try = [actor_name, f"{actor_name} (AV女優)", f"{actor_name} (女優)"]
        if "（" in actor_name and "）" in actor_name:
            match = re.search(r'(.+?)（(.+?)）', actor_name)
            if match:
                names_to_try.extend([match.group(1), match.group(2)])
        elif "(" in actor_name and ")" in actor_name:
            match = re.search(r'(.+?)\((.+?)\)', actor_name)
            if match:
                names_to_try.extend([match.group(1), match.group(2)])
                
        valid_url = await asyncio.to_thread(find_valid_url, names_to_try)
        if not valid_url:
            print(f"No valid Wikipedia page found for {actor_name}.")
            return None
            
        instruction = "Extract the actress profile information from the Wikipedia page. Only use metric measurements (cm) for height and sizes, ignoring any imperial (inches) tables."
        try:
            from crawl4ai import LLMConfig
            strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(provider="gemini/gemini-2.5-flash", api_token=api_key),
                instruction=instruction,
                schema=ActressProfileSchema.model_json_schema(),
                extraction_type="schema",
                force_json_response=True
            )
            config = CrawlerRunConfig(extraction_strategy=strategy)
            result = await web_crawler.arun(url=valid_url, config=config)
            
            if result.extracted_content:
                try:
                    data = json.loads(result.extracted_content)
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]
                    elif isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    print("Failed to parse LLM JSON response.")
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            
        return None

    async def _scan_star_pages(self, star_url: str, actor_name: str, web_crawler: AsyncWebCrawler):
        print(f"\n--- Scanning full list for actor: {actor_name} ---")
        page = 1
        while True:
            page_url = f"{star_url}/{page}" if page > 1 else star_url
            print(f"Scanning {actor_name} page {page}: {page_url}")
            
            star_soup = await self._fetch_soup_safe(page_url, web_crawler)
            boxes = star_soup.select('.movie-box')
            if not boxes:
                print(f"No more media found on page {page} for {actor_name}.")
                break
                
            for box in boxes:
                date_tags = box.select('date')
                scene_id = date_tags[0].text.strip() if date_tags else ""
                span_tag = box.select_one('.photo-info span')
                title = span_tag.text.strip() if span_tag else ""
                if title: title = title.split('\n')[0].strip()
                media_url = box.get('href', '')
                if media_url and not media_url.startswith('http'):
                    media_url = "https://www.javbus.com" + media_url
                    
                if not scene_id or not media_url: continue
                
                print(f"[{actor_name}] Found '{scene_id}': {title}")
                self._add_to_actor_media_list(actor_name, scene_id, title)
                await self._process_discovered_media(scene_id, title, media_url, web_crawler)
                
            page += 1
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
            await asyncio.sleep(delay)

    async def run_discovery(self, web_crawler: AsyncWebCrawler):
        ain_list = set()
        ain_file = self.config.ain_list_file
        if ain_file and os.path.exists(ain_file):
            if not ain_file.endswith('.json'):
                print(f"ALERT: Non-JSON list file detected: {ain_file}. Support for plain text lists has been removed.")
            try:
                with open(ain_file, 'r', encoding='utf-8') as f:
                    ain_data = json.load(f)
                    if isinstance(ain_data, dict):
                        ain_list = set(ain_data.keys())
                    else:
                        print(f"ALERT: {ain_file} is not a JSON dictionary. Only dictionary format ({'ActorName': [IDs]}) is supported.")
            except Exception as e:
                print(f"Error loading ain list: {e}")
                
        prefixes = self.config.discover_prefixes
        base_url = SITES_CONFIG.get(self.config.site, {}).get('home_url', 'https://www.javbus.com')
        
        start_p = self.config.discover_start_page
        for page in range(start_p, start_p + self.config.discover_pages):
            url = f"{base_url}/page/{page}" if page > 1 else f"{base_url}/"
            
            print(f"Discovering page {page}: {url}")
            soup = await self._fetch_soup_safe(url, web_crawler)
            
            items = []
            for box in soup.select('.movie-box'):
                date_tags = box.select('date')
                scene_id = date_tags[0].text.strip() if date_tags else ""
                span_tag = box.select_one('.photo-info span')
                title = span_tag.text.strip() if span_tag else ""
                
                if title:
                    title = title.split('\\n')[0].strip()

                page_url = box.get('href', '')
                if page_url and not page_url.startswith('http'):
                    page_url = base_url + page_url
                    
                items.append({
                    'id': scene_id,
                    'title': title,
                    'page_url': page_url
                })
            
            for item in items:
                scene_id = item.get('id')
                title = item.get('title', '')
                page_url = item.get('page_url')
                
                if not scene_id or not page_url:
                    continue
                
                # Match logic
                match_prefix = any(scene_id.startswith(p) for p in prefixes) if prefixes else False
                matched_actor = None
                if ain_list:
                    for actor in ain_list:
                        if actor in title:
                            matched_actor = actor
                            break
                
                # Intuitive Match: If no filters are provided, everything is a match.
                is_match = False
                match_reason = ""
                if not prefixes and not ain_list:
                    is_match = True
                    match_reason = "Unfiltered"
                elif match_prefix:
                    is_match = True
                    match_reason = "Prefix"
                elif matched_actor:
                    is_match = True
                    match_reason = "Actor"

                if is_match:
                    print(f"Matched ({match_reason}) '{scene_id}': {title}")
                    if matched_actor:
                        self._add_to_actor_media_list(matched_actor, scene_id, title)
                    await self._process_discovered_media(scene_id, title, page_url, web_crawler)
            
            if page < start_p + self.config.discover_pages - 1:
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                print(f"Waiting for {delay:.2f} seconds before next page...")
                await asyncio.sleep(delay)

    async def run_collection_scan(self, web_crawler: AsyncWebCrawler):
        active_scan_data = self._load_active_scan()
        if not active_scan_data:
            print(f"No performers found in active scan file: {self.config.active_scan_file}")
            return
            
        # If specific scenes were provided, treat them as group names to scan
        target_groups = self.config.scenes if self.config.scenes else active_scan_data.keys()
        
        for actor_name in target_groups:
            star_url = active_scan_data.get(actor_name)
            if not star_url:
                if self.config.scenes:
                    print(f"Group '{actor_name}' not found in active scan file. Skipping.")
                continue
                
            print(f"\n>>> Scanning collection for '{actor_name}': {star_url}")
            await self._extract_and_save_actor_info(star_url, actor_name, web_crawler)
            await self._scan_star_pages(star_url, actor_name, web_crawler)


    async def download_actor_covers(self, actor_name: str):
        print(f"\n--- Downloading covers for {actor_name} ---")
        media_list_path = self.actress_dir / actor_name / "media_list.json"
        
        if not media_list_path.exists():
            print(f"Media list for {actor_name} not found at {media_list_path}")
            return
            
        with open(media_list_path, 'r', encoding='utf-8') as f:
            media_list = json.load(f)
            
        headers = self._get_http_headers()
        headers['Referer'] = SITES_CONFIG.get(self.config.site, {}).get("home_url", "https://www.javbus.com") + "/"
        
        tasks = []
        async with self._get_client_session(headers=headers) as session:
            for item in media_list:
                scene_id = item.get("id")
                if not scene_id: continue
                
                detail_path = self.media_dir / scene_id / f"{scene_id}.json"
                if not detail_path.exists():
                    print(f"Missing detail JSON for {scene_id}, skipping cover download.")
                    continue
                    
                with open(detail_path, 'r', encoding='utf-8') as df:
                    try:
                        detail = json.load(df)
                    except json.JSONDecodeError:
                        continue
                        
                cover_url = detail.get("cover_image")
                if cover_url:
                    if not cover_url.startswith('http'):
                        cover_url = "https://www.javbus.com" + cover_url
                        
                    from urllib import parse
                    parsed = parse.urlparse(cover_url)
                    name = Path(parsed.path).name
                    ext = '.' + name.split('.')[-1] if '.' in name else '.jpg'
                    
                    dest = self.media_dir / scene_id / f"cover{ext}"
                    
                    async def download_file(session, url, dest):
                        if dest.exists() and dest.stat().st_size > 0:
                            return True
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            async with session.get(url, timeout=20) as resp:
                                resp.raise_for_status()
                                with open(dest, 'wb') as fh:
                                    async for chunk in resp.content.iter_chunked(8192):
                                        fh.write(chunk)
                                return True
                        except Exception as e:
                            if dest.exists() and dest.stat().st_size == 0:
                                try: dest.unlink()
                                except OSError: pass
                            print(f"Failed to download {url}: {e}", file=sys.stderr)
                            return False

                    tasks.append(download_file(session, cover_url, dest))
            
            if tasks:
                print(f"Found {len(tasks)} covers to download. Starting concurrent downloads...")
                semaphore = asyncio.Semaphore(10)
                async def sem_task(t):
                    async with semaphore:
                        return await t
                
                results = await asyncio.gather(*(sem_task(t) for t in tasks))
                success = sum(1 for r in results if r)
                print(f"Successfully downloaded/verified {success} covers for {actor_name}.")
            else:
                print(f"No covers found to download for {actor_name}.")

    def _stash_request(self, query: str, variables: dict = None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        try:
            response = requests.post(self.config.stash_url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Stash request failed ({response.status_code}): {response.text}")
                return None
            result = response.json()
            if "errors" in result:
                print(f"Stash GraphQL errors: {result['errors']}")
            return result.get("data")
        except Exception as e:
            print(f"Failed to connect to Stash: {e}")
            return None

    def _get_or_create_performer(self, name: str):
        cache_key = f"performer_{name}"
        if cache_key in self._stash_cache:
            return self._stash_cache[cache_key]

        query = """
        query FindPerformers($filter: FindFilterType, $performer_filter: PerformerFilterType) {
          findPerformers(filter: $filter, performer_filter: $performer_filter) {
            performers { id name }
          }
        }
        """
        variables = {"performer_filter": {"name": {"value": name, "modifier": "EQUALS"}}}
        data = self._stash_request(query, variables)
        if data and data.get("findPerformers") and data["findPerformers"].get("performers"):
            pid = data["findPerformers"]["performers"][0]["id"]
            self._stash_cache[cache_key] = pid
            return pid
        
        print(f"Performer '{name}' not found. Creating...")
        mutation = """
        mutation PerformerCreate($input: PerformerCreateInput!) {
          performerCreate(input: $input) { id }
        }
        """
        data = self._stash_request(mutation, {"input": {"name": name}})
        pid = data["performerCreate"]["id"] if data and data.get("performerCreate") else None
        if pid:
            self._stash_cache[cache_key] = pid
        return pid

    def _get_or_create_tag(self, name: str):
        cache_key = f"tag_{name}"
        if cache_key in self._stash_cache:
            return self._stash_cache[cache_key]

        query = """
        query FindTags($filter: FindFilterType, $tag_filter: TagFilterType) {
          findTags(filter: $filter, tag_filter: $tag_filter) {
            tags { id name }
          }
        }
        """
        variables = {"tag_filter": {"name": {"value": name, "modifier": "EQUALS"}}}
        data = self._stash_request(query, variables)
        if data and data.get("findTags") and data["findTags"].get("tags"):
            tid = data["findTags"]["tags"][0]["id"]
            self._stash_cache[cache_key] = tid
            return tid
        
        print(f"Tag '{name}' not found. Creating...")
        mutation = """
        mutation TagCreate($input: TagCreateInput!) {
          tagCreate(input: $input) { id }
        }
        """
        data = self._stash_request(mutation, {"input": {"name": name}})
        tid = data["tagCreate"]["id"] if data and data.get("tagCreate") else None
        if tid:
            self._stash_cache[cache_key] = tid
        return tid

    def _get_or_create_studio(self, name: str):
        cache_key = f"studio_{name}"
        if cache_key in self._stash_cache:
            return self._stash_cache[cache_key]

        query = """
        query FindStudios($filter: FindFilterType, $studio_filter: StudioFilterType) {
          findStudios(filter: $filter, studio_filter: $studio_filter) {
            studios { id name }
          }
        }
        """
        variables = {"studio_filter": {"name": {"value": name, "modifier": "EQUALS"}}}
        data = self._stash_request(query, variables)
        if data and data.get("findStudios") and data["findStudios"].get("studios"):
            sid = data["findStudios"]["studios"][0]["id"]
            self._stash_cache[cache_key] = sid
            return sid
        
        print(f"Studio '{name}' not found. Creating...")
        mutation = """
        mutation StudioCreate($input: StudioCreateInput!) {
          studioCreate(input: $input) { id }
        }
        """
        data = self._stash_request(mutation, {"input": {"name": name}})
        sid = data["studioCreate"]["id"] if data and data.get("studioCreate") else None
        if sid:
            self._stash_cache[cache_key] = sid
        return sid

    def _find_scene_by_volume(self, volume_id: str):
        query = """
        query FindScenes($filter: FindFilterType) {
          findScenes(filter: $filter) {
            scenes { id title performers { id } tags { id } studio { id } }
          }
        }
        """
        data = self._stash_request(query, {"filter": {"q": volume_id}})
        if data and data.get("findScenes") and data["findScenes"].get("scenes"):
            return data["findScenes"]["scenes"][0]
        return None

    def _update_scene_in_stash(self, scene_id: str, existing_performers: list, existing_tags: list, performer_id: str = None, tag_id: str = None, studio_id: str = None, cover_path: Path = None):
        input_data = {"id": scene_id}
        
        if performer_id:
            p_ids = [p["id"] for p in existing_performers]
            if performer_id not in p_ids:
                p_ids.append(performer_id)
            input_data["performer_ids"] = p_ids
            
        if tag_id:
            t_ids = [t["id"] for t in existing_tags]
            if tag_id not in t_ids:
                t_ids.append(tag_id)
            input_data["tag_ids"] = t_ids
            
        if studio_id:
            input_data["studio_id"] = studio_id

        if cover_path and cover_path.exists():
            with open(cover_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
                input_data["cover_image"] = f"data:image/jpeg;base64,{img_data}"
        
        mutation = "mutation SceneUpdate($input: SceneUpdateInput!) { sceneUpdate(input: $input) { id } }"
        return self._stash_request(mutation, {"input": input_data})

    async def sync_to_stash_group(self, group_name: str):
        print(f"\n--- Syncing {group_name} to Stash (Type: {self.config.sync_type}) ---")
        
        media_list = []
        # Attempt to load from legacy media_list format
        media_list_path = self.actress_dir / group_name / "media_list.json"
        
        if media_list_path.exists():
            try:
                with open(media_list_path, 'r', encoding='utf-8') as f:
                    media_list = json.load(f)
            except Exception as e:
                print(f"Error loading {media_list_path}: {e}")
        
        # Whitelist Filtering Logic: Use ain_list to filter or supplement the media_list
        if self.config.ain_list_file and Path(self.config.ain_list_file).exists():
            try:
                with open(self.config.ain_list_file, 'r', encoding='utf-8') as f:
                    ain_data = json.load(f)
                    if isinstance(ain_data, dict) and group_name in ain_data:
                        local_ids = set(ain_data[group_name])
                        if media_list:
                            # Filter media_list to only include items on disk
                            original_count = len(media_list)
                            media_list = [m for m in media_list if m.get("id") in local_ids]
                            print(f"Filtered {original_count} scenes to {len(media_list)} local items using {self.config.ain_list_file}.")
                        else:
                            # Fallback to ain_list if no media_list.json exists
                            media_list = [{"id": v_id} for v_id in local_ids]
                            print(f"Loaded {len(media_list)} scenes directly from {self.config.ain_list_file}.")
                    else:
                        print(f"Group '{group_name}' not found in {self.config.ain_list_file}. No filtering applied.")
            except Exception as e:
                print(f"Error processing {self.config.ain_list_file}: {e}")

        if not media_list:
            ain_msg = f" or {self.config.ain_list_file}" if self.config.ain_list_file else ""
            print(f"No scenes to sync for {group_name} (checked media_list.json{ain_msg}).")
            return
            
        p_id = None
        t_id = None
        s_id = None
        
        if self.config.sync_type == "performer":
            p_id = self._get_or_create_performer(group_name)
            if not p_id: return
        elif self.config.sync_type == "tag":
            t_id = self._get_or_create_tag(group_name)
            if not t_id: return
        elif self.config.sync_type == "studio":
            s_id = self._get_or_create_studio(group_name)
            if not s_id: return
        else:
            print(f"Unknown sync_type: {self.config.sync_type}")
            return
        
        for item in media_list:
            v_id = item.get("id")
            if not v_id: continue
            
            detail_file = self.media_dir / v_id / f"{v_id}.json"
            detail_data = {}
            if detail_file.exists():
                try:
                    with open(detail_file, 'r', encoding='utf-8') as df:
                        detail_data = json.load(df)
                except Exception:
                    pass

            meta = detail_data.get("_meta", {})
            current_hash = meta.get("hash")
            last_synced_hash = meta.get("last_synced_hash")

            if current_hash and current_hash == last_synced_hash:
                print(f"  Scene {v_id} unchanged since last sync. Skipping.")
                continue
            
            scene = self._find_scene_by_volume(v_id)
            if not scene:
                print(f"  Scene for {v_id} not found in Stash.")
                continue
                
            cover_file = self.media_dir / v_id / "cover.jpg"
            if not cover_file.exists():
                matches = list(self.media_dir.glob(f"{v_id}/cover.*"))
                if matches: cover_file = matches[0]

            if self._update_scene_in_stash(
                scene_id=scene["id"], 
                existing_performers=scene.get("performers", []), 
                existing_tags=scene.get("tags", []), 
                performer_id=p_id, 
                tag_id=t_id, 
                studio_id=s_id, 
                cover_path=cover_file
            ):
                print(f"  Successfully updated scene {v_id} in Stash.")
                
                # Update last_synced_hash on success
                if current_hash and detail_file.exists():
                    detail_data["_meta"]["last_synced_hash"] = current_hash
                    try:
                        with open(detail_file, 'w', encoding='utf-8') as df:
                            json.dump(detail_data, df, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"  Failed to update last_synced_hash for {v_id}: {e}")

    async def rebuild_list(self, category: str):
        data_dir = os.environ.get("CRAW_DATA", CRAW_DATA)
        out_file = os.path.join(data_dir, "list", f"{category}_list.json")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        base = self.config.rebuild_path.format(category=category)
        
        if self.config.rebuild_host:
            print(f"Rebuilding {out_file} via SSH ({self.config.rebuild_host}:{base})...")
            import subprocess
            cmd = f'ssh {self.config.rebuild_host} "find {base} -maxdepth 2 -type d"'
            try:
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            except Exception as e:
                print(f"Failed to rebuild list via SSH: {e}")
                return
        else:
            print(f"Rebuilding {out_file} via local filesystem ({base})...")
            try:
                import subprocess
                cmd = f'find {base} -maxdepth 2 -type d'
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            except Exception as e:
                print(f"Failed to rebuild list locally: {e}")
                return

        lines = output.strip().split('\n')
        actor_data = {}
        for line in lines:
            line = line.strip()
            if line == base or not line.startswith(base): continue
            rel = line[len(base):].lstrip('/')
            parts = rel.split('/')
            if len(parts) >= 1:
                actress = parts[0]
                if actress not in actor_data: actor_data[actress] = []
                if len(parts) >= 2:
                    actor_data[actress].append(parts[1])
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(actor_data, f, ensure_ascii=False, indent=2)
        print(f"Rebuilt {out_file} with {len(actor_data)} actresses.")

    async def mcp_match(self, file_path: str):
        list_file = self.config.ain_list_file
        if not list_file or not Path(list_file).exists():
            print(f"List file not specified or not found. Cannot proceed.")
            return
        try:
            with open(list_file, "r", encoding="utf-8") as f:
                ain_data = json.load(f)
                if not isinstance(ain_data, dict):
                    print(f"ALERT: {list_file} is not a JSON dictionary. Only dictionary format is supported.")
                    return
                ain_list = set(ain_data.keys())
        except Exception as e:
            print(f"Error loading {list_file}: {e}")
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                mcp_output = json.load(f)
        except Exception as e:
            print(f"Failed to load MCP file {file_path}: {e}")
            return
            
        matches = []
        for item in mcp_output:
            title = item.get("title", "")
            for actor in ain_list:
                if actor in title:
                    matches.append((actor, item.get("id", ""), title, item.get("page_url", "")))
                    
        print(f"Found {len(matches)} matches.")
        for m in matches:
            print(f"Matched {m[0]} -> {m[1]} ({m[2][:30]}...)")

    async def package_release(self, version: str):
        import zipfile
        
        release_dir = Path("release")
        release_dir.mkdir(exist_ok=True)
        archive_name = release_dir / f"crawler-v{version}.zip"
        
        ignored = []
        if Path(".gitignore").exists():
            with open(".gitignore", "r") as f:
                ignored = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
        def is_ignored(p):
            for pattern in ignored:
                if Path(p).match(pattern) or pattern in str(p):
                    return True
            return False
            
        print(f"Creating release archive: {archive_name}")
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk("."):
                if ".git" in root or is_ignored(root): continue
                for file in files:
                    file_path = Path(root) / file
                    if not is_ignored(file_path) and file_path.name != archive_name.name and file_path.name != "package.py":
                        zf.write(file_path)
        print("Package created successfully.")

    async def _process_native(self, scene_id: str, url: str):
        print(f"\n>>> Native Processing: {scene_id} at {url}")
        from bs4 import BeautifulSoup
        
        html = ""
        async with self._get_client_session(headers=self._get_http_headers()) as session:
            try:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                    else:
                        print(f"Failed {scene_id}: HTTP {resp.status}")
                        return
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                return
                
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.select_one('.header')
        if not header:
            print(f"Skipped {scene_id} (Age Gate or 404)")
            return
            
        title = header.text.strip()
        cover = soup.select_one('.bigImage img')
        cover_url = cover['src'] if cover else ""
        if cover_url and not cover_url.startswith('http'):
            cover_url = "https://www.javbus.com" + cover_url
            
        samples = [img['src'] if img['src'].startswith('http') else "https://www.javbus.com" + img['src']
                   for img in soup.select('.sample-box img')]

        detail = {
            'id': scene_id,
            'title': title,
            'cover_image': cover_url,
            'sample_images': samples,
            'page_url': url
        }

        info_block = soup.select_one(".col-md-3.info") or soup.select_one(".info")
        if info_block:
            for p in info_block.select("p"):
                text = p.get_text(separator=' ', strip=True)
                if "識別碼:" in text or "ID:" in text:
                    detail["id"] = text.split(":")[-1].strip()
                elif "發行日期:" in text:
                    detail["release_date"] = text.split(":")[-1].strip()
                elif "長度:" in text:
                    detail["length"] = text.split(":")[-1].strip()
                elif "導演:" in text:
                    detail["director"] = text.split(":")[-1].strip()
                elif "製作商:" in text:
                    detail["studio"] = text.split(":")[-1].strip()
                elif "發行商:" in text:
                    detail["label"] = text.split(":")[-1].strip()

            genres = []
            for span in info_block.select("span.genre a[href*='/genre/']"):
                genres.append(span.text.strip())
            if genres:
                detail["genres"] = genres

            performers = []
            seen = set()
            for a in info_block.select("a[href*='/star/']"):
                p_name = a.text.strip()
                p_url = a.get('href', '')
                if p_name and p_url and p_url not in seen:
                    if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
                    
                    primary_name, credited_as = self._resolve_actor_name(p_name)
                    p_data = {"name": primary_name, "url": p_url}
                    if credited_as:
                        p_data["credited_as"] = credited_as
                        
                    performers.append(p_data)
                    seen.add(p_url)
            detail["performers"] = performers
        else:
            # Fallback for performers
            performers = []
            for a in soup.select('a[href*="/star/"]'):
                p_name = a.text.strip()
                p_url = a.get('href', '')
                if p_name and p_url:
                    if not p_url.startswith('http'): p_url = "https://www.javbus.com" + p_url
                    
                    primary_name, credited_as = self._resolve_actor_name(p_name)
                    p_data = {"name": primary_name, "url": p_url}
                    if credited_as:
                        p_data["credited_as"] = credited_as
                        
                    performers.append(p_data)
            detail["performers"] = performers

        magnets = []
        for tr in soup.select('#magnet-table tr'):
            links = tr.select('a')
            if len(links) >= 3:
                magnets.append({
                    'name': links[0].text.strip(),
                    'uri': links[0]['href'],
                    'total_size': links[1].text.strip(),
                    'date': links[2].text.strip()
                })

        detail['magnet_entries'] = magnets

        detail_dir = self.media_dir / detail['id']
        detail_dir.mkdir(parents=True, exist_ok=True)
        detail_file = detail_dir / f"{detail['id']}.json"

        detail = self._inject_meta(detail)

        with open(detail_file, "w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, indent=2)
        print(f"Wrote {detail_file}")
        
        if self.config.run_download:
            await self.run_download(scene_id)
            
        # Append magnets
        magnet_file = self.config.magnet_output_file
        for mag in magnets:
            gb = parse_size_to_gb(mag['total_size'])
            if gb > 1.2:
                os.makedirs(os.path.dirname(magnet_file), exist_ok=True)
                with open(magnet_file, 'a', encoding='utf-8') as mf:
                    mf.write(mag['uri'] + '\n')
                print(f" Saved magnet: {gb:.2f}GB")

    async def process_scenes(self, run_search: bool, run_parse: bool, run_download: bool):
        if self.config.native_fetch:
            print("\n>>> Bypassing Crawl4AI. Using lightweight native HTTP/BS4 pipeline...")
            semaphore = asyncio.Semaphore(3)
            
            async def process_with_semaphore(scene_name):
                if not self.config.force and self._is_complete(scene_name):
                    print(f"Skipping '{scene_name}' as it appears complete. Use --force to re-process.")
                    return
                async with semaphore:
                    url = build_url(self.config.site, scene_name)
                    await self._process_native(scene_name, url)
                    
            tasks = [process_with_semaphore(scene_name) for scene_name in self.config.scenes]
            if tasks:
                await asyncio.gather(*tasks)
            return

        browser_conf = BrowserConfig(
            headless=True,
            user_data_dir=self.config.user_data_dir,
            extra_args=[
                "--disable-ipv6",
                "--disable-network-manager-config",
                "--disable-background-networking",
                "--no-sandbox"
            ]
        )
        async with AsyncWebCrawler(config=browser_conf) as web_crawler:
            print(f"Initializing session context...")
            await self._fetch_soup_safe(SITES_CONFIG.get(self.config.site, {}).get('home_url', 'https://www.javbus.com'), web_crawler)
            
            if self.config.discover:
                await self.run_discovery(web_crawler)
            if self.config.collection_scan:
                await self.run_collection_scan(web_crawler)
            if not self.config.discover and not self.config.collection_scan:
                semaphore = asyncio.Semaphore(3)
                async def process_with_semaphore(idx, scene_name):
                    async with semaphore:
                        if not self.config.force and self._is_complete(scene_name):
                            print(f"Skipping '{scene_name}' as it appears complete. Use --force to re-process.")
                            return
                        try:
                            await self._process_single_scene(scene_name, web_crawler, run_search, run_parse, run_download)
                            if idx < len(self.config.scenes) - 1:
                                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                                await asyncio.sleep(delay)
                        except Exception as e:
                            print(f"Failed to process scene '{scene_name}': {e}", file=sys.stderr)
                
                tasks = [process_with_semaphore(i, sc) for i, sc in enumerate(self.config.scenes)]
                if tasks:
                    await asyncio.gather(*tasks)

def parse_time(time_str: str) -> float:
    if isinstance(time_str, (int, float)):
        return float(time_str)
    time_str = str(time_str).lower().strip()
    if time_str.endswith('s'):
        return float(time_str[:-1])
    elif time_str.endswith('m'):
        return float(time_str[:-1]) * 60
    elif time_str.endswith('h'):
        return float(time_str[:-1]) * 3600
    return float(time_str)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crawler for javdb-like pages")
    parser.add_argument("scene", nargs='*', help="One or more scene identifiers to process")
    parser.add_argument("--site", default="javdb", help="Site key to use from SITE_REGISTRY")
    parser.add_argument("--merge-detail", action="store_true", help="Enable merging parsed detail into search JSON")
    parser.add_argument("--download-image", action="store_true", help="Enable downloading cover and sample images")
    parser.add_argument("--run-search", action="store_true", help="Run the search phase")
    parser.add_argument("--run-parse", action="store_true", help="Run the parse phase")
    parser.add_argument("--run-download", action="store_true", help="Run the download phase")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-processing")
    parser.add_argument("--media-dir", default=os.path.join(CRAW_DATA, "media_detail"), help="Directory to save media details")
    parser.add_argument("--actress-dir", default=os.path.join(CRAW_DATA, "actress"), help="Directory to save actress details")
    parser.add_argument("--search-dir", default="search_site", help="Directory to save search results")
    parser.add_argument("--logdir", default=".", help="Directory to save verbose output files")
    parser.add_argument("--input-file", help="JSON file with a list of scenes to process")
    parser.add_argument("--retry-limit", type=int, default=None, help="Number of retries")
    parser.add_argument("--min-delay", type=str, default="10s", help="Min delay")
    parser.add_argument("--max-delay", type=str, default="90s", help="Max delay")
    parser.add_argument("--user-data-dir", default="./chrome-profile", help="Chrome profile path")
    parser.add_argument("--user-agent", default=None, help="Custom User-Agent")
    parser.add_argument("--dry-run", action="store_true", help="Dry run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--discover", action="store_true", help="Discovery mode")
    parser.add_argument("--collection-scan", action="store_true", help="Collection scan mode")
    parser.add_argument("--start-page", type=int, default=1, help="Start page")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages")
    parser.add_argument("--prefix", nargs='+', default=[], help="ID prefixes")
    parser.add_argument("--ain-list", default=None, help="Actor list file (e.g. data/ain_list.json, data/cin_list.json)")
    parser.add_argument("--active-scan", default=os.path.join(CRAW_CONF, "active_scan.json"), help="Active scan file")
    parser.add_argument("--magnet-output", default=os.path.join(CRAW_DATA, "output", "to-be-downloaded.txt"), help="File to append magnets to")
    parser.add_argument("--download-actor-covers", default="", help="Download all covers for the specified actor")
    parser.add_argument("--stash-url", default="http://192.168.20.24:9999/graphql", help="Stash GraphQL URL")
    parser.add_argument("--sync-to-stash", default="", help="Sync all scenes for the specified group to Stash")
    parser.add_argument("--sync-type", default="performer", choices=["performer", "tag", "studio"], help="Type of entity to sync (default: performer)")
    parser.add_argument("--rebuild-list", type=str, metavar="CATEGORY", help="Rebuild <category>_list.json via SSH (e.g. ain, cin, golden)")
    parser.add_argument("--rebuild-host", type=str, help="SSH connection string (default: winsonsun@192.168.20.24)")
    parser.add_argument("--rebuild-path", type=str, help="Path template for indexing (default: /mnt/cig/video/{category})")
    parser.add_argument("--mcp-match", type=str, help="Match MCP JSON output file against the current actor list file")
    parser.add_argument("--package", type=str, help="Create a release zip with the given version")
    parser.add_argument("--native-fetch", action="store_true", help="Use lightweight native HTTP/BS4 instead of headless browser")
    parser.add_argument("--llm-enrich", action="store_true", help="Use LLM to enrich missing actor profile data via Wikipedia")

    args = parser.parse_args()
    config = CrawlerConfig()
    config.user_agent = args.user_agent or os.environ.get("USER_AGENT") or config.user_agent
    config.site = args.site
    config.merge_detail = args.merge_detail
    config.download_image = args.download_image
    config.force = args.force
    config.verbose = args.verbose
    config.media_dir = args.media_dir
    config.actress_dir = args.actress_dir
    config.search_dir = args.search_dir
    config.logdir = args.logdir
    config.user_data_dir = args.user_data_dir
    config.dry_run = args.dry_run
    config.discover = args.discover
    config.collection_scan = args.collection_scan
    config.discover_start_page = args.start_page
    config.discover_pages = args.pages
    config.discover_prefixes = args.prefix
    config.ain_list_file = args.ain_list
    config.active_scan_file = args.active_scan
    config.magnet_output_file = args.magnet_output
    config.download_actor_covers = args.download_actor_covers
    config.stash_url = args.stash_url
    config.sync_to_stash = args.sync_to_stash
    config.sync_type = args.sync_type
    config.native_fetch = args.native_fetch
    config.llm_enrich = args.llm_enrich
    config.rebuild_host = args.rebuild_host if args.rebuild_host is not None else config.rebuild_host
    config.rebuild_path = args.rebuild_path if args.rebuild_path is not None else config.rebuild_path

    c = Crawler(config)

    # Standalone utilities
    if args.rebuild_list:
        await c.rebuild_list(args.rebuild_list)
        return

    if args.mcp_match:
        await c.mcp_match(args.mcp_match)
        return

    if args.package:
        await c.package_release(args.package)
        return

    if config.dry_run:
        print("Dry run headers:", c._get_http_headers())
        return

    if args.input_file:
        with open(args.input_file, 'r') as f:
            data = json.load(f)
            config.scenes = data if isinstance(data, list) else data.get('scenes', [])
    elif args.scene:
        config.scenes.extend(args.scene)
    
    config.retry_limit = args.retry_limit if args.retry_limit is not None else config.retry_limit
    config.min_delay = parse_time(args.min_delay)
    config.max_delay = parse_time(args.max_delay)

    run_search, run_parse, run_download = args.run_search, args.run_parse, args.run_download
    
    if config.download_actor_covers:
        await c.download_actor_covers(config.download_actor_covers)
    elif config.sync_to_stash and not any([run_search, run_parse, run_download]):
        await c.sync_to_stash_group(config.sync_to_stash)
    else:
        if not any([run_search, run_parse, run_download]):
            run_search = run_parse = run_download = True
        
        await c.process_scenes(run_search, run_parse, run_download)
        
        if config.sync_to_stash:
            await c.sync_to_stash_group(config.sync_to_stash)

if __name__ == "__main__":
    asyncio.run(main())
