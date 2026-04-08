#!/usr/bin/env python3
import sys
import datetime
import os

def main():
    if len(sys.argv) != 5:
        print("Usage: python record_scar.py \"[Brief Title]\" \"[Trigger]\" \"[Physics]\" \"[Constraint]\"")
        sys.exit(1)

    title = sys.argv[1]
    trigger = sys.argv[2]
    physics = sys.argv[3]
    constraint = sys.argv[4]

    # Use the current working directory to find or create FOSSIL_RECORD.md
    file_path = os.path.join(os.getcwd(), "FOSSIL_RECORD.md")
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    scar_entry = f"""
## Scar: {date_str} {title}
- **Trigger:** {trigger}
- **Physics:** {physics}
- **Constraint:** {constraint}
"""
    
    try:
        # Check if file exists, if not create it with a header
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# The Fossil Record\n\nA ledger of environmental constraints, failures, and the physical rules of the sandbox.\n")
        
        # Append the new scar
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(scar_entry)
            
        print(f"Success: Scar '{title}' recorded in {file_path}")
    except Exception as e:
        print(f"Error: Failed to record scar. {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
