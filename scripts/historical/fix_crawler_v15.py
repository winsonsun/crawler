import re

with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

# Replace the generic "Downloaded cover and sample images" message
new_download_print = """                if res and isinstance(res, dict):
                    for dl in res.get('downloaded', []):
                        print(f"Downloaded image: {dl}")
                    for fl in res.get('failed', []):
                        print(f"Failed to download image: {fl}")
                    if not res.get('downloaded') and not res.get('failed') and res.get('skipped'):
                        print("Images already exist, skipping download.")"""

text = text.replace('print("Downloaded cover and sample images")', new_download_print)

# Fix the double magnet appending
# Remove self._check_and_save_magnets from run_parse
text = re.sub(r'\s+self\._check_and_save_magnets\(detail\["id"\]\)\n', '\n', text)

# Update _check_and_save_magnets to prevent duplicate entries in the text file
new_magnet_logic = """    def _check_and_save_magnets(self, scene_id: str):
        detail_file = self.media_dir / scene_id / f"{scene_id}.json"
        if detail_file.exists():
            try:
                with open(detail_file, 'r', encoding='utf-8') as df:
                    ddata = json.load(df)
                    for mag in ddata.get('magnet_entries', []):
                        size_gb = parse_size_to_gb(mag.get('total_size', ''))
                        if size_gb > 1.2:
                            # Read existing to avoid duplicates
                            existing_lines = []
                            if os.path.exists('to-be-downloaded.txt'):
                                with open('to-be-downloaded.txt', 'r', encoding='utf-8') as mf:
                                    existing_lines = mf.read().splitlines()
                            
                            uri = mag.get('uri')
                            if uri not in existing_lines:
                                with open('to-be-downloaded.txt', 'a', encoding='utf-8') as mf:
                                    mf.write(f"{uri}\\n")
                                print(f"Saved magnet (>1.2GB) for {scene_id}: {size_gb:.2f}GB")
            except Exception as e:
                print(f"Failed to check magnets for {scene_id}: {e}", file=sys.stderr)"""

# Replace _check_and_save_magnets block
text = re.sub(r'    def _check_and_save_magnets\(self, scene_id: str\):.*?(?=    async def _process_discovered_media)', new_magnet_logic + "\n\n", text, flags=re.DOTALL)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
