import os
import sys
import json
import re
import urllib.parse
import glob
from collections import defaultdict

CRAW_CONF = os.environ.get("CRAW_CONF", "./config")
CRAW_DATA = os.environ.get("CRAW_DATA", "./data")

# Add the scripts directory to the path so we can import RenameTool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rename_tool import RenameTool

def get_existing_ids(list_dir):
    """Collects all IDs already present in JSON files within list_dir."""
    existing_ids = set()
    if not os.path.exists(list_dir):
        print(f"[Info] List directory not found: {list_dir}. Skipping filtering.")
        return existing_ids

    json_files = glob.glob(os.path.join(list_dir, "*.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Recursively extract IDs from lists or dictionaries
                def extract(obj):
                    if isinstance(obj, str):
                        existing_ids.add(obj.strip().upper())
                    elif isinstance(obj, list):
                        for item in obj:
                            extract(item)
                    elif isinstance(obj, dict):
                        for key, value in obj.items():
                            # Add the key as an ID (some JSON files use IDs as keys)
                            existing_ids.add(str(key).strip().upper())
                            # Recurse into values to find more IDs (some use lists of IDs as values)
                            extract(value)

                extract(data)
        except Exception as e:
            print(f"[Warning] Failed to read {file_path}: {e}")
    
    print(f"Collected {len(existing_ids)} existing IDs from {len(json_files)} files.")
    return existing_ids

def main():
    input_txt = os.path.join(CRAW_DATA, "output", "to-be-downloaded.txt")
    output_json = os.path.join(CRAW_DATA, "output", "canonical_scene_id.json")
    list_dir = os.path.join(CRAW_DATA, "list")

    grouped_data = defaultdict(list)
    # Load existing IDs for filtering
    existing_ids = get_existing_ids(list_dir)

    if os.path.exists(input_txt):
        # 1. Read and remove duplicates from text file
        with open(input_txt, "r", encoding="utf-8") as f:
            lines = f.readlines()

        unique_records = []
        seen = set()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line not in seen:
                seen.add(line)
                unique_records.append(line)

        print(f"Found {len(lines)} total records in {input_txt}, {len(unique_records)} unique.")

        # 2. Rewrite the file to remove duplicates
        with open(input_txt, "w", encoding="utf-8") as f:
            for record in unique_records:
                f.write(record + "\n")
        print(f"Overwrote {input_txt} with unique records.")

        # 3. Process and group
        tool = RenameTool(config_path=os.path.join(CRAW_CONF, "rename_policy.json"))

        for record in unique_records:
            # Extract the 'dn' parameter
            dn_match = re.search(r"&dn=([^&]+)", record)
            if dn_match:
                raw_dn = dn_match.group(1)
                # URL Decode
                decoded_dn = urllib.parse.unquote(raw_dn)
                # Clean up literal backslashes escaping brackets sometimes found in magnets
                decoded_dn = decoded_dn.replace("\\[", "[").replace("\\]", "]")
                
                # Process using rename_tool
                canonical_id = tool.process_filename(decoded_dn)
                
                # Strip common file extensions to consolidate the IDs
                base, ext = os.path.splitext(canonical_id)
                if ext.lower() in [".mp4", ".mkv", ".avi", ".wmv"]:
                    canonical_id = base
            else:
                # Fallback if no dn parameter is found
                canonical_id = tool.process_filename(record)
                
                # Strip common file extensions for fallback as well
                base, ext = os.path.splitext(canonical_id)
                if ext.lower() in [".mp4", ".mkv", ".avi", ".wmv"]:
                    canonical_id = base
            
            # Filter: Skip if canonical_id is already downloaded
            if canonical_id.strip().upper() in existing_ids:
                continue
                
            grouped_data[canonical_id].append(record)
            
    elif os.path.exists(output_json):
        print(f"[Info] {input_txt} not found. Loading existing JSON: {output_json} for filtering.")
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                # Re-filter the existing data
                for cid, magnets in raw_data.items():
                    if cid.strip().upper() not in existing_ids:
                        grouped_data[cid] = magnets
        except Exception as e:
            print(f"[Error] Failed to load {output_json}: {e}")
            return
    else:
        print(f"[Error] Neither {input_txt} nor {output_json} was found.")
        return

    # 4. Write output
    output_data = dict(grouped_data)
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Final dataset contains {len(output_data)} canonical IDs (after filtering).")
    print(f"Output written to {output_json}")

if __name__ == "__main__":
    main()
