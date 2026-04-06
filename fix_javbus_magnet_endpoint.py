import re
import json

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# Replace endpoints list in _fetch_javbus_magnets
old_endpoints = """        endpoints = [
            "https://www.javbus.com/ajax/uncensored-torrent.php",
            "https://www.javbus.com/ajax/torrent.php"
        ]"""
new_endpoints = """        endpoints = [
            "https://www.javbus.com/ajax/uncledatoolsbyajax.php"
        ]"""
content = content.replace(old_endpoints, new_endpoints)

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
