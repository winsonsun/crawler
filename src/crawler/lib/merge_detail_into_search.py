#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge media_detail JSON into search_site/<site>_search.json.
Usage:
  python3 merge_detail_into_search.py media_detail/MIST-001/MIST-001.json --site javdb
If given a directory, will merge all `*.json` files inside.
"""
import argparse
import json
import shutil
import time
from pathlib import Path

FIELDS_TO_MERGE = [
    'sample_images', 'actors', 'tags', 'duration', 'duration_minutes',
    'cover_image', 'page_url', 'play_url', 'released_date', 'maker', 'publisher', 'magnet_links',
    'release_date', 'length', 'director', 'studio', 'label', 'genres', 'performers'
]


def merge_detail(detail_path: Path, site_key: str, search_dir: str = 'search_site') -> dict:
    detail = json.loads(detail_path.read_text(encoding='utf-8'))
    sid = detail.get('id') or detail_path.stem

    search_dir = Path(search_dir)
    search_dir.mkdir(exist_ok=True)
    search_file = search_dir / f"{site_key}_search.json"

    if search_file.exists():
        # backup
        bak = search_dir / f"{site_key}_search.json.bak.{int(time.time())}"
        shutil.copy2(search_file, bak)

        try:
            search_data = json.loads(search_file.read_text(encoding='utf-8'))
        except Exception:
            search_data = {}
    else:
        search_data = {}

    entry = search_data.get(sid, {}) or {}

    # Merge fields
    for f in FIELDS_TO_MERGE:
        if f in detail and detail[f]:
            entry[f] = detail[f]

    # Also ensure some common mappings
    # If cover_image provided, keep image_url if not present
    if 'cover_image' in entry and 'image_url' not in entry:
        entry['image_url'] = entry['cover_image']

    if 'page_url' in entry:
        entry['page_url'] = entry['page_url']

    # Update title if available and missing
    if 'title' in detail and ('title' not in entry or not entry.get('title')):
        entry['title'] = detail['title']

    # Write back
    search_data[sid] = entry

    # Pretty write
    search_file.write_text(json.dumps(search_data, ensure_ascii=False, indent=2), encoding='utf-8')

    return {'id': sid, 'merged_keys': list(entry.keys()), 'search_file': str(search_file)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('path', help='detail json file or directory')
    p.add_argument('--site', default='javdb', help='site key (default javdb)')
    p.add_argument('--search-dir', default='search_site', help='Directory to save search results')
    args = p.parse_args()

    path = Path(args.path)
    results = []
    if path.is_dir():
        for j in sorted(path.glob('*.json')):
            res = merge_detail(j, args.site, search_dir=args.search_dir)
            print(f"Merged {j} => {res['search_file']} (keys: {', '.join(res['merged_keys'])})")
            results.append(res)
    else:
        if not path.exists():
            print(f"File not found: {path}")
            raise SystemExit(2)
        res = merge_detail(path, args.site, search_dir=args.search_dir)
        print(f"Merged {path} => {res['search_file']} (keys: {', '.join(res['merged_keys'])})")


if __name__ == '__main__':
    main()
