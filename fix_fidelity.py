import re

with open("src/crawler/sites/javdb/page_parser.py", "r") as f:
    content = f.read()

# Update the magnet_entries extraction logic to capture dates
new_magnet_logic = """
        # try to find file count like '1 file(s)'
        file_count = None
        mcount = re.search(r'([0-9]+)\s*file', display, flags=re.I)
        if mcount:
            try:
                file_count = int(mcount.group(1))
            except Exception:
                file_count = None

        # FIDELITY UPDATE: try to find update date like '2013-06-13'
        # Check display text first, then check the line immediately AFTER the link in block_text
        date_str = None
        mdate = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2})', display)
        if mdate:
            date_str = mdate.group(1)
        else:
            # Look in the context surrounding the match in block_text
            context = block_text[m.end():m.end()+100]
            mdate_context = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2})', context)
            if mdate_context:
                date_str = mdate_context.group(1)

        magnet_entries.append({
            'uri': uri.rstrip('),.;'),
            'name': name,
            'total_size': total_size,
            'file_count': file_count,
            'date': date_str
        })
"""

content = re.sub(
    r"\s+# try to find file count like '1 file\(s\)'\s+file_count = None.*?magnet_entries\.append\(\{.*?\}\)",
    new_magnet_logic,
    content,
    flags=re.DOTALL
)

with open("src/crawler/sites/javdb/page_parser.py", "w") as f:
    f.write(content)
