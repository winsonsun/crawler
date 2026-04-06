import re
with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

text = text.replace("print(f\"Downloaded: {len(res['downloaded'])} images, Failed: {len(res['failed'])}\")", 
                    "print(f\"Downloaded: {len(res['downloaded'])} images, Failed: {len(res['failed'])}\")\n                print(f\"DEBUG HEADERS: {headers}\")")
with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
