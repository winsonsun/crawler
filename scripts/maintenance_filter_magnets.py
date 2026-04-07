import os
import json
import datetime
import glob
from pathlib import Path

CRAW_DATA = os.environ.get("CRAW_DATA", "./data")

def is_recent(date_str, max_days=365):
    if not date_str:
        return True
    try:
        dt = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        limit = datetime.datetime.now() - datetime.timedelta(days=max_days)
        return dt >= limit
    except ValueError:
        return True

def main():
    import argparse
    import json
    
    CRAW_CONF = os.environ.get("CRAW_CONF", "./config")
    crawler_json_path = os.path.join(CRAW_CONF, "crawler.json")
    default_days = 365
    if os.path.exists(crawler_json_path):
        try:
            with open(crawler_json_path, "r", encoding="utf-8") as f:
                crawler_defaults = json.load(f)
                default_days = crawler_defaults.get("magnet_max_age_days", 365)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Filter magnets in to-be-downloaded.txt based on age.")
    parser.add_argument("--days", type=int, default=default_days, help=f"Filter out magnets older than this many days (default: {default_days})")
    args = parser.parse_args()

    magnet_file = os.path.join(CRAW_DATA, "output", "to-be-downloaded.txt")
    media_dir = Path(CRAW_DATA) / "media_detail"
    
    if not os.path.exists(magnet_file):
        print(f"File not found: {magnet_file}")
        return

    print(f"Scanning media details for age verification (Max age: {args.days} days)...")
    blacklist = set()
    whitelist = set()
    
    json_files = list(media_dir.glob("**/*.json"))
    print(f"Found {len(json_files)} metadata files.")

    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                date = data.get('release_date') or data.get('date')
                # If we find magnet entries in the JSON
                magnets = data.get('magnet_entries', [])
                uris = [m.get('uri') for m in magnets if m.get('uri')]
                
                if not is_recent(date, max_days=args.days):
                    for u in uris:
                        blacklist.add(u)
                else:
                    for u in uris:
                        whitelist.add(u)
        except Exception:
            continue

    print(f"Identified {len(blacklist)} magnets older than {args.days} days.")
    print(f"Identified {len(whitelist)} magnets newer than {args.days} days.")

    # Load current file
    with open(magnet_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_count = len(lines)
    filtered_lines = []
    removed_count = 0

    for line in lines:
        uri = line.strip()
        if not uri:
            continue
            
        # Decision logic:
        # 1. If it's explicitly blacklisted -> remove
        # 2. If it's explicitly whitelisted -> keep
        # 3. If it's unknown -> keep (fail open)
        if uri in blacklist and uri not in whitelist:
            removed_count += 1
            continue
        
        filtered_lines.append(line)

    if removed_count > 0:
        with open(magnet_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_lines)
        print(f"Maintenance complete. Removed {removed_count} old magnets from {magnet_file}.")
        print(f"Remaining magnets: {len(filtered_lines)} (Original: {original_count})")
    else:
        print("No old magnets found in the file. No changes made.")

if __name__ == "__main__":
    main()
