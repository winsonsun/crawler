import re

with open("src/crawler/crawler.py", "r") as f:
    text = f.read()

correct_method = """    def _check_and_save_magnets(self, scene_id: str):
        detail_file = self.media_dir / scene_id / f"{scene_id}.json"
        if detail_file.exists():
            try:
                import os, json
                from .crawler import parse_size_to_gb # or just rely on global scope
                
                with open(detail_file, 'r', encoding='utf-8') as df:
                    ddata = json.load(df)
                    
                    existing_lines = []
                    if os.path.exists('to-be-downloaded.txt'):
                        with open('to-be-downloaded.txt', 'r', encoding='utf-8') as mf:
                            existing_lines = mf.read().splitlines()
                            
                    for mag in ddata.get('magnet_entries', []):
                        size_gb = parse_size_to_gb(mag.get('total_size', ''))
                        if size_gb > 1.2:
                            uri = mag.get('uri')
                            if uri not in existing_lines:
                                with open('to-be-downloaded.txt', 'a', encoding='utf-8') as mf:
                                    mf.write(uri + "\\n")
                                existing_lines.append(uri)
                                print(f"Saved magnet (>1.2GB) for {scene_id}: {size_gb:.2f}GB")
            except Exception as e:
                print(f"Failed to check magnets for {scene_id}: {e}", file=sys.stderr)"""

text = re.sub(r'    def _check_and_save_magnets\(self, scene_id: str\):.*?(?=    async def _process_discovered_media)', correct_method + "\n\n", text, flags=re.DOTALL)

with open("src/crawler/crawler.py", "w") as f:
    f.write(text)
