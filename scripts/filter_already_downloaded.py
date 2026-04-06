import os
import json
import glob

def filter_already_downloaded():
    CRAW_DATA = os.environ.get("CRAW_DATA", "./data")
    list_dir = os.path.join(CRAW_DATA, "list")
    output_file = os.path.join(CRAW_DATA, "output", "canonical_scene_id.json")

    if not os.path.exists(output_file):
        print(f"[Info] Output file not found: {output_file}. Nothing to filter.")
        return

    if not os.path.exists(list_dir):
        print(f"[Info] List directory not found: {list_dir}. Skipping filtering.")
        return

    # 1. Collect all already downloaded IDs from the repository files
    downloaded_ids = set()
    json_files = glob.glob(os.path.join(list_dir, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # If data is a list, assume each item is an ID
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, str):
                            downloaded_ids.add(item.strip().upper())
                        elif isinstance(item, dict) and "id" in item:
                            downloaded_ids.add(str(item["id"]).strip().upper())
                
                # If data is a dict, assume keys are IDs
                elif isinstance(data, dict):
                    for key in data.keys():
                        downloaded_ids.add(str(key).strip().upper())
                        
            print(f"Loaded IDs from: {file_path}")
        except Exception as e:
            print(f"[Error] Failed to read {file_path}: {e}")

    print(f"Total unique repository IDs collected: {len(downloaded_ids)}")

    # 2. Load the canonical_scene_id.json and filter it
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            canonical_data = json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load {output_file}: {e}")
        return

    original_count = len(canonical_data)
    
    # Filter the dictionary: remove keys that exist in downloaded_ids
    # We do a case-insensitive match for the filter
    filtered_data = {
        key: value for key, value in canonical_data.items() 
        if key.strip().upper() not in downloaded_ids
    }
    
    removed_count = original_count - len(filtered_data)
    
    if removed_count > 0:
        # 3. Save the filtered results back to the file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            print(f"Filtered {removed_count} IDs that were already in the repository.")
            print(f"Remaining IDs to download: {len(filtered_data)}")
        except Exception as e:
            print(f"[Error] Failed to save filtered data to {output_file}: {e}")
    else:
        print("No IDs were found in the repositories. No changes made.")

if __name__ == "__main__":
    filter_already_downloaded()
