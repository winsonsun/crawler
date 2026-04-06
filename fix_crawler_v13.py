import re
with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Make it print the result of download
text = text.replace('print("Downloaded cover and sample images")', 'print(f"Downloaded: {len(res[\'downloaded\'])} images, Failed: {len(res[\'failed\'])}")')

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)

with open("src/crawler/lib/download_samples.py", "r") as f:
    text2 = f.read()

# Make it print the exception in download_samples
text2 = text2.replace(
    "except Exception:\n            results['failed'].append(url)",
    "except Exception as e:\n            print(f'Download failed for {url}: {e}')\n            results['failed'].append(url)"
)
with open("src/crawler/lib/download_samples.py", "w") as f:
    f.write(text2)
