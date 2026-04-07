import os
import sys
import json
import re
import requests
import glob
from pathlib import Path

CRAW_CONF = os.environ.get("CRAW_CONF", "./config")
CRAW_DATA = os.environ.get("CRAW_DATA", "./data")

# Import RenameTool from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rename_tool import RenameTool

def get_existing_ids_with_sizes(list_dir):
    """Collects all IDs and their sizes from JSON files within list_dir."""
    existing_data = {} # { "ID": size_mb }
    if not os.path.exists(list_dir):
        return existing_data

    json_files = glob.glob(os.path.join(list_dir, "*.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Structure: { "Actress": { "ID": size_mb } }
                if isinstance(data, dict):
                    for actress, scenes in data.items():
                        if isinstance(scenes, dict):
                            for scene_id, size in scenes.items():
                                existing_data[scene_id.strip().upper()] = size
        except Exception: pass
    return existing_data

class DelugeClient:
    def __init__(self, url, password):
        self.url = url.rstrip('/') + "/json"
        self.password = password
        self.session = requests.Session()
        self.request_id = 0

    def _call(self, method, params):
        self.request_id += 1
        payload = {"method": method, "params": params, "id": self.request_id}
        try:
            resp = self.session.post(self.url, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"[Error] Deluge API call failed: {e}")
            return None

    def login(self):
        result = self._call("auth.login", [self.password])
        return result and result.get("result") == True

    def get_torrents(self):
        # We request name, hash, total_size (bytes), and active_time (seconds)
        result = self._call("web.update_ui", [["name", "hash", "total_size", "active_time"], {}])
        if result and "result" in result and "torrents" in result["result"]:
            return result["result"]["torrents"]
        return {}

    def remove_torrents(self, hashes, remove_data=True):
        # core.remove_torrents takes [hashes_list, remove_data_bool]
        result = self._call("core.remove_torrents", [hashes, remove_data])
        return result

    def add_magnet(self, magnet_uri, options=None):
        # core.add_torrent_magnet takes [uri, options_dict]
        if options is None: options = {}
        result = self._call("core.add_torrent_magnet", [magnet_uri, options])
        return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Filter, delete, or upload torrents to Deluge.")
    parser.add_argument("--deletion-plan", action="store_true", help="Physically remove torrents identified in the deletion plan from the server.")
    parser.add_argument("--upload-new", action="store_true", help="Upload new magnet links from canonical_scene_id.json to the server.")
    args = parser.parse_args()

    # 1. Load Config
    config_path = os.path.join(CRAW_CONF, "crawler.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    deluge_url = config.get("deluge_url", "http://100.64.26.2:8112")
    deluge_pass = config.get("deluge_pass", "deluge")
    
    # 2. Connect to Deluge
    print(f"Connecting to Deluge at {deluge_url}...")
    client = DelugeClient(deluge_url, deluge_pass)
    if not client.login():
        print("[Error] Failed to login to Deluge. Check your password in config/crawler.json")
        return

    raw_torrents = client.get_torrents()
    print(f"Retrieved {len(raw_torrents)} torrents from Deluge.")

    # 3. Process names with RenameTool
    tool = RenameTool(config_path=os.path.join(CRAW_CONF, "rename_policy.json"))
    processed_list = []
    
    for t_hash, t_info in raw_torrents.items():
        name = t_info.get("name", "")
        # Convert total_size from bytes to Megabytes
        size_bytes = t_info.get("total_size", 0)
        size_mb = size_bytes / (1024 * 1024)
        active_time = t_info.get("active_time", 0) # in seconds
        
        canonical_id = tool.process_filename(name)
        # Strip extension
        base, _ = os.path.splitext(canonical_id)
        processed_list.append({
            "hash": t_hash,
            "name": name,
            "size_mb": size_mb,
            "active_time": active_time,
            "canonical_id": base.strip().upper()
        })

    # Save raw list
    output_dir = Path(CRAW_DATA) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    list_file = output_dir / "deluge_torrent_list.json"
    with open(list_file, "w", encoding="utf-8") as f:
        json.dump(processed_list, f, indent=2, ensure_ascii=False)
    print(f"Saved processed list to {list_file}")

    # 4. Filter against repository and apply Maintenance Rules
    threshold_mb = 500
    existing_ids_with_sizes = get_existing_ids_with_sizes(os.path.join(CRAW_DATA, "list"))
    print(f"Loaded {len(existing_ids_with_sizes)} IDs from local repository lists.")

    deletion_plan = []
    skipped_for_quality = []
    
    for item in processed_list:
        name_lower = item["name"].lower()
        size_mb = item["size_mb"]
        active_days = item["active_time"] / (24 * 3600)
        cid = item["canonical_id"]
        
        # RULE A: Duplicate/Archived Check
        is_archived = cid in existing_ids_with_sizes
        if is_archived:
            existing_size = existing_ids_with_sizes[cid]
            if existing_size < (size_mb - threshold_mb):
                skipped_for_quality.append({
                    "id": cid,
                    "existing": f"{existing_size:.0f}MB",
                    "deluge": f"{size_mb:.0f}MB",
                    "diff": f"{size_mb - existing_size:.0f}MB"
                })
                continue
            else:
                item["reason"] = "Already Archived"
                deletion_plan.append(item)
                continue

        # RULE B: Junk/Stale [javdb.com] Check
        # If name has [javdb.com], size < 100M, and active > 2 days
        if "[javdb.com]" in name_lower and size_mb < 100 and active_days > 2:
            item["reason"] = f"Stale Junk (<100MB, {active_days:.1f} days active)"
            deletion_plan.append(item)
            continue

    # 5. Output Results and Execute Plan
    plan_file = output_dir / "deluge_deletion_plan.json"
    
    if skipped_for_quality:
        print(f"\n[Quality Check] Keeping {len(skipped_for_quality)} torrents because Deluge version is >500MB larger than archived version:")
        for s in skipped_for_quality:
            print(f"  + [{s['id']}] Deluge: {s['deluge']} | Repo: {s['existing']} (Diff: {s['diff']})")

    if deletion_plan:
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(deletion_plan, f, indent=2, ensure_ascii=False)
        print(f"\n[ALERT] Found {len(deletion_plan)} torrents matching deletion criteria:")
        for item in deletion_plan:
            print(f"  - [{item['reason']}] {item['name']} ({item['size_mb']:.0f}MB)")
        
        if args.deletion_plan:
            import time
            batch_size = config.get("deluge_batch_size", 50)
            batch_delay = config.get("deluge_batch_delay", 2)
            
            print(f"\n>>> EXECUTING DELETION of {len(deletion_plan)} torrents (Batch size: {batch_size})...")
            
            hashes_to_remove = [item["hash"] for item in deletion_plan]
            
            # Process in batches
            for i in range(0, len(hashes_to_remove), batch_size):
                batch = hashes_to_remove[i:i + batch_size]
                print(f"  - Deleting batch {i//batch_size + 1} ({len(batch)} items)...")
                client.remove_torrents(batch, remove_data=True)
                if i + batch_size < len(hashes_to_remove):
                    time.sleep(batch_delay)
            
            print("Done. Torrents and data have been removed from the server.")
        else:
            print(f"\nDeletion plan saved to {plan_file}")
            print("Run with --deletion-plan to physically remove these from the server.")
    else:
        print("\n[Success] No redundant or stale torrents found in Deluge.")
        if plan_file.exists():
            plan_file.unlink()

    # 6. Upload New Magnets
    if args.upload_new:
        import time
        canonical_file = output_dir / "canonical_scene_id.json"
        if not canonical_file.exists():
            print(f"\n[Error] {canonical_file} not found. Run group_magnets.py first.")
            return

        with open(canonical_file, 'r', encoding='utf-8') as f:
            try:
                new_data = json.load(f)
            except Exception as e:
                print(f"[Error] Failed to parse {canonical_file}: {e}")
                return
            
        active_ids = {item["canonical_id"] for item in processed_list}
        batch_size = config.get("deluge_batch_size", 50)
        batch_delay = config.get("deluge_batch_delay", 2)
        
        print(f"\n>>> SCANNING FOR NEW MAGNETS (Batch size: {batch_size})...")
        
        uploaded_count = 0
        current_batch_count = 0
        
        for cid, magnets in new_data.items():
            cid_upper = cid.strip().upper()
            if cid_upper not in active_ids and cid_upper not in existing_ids_with_sizes:
                print(f"  + Uploading new magnets for {cid}:")
                for m_uri in magnets:
                    res = client.add_magnet(m_uri)
                    if res and res.get("result"):
                        print(f"    - Success: {m_uri[:60]}...")
                        uploaded_count += 1
                        current_batch_count += 1
                    else:
                        print(f"    - Failed to upload magnet for {cid}")
                    
                    # Flow control check
                    if current_batch_count >= batch_size:
                        print(f"  [Flow Control] Waiting {batch_delay}s before next batch...")
                        time.sleep(batch_delay)
                        current_batch_count = 0

        print(f"\nFinished uploading {uploaded_count} new magnet(s) to Deluge.")

if __name__ == "__main__":
    main()
