with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

text = text.replace("if title: title = title.split('\n')[0].strip()", "if title: title = title.split('\\n')[0].strip()")

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
