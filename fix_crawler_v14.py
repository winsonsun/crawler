with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Fix the referer in run_download
import re
text = re.sub(
    r"'Referer': SITES_CONFIG\.get\(self\.config\.site, \{\}\)\.get\(\"home_url\", \"\"\)",
    "'Referer': SITES_CONFIG.get(self.config.site, {}).get(\"home_url\", \"\") + \"/\"",
    text
)

# Remove the debug headers print
text = text.replace('print(f"DEBUG HEADERS: {headers}")\n                ', '')
text = text.replace('print(f"Downloaded: {len(res[\'downloaded\'])} images, Failed: {len(res[\'failed\'])}")', 'print("Downloaded cover and sample images")')

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)

with open("src/crawler/lib/download_samples.py", "r") as f:
    text2 = f.read()

# Remove the print from download_samples
text2 = text2.replace(
    "except Exception as e:\n            print(f'Download failed for {url}: {e}')\n            results['failed'].append(url)",
    "except Exception:\n            results['failed'].append(url)"
)
with open("src/crawler/lib/download_samples.py", "w") as f:
    f.write(text2)
