# Refactor Patterns

Use these patterns to compress the "messy" state of the project into a clean, hierarchical "Basement."

## 1. The Site Adapter Pattern
Move site-specific quirks into a separate module in `src/crawler/sites/`.

**Original Monolith Logic:**
```python
if self.config.site == "javbus":
    selector = ".movie-box"
elif self.config.site == "javdb":
    selector = ".item"
```

**Refactored Adapter:**
```python
# src/crawler/sites/javbus/parser.py
def extract_items(html):
    # [Site-specific logic]
```

## 2. Library Extraction (shared Logic)
Move methods that don't depend on site-specific data to `src/crawler/lib/`.

**Candidates for Extraction:**
- `_get_http_headers()`
- `download_image(url, dest)`
- `async_save_json(data, path)`
- Lock and Semaphore management logic.

## 3. Pipeline Abstraction
The `crawler.py` should only manage the "High-Level Orchestration." The actual "Steps" of the business process should be in a `pipeline.py`.

```python
# src/crawler/lib/pipeline.py
class ExtractionPipeline:
    async def run_search(self, query): ...
    async def run_parse(self, url): ...
```

## 4. Fossil Consolidation
When a site parser is stable and refactored, the associated "Scars" in `FOSSIL_RECORD.md` should be moved to the top of the site's `__init__.py` or `parser.py` as docstrings, serving as "Living Documentation."
