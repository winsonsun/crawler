with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Fix path for actress file
import re
text = re.sub(
    r"actor_file = Path\(self\.config\.active_scan_file\)\.parent / f\"\{actor_name\}\.json\"",
    r'actor_file = Path("actress") / f"{actor_name}.json"',
    text
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
