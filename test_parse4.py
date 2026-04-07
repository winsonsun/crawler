import requests
from bs4 import BeautifulSoup
import json

headers = {"Cookie": "existmag=all; age=verified; dv=1"}
html = requests.get("https://www.javbus.com/MKMP-713", headers=headers).text
soup = BeautifulSoup(html, "lxml")

detail = {}
info_block = soup.select_one(".col-md-3.info") or soup.select_one(".info")
if info_block:
    for p in info_block.select("p"):
        text = p.get_text(separator=' ', strip=True)
        print("TEXT:", repr(text))
