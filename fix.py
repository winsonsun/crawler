with open("src/crawler/crawler.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "document.cookie =" in line and "self.dynamic_cookie.replace" in line:
        lines[i] = '                document.cookie = "{self.dynamic_cookie.replace(\'\\\"\', \'\\\\\\\"\')}";\n'

with open("src/crawler/crawler.py", "w") as f:
    f.writelines(lines)
