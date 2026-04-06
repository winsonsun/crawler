#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse a saved page markdown and merge parsed fields into existing media_detail JSON.
Usage:
  python3 update_detail_from_page.py --page my_page.txt --id MIST-001
"""
import argparse
import json
import shutil
import os
from pathlib import Path

CRAW_DATA = os.environ.get("CRAW_DATA", "./data")
DEFAULT_MEDIA_DIR = os.path.join(CRAW_DATA, "media_detail")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--page', required=True)
    p.add_argument('--id', required=True)
    p.add_argument('--media-dir', default=DEFAULT_MEDIA_DIR, help='Directory to save media details')
    args = p.parse_args()

    page_path = Path(args.page)
    if not page_path.exists():
        print('Page file not found:', page_path)
        raise SystemExit(2)

    try:
        from sites.javdb import page_parser
    except Exception as e:
        print('Failed to import page_parser:', e)
        raise

    txt = page_path.read_text(encoding='utf-8')
    parsed = page_parser.parse_from_text(txt, id_hint=args.id)
    if not parsed:
        print('No parsed detail found in page')
        raise SystemExit(1)

    media_dir = Path(args.media_dir) / parsed.get('id', args.id)
    media_dir.mkdir(parents=True, exist_ok=True)
    dest = media_dir / f"{parsed.get('id', args.id)}.json"

    # backup existing
    if dest.exists():
        bak = dest.with_suffix(dest.suffix + '.bak')
        shutil.copy2(dest, bak)
        print('Backed up', dest, 'to', bak)

    # If existing file exists, merge some fields instead of overwriting everything
    if dest.exists():
        try:
            existing = json.loads(dest.read_text(encoding='utf-8'))
        except Exception:
            existing = {}
    else:
        existing = {}

    # Merge strategy: favor parsed fields for lists and magnet_entries, keep existing other fields when present
    for k, v in parsed.items():
        # Replace lists and magnet_entries
        if isinstance(v, list) or k in ('magnet_entries', 'magnet_links'):
            existing[k] = v
        else:
            # keep existing value if present, else use parsed
            if k not in existing or not existing.get(k):
                existing[k] = v

    # always ensure id and title
    existing['id'] = parsed.get('id', existing.get('id', args.id))
    if parsed.get('title'):
        existing['title'] = parsed.get('title')

    dest.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Wrote', dest)

if __name__ == '__main__':
    main()
