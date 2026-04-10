import os
import sys
import json
import argparse
from datetime import datetime
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def update_fossil_record(title, trigger, physics, constraint):
    date_str = datetime.now().strftime("%Y-%m-%d")
    record_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'FOSSIL_RECORD.md'))
    
    new_entry = f"\n## Scar: {date_str} {title}\n"
    new_entry += f"- **Trigger:** {trigger}\n"
    new_entry += f"- **Physics:** {physics}\n"
    new_entry += f"- **Constraint:** {constraint}\n"
    
    with open(record_path, 'a', encoding='utf-8') as f:
        f.write(new_entry)
    print(f"✅ Appended new scar to {record_path}")

def update_state_vector(title):
    vector_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'STATE_VECTOR.json'))
    slug = slugify(title)
    
    if os.path.exists(vector_path):
        with open(vector_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
        if "current_scars" not in state:
            state["current_scars"] = []
            
        if slug not in state["current_scars"]:
            state["current_scars"].append(slug)
            
            with open(vector_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            print(f"✅ Added '{slug}' to STATE_VECTOR.json")
    else:
        print(f"⚠️ STATE_VECTOR.json not found at {vector_path}")

def main():
    parser = argparse.ArgumentParser(description="Record an environmental scar.")
    parser.add_argument("--title", required=True, help="Short title of the failure/scar.")
    parser.add_argument("--trigger", required=True, help="What action triggered the failure?")
    parser.add_argument("--physics", required=True, help="What is the underlying rule/physics of the site causing this?")
    parser.add_argument("--constraint", required=True, help="What must the crawler do to survive this?")
    
    args = parser.parse_args()
    
    update_fossil_record(args.title, args.trigger, args.physics, args.constraint)
    update_state_vector(args.title)

if __name__ == "__main__":
    main()
