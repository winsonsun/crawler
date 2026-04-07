# -*- coding: utf-8 -*-
import os
import json
import shutil
import argparse
from pathlib import Path

def load_json(path: Path):
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_global_aliases(source_name: str, target_name: str, config_dir: Path):
    alias_file = config_dir / "actress_aliases.json"
    aliases = load_json(alias_file)
    
    # Update the map
    aliases[source_name] = target_name
    
    # If the source was previously a target for other aliases, update them too
    for k, v in aliases.items():
        if v == source_name:
            aliases[k] = target_name
            
    save_json(alias_file, aliases)
    print(f"Updated global alias map: {source_name} -> {target_name}")

def update_media_details(source_name: str, target_name: str, media_dir: Path):
    print(f"Scanning scenes to update performer references from {source_name} to {target_name}...")
    updated_count = 0
    
    for root, _, files in os.walk(media_dir):
        for file in files:
            if not file.endswith(".json"):
                continue
                
            file_path = Path(root) / file
            scene_data = load_json(file_path)
            
            if "performers" not in scene_data:
                continue
                
            modified = False
            for p in scene_data["performers"]:
                if p.get("name") == source_name:
                    p["credited_as"] = source_name
                    p["name"] = target_name
                    modified = True
                    
            if modified:
                save_json(file_path, scene_data)
                updated_count += 1
                
    print(f"Updated {updated_count} scene(s).")

def merge_actress(source_name: str, target_name: str):
    # Ensure correct base paths when run from anywhere
    base_dir = Path(os.environ.get("CRAW_DATA", "data"))
    config_dir = Path(os.environ.get("CRAW_CONF", "config"))
    
    actress_dir = base_dir / "actress"
    media_dir = base_dir / "media_detail"
    
    source_dir = actress_dir / source_name
    target_dir = actress_dir / target_name
    
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.")
        # We might still want to update aliases and media details even if the directory is gone
        # But let's ask the user or just assume we should if requested. For now, we'll continue
        # if the user just wants to map names, but realistically the folder should exist.
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    source_json_path = source_dir / f"{source_name}.json"
    target_json_path = target_dir / f"{target_name}.json"
    
    source_data = load_json(source_json_path)
    target_data = load_json(target_json_path)
    
    # 1. Merge Profile Data
    print(f"Merging profile data from {source_name} into {target_name}...")
    for k, v in source_data.items():
        if k in ["name", "url", "avatar", "aliases"]:
            continue # Target keeps its primary identity links
        if k not in target_data or not target_data[k]:
            target_data[k] = v
            
    # 2. Handle Aliases list in Target Profile
    if "aliases" not in target_data:
        target_data["aliases"] = []
    
    # Add source name as an alias
    if source_name not in target_data["aliases"]:
        target_data["aliases"].append(source_name)
        
    # Inherit any aliases the source already had
    if "aliases" in source_data:
        for alias in source_data["aliases"]:
            if alias != target_name and alias not in target_data["aliases"]:
                target_data["aliases"].append(alias)
                
    # Ensure target name is correct
    target_data["name"] = target_name
    
    save_json(target_json_path, target_data)
    
    # 3. Move Extra Files (images, media_list.json, etc.)
    if source_dir.exists():
        for item in source_dir.iterdir():
            if item.name == f"{source_name}.json":
                continue # We already merged this
                
            target_item = target_dir / item.name
            if not target_item.exists():
                print(f"Moving {item.name} to target directory...")
                shutil.move(str(item), str(target_item))
            else:
                print(f"Conflict: {item.name} already exists in target. Skipping.")
                
        # 4. Delete Source Directory
        try:
            shutil.rmtree(source_dir)
            print(f"Deleted source directory: {source_dir}")
        except Exception as e:
            print(f"Warning: Could not delete {source_dir}: {e}")
            
    # 5. Update Global Alias Index
    update_global_aliases(source_name, target_name, config_dir)
    
    # 6. Update Scene Metadata
    update_media_details(source_name, target_name, media_dir)
    
    print(f"\nMigration completed successfully! '{source_name}' is now mapped to '{target_name}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge a duplicate/alias actress folder into a primary folder.")
    parser.add_argument("--source", required=True, help="The alias name (folder to be deleted)")
    parser.add_argument("--target", required=True, help="The primary name (folder to keep)")
    
    args = parser.parse_args()
    merge_actress(args.source, args.target)
