import re
with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Let's inspect the fallback in run_parse
m = re.search(r'detail\["cover_image"\].*?', text)
print(m)
