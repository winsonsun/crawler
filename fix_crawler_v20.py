with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

text = text.replace('        print(f"\n--- Scanning full list for actor: {actor_name} ---")', '        print(f"\\n--- Scanning full list for actor: {actor_name} ---")')

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
