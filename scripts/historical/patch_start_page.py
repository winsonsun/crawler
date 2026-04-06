with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Add discover_start_page to config
text = text.replace(
    "discover_pages: int = 3",
    "discover_start_page: int = 1\n    discover_pages: int = 3"
)

# Update run_discovery range
text = text.replace(
    "for page in range(1, self.config.discover_pages + 1):",
    "for page in range(self.config.discover_start_page, self.config.discover_start_page + self.config.discover_pages):"
)

# Update argparse
text = text.replace(
    "parser.add_argument(\"--pages\", type=int, default=3",
    "parser.add_argument(\"--start-page\", type=int, default=1, help=\"Starting page for discovery\")\n    parser.add_argument(\"--pages\", type=int, default=3"
)

# Update args assignment
text = text.replace(
    "config.discover_pages = args.pages",
    "config.discover_start_page = args.start_page\n    config.discover_pages = args.pages"
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
