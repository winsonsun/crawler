with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

text = text.replace("                                if res and isinstance", "                if res and isinstance")
with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
