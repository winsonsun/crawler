# Patch Examples

Use these templates when generating a "Fix Script" to surgically mutate the codebase.

## 1. Surgical Method Replacement (Regex)
Use `re.sub` with `re.DOTALL` to swap out an entire method implementation while keeping its signature.

```python
import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# Replace the _fetch_soup_safe method
new_method = """
    async def _fetch_soup_safe(self, url: str, web_crawler: AsyncWebCrawler):
        # [New implementation logic here]
"""

content = re.sub(
    r"\s+async def _fetch_soup_safe\(self, url: str, web_crawler: AsyncWebCrawler\):.*?(?=\s+def _next_method)",
    new_method,
    content,
    flags=re.DOTALL
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
```

## 2. Async Lock/Semaphore Injection
Use for protecting shared resources (files, sessions) during high-concurrency tasks.

```python
# Injection into __init__
if "self.search_lock =" not in content:
    content = re.sub(
        r"self\.session_id =.*?\)",
        "\\g<0>\n        self.search_lock = asyncio.Lock()",
        content,
        flags=re.DOTALL
    )
```

## 3. Playwright JS Injection
For bypassing age gates or Cloudflare challenges.

```python
# Injecting a JS bypass string
js_bypass = '''
return (() => {
    const btn = document.querySelector('button.age-confirm');
    if (btn) btn.click();
    return { cookie: document.cookie };
})();
'''
# [Update the crawler.arun call with the new js_code]
```

## 4. Argparse/Config Expansion
For adding new CLI flags or configuration parameters.

```python
# Add a new argument
old_arg = 'parser.add_argument("--site", default="javdb")'
new_arg = old_arg + '\n    parser.add_argument("--new-feature", action="store_true")'
content = content.replace(old_arg, new_arg)
```
