import os
import json
from pathlib import Path

def rebuild_ain_list(target_path, output_file):
    """
    Scans the target directory and rebuilds the actor media list.
    Structure: target_path / ActressName / SceneID
    """
    actor_data = {}
    
    if not os.path.exists(target_path):
        print(f"[Error] Target path does not exist: {target_path}")
        return

    print(f"Scanning {target_path}...")
    
    # List actresses (Level 1 directories)
    try:
        actresses = [d for d in os.listdir(target_path) if os.path.isdir(os.path.join(target_path, d))]
    except OSError as e:
        print(f"[Error] Failed to list directory {target_path}: {e}")
        return

    for actress in actresses:
        actress_path = os.path.join(target_path, actress)
        actor_data[actress] = []
        
        # List Scene IDs (Level 2 directories)
        try:
            scene_ids = [d for d in os.listdir(actress_path) if os.path.isdir(os.path.join(actress_path, d))]
            actor_data[actress] = scene_ids
        except OSError as e:
            print(f"[Warning] Failed to list scenes for {actress}: {e}")
            continue

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(actor_data, f, ensure_ascii=False, indent=2)
        print(f"[Success] Rebuilt {output_file} with {len(actor_data)} actresses.")
    except Exception as e:
        print(f"[Error] Failed to write {output_file}: {e}")

if __name__ == "__main__":
    CRAW_DATA = os.environ.get("CRAW_DATA", "./data")
    TARGET = "/mnt/cig/video/ain"
    # We save to data/list/ain_list.json to match the project's refactored structure
    OUTPUT = os.path.join(CRAW_DATA, "list", "ain_list.json")
    
    rebuild_ain_list(TARGET, OUTPUT)
