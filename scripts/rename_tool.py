import os
import sys
import json
import re
import argparse
import fnmatch

CRAW_CONF = os.environ.get("CRAW_CONF", "./config")
CRAW_DATA = os.environ.get("CRAW_DATA", "./data")

class RenameTool:
    def __init__(self, config_path=os.path.join(CRAW_CONF, "rename_policy.json"), rules=None):
        self.config_path = config_path
        self.rename_rules = rules
        if self.rename_rules is None:
            self.load_config()
        else:
            self.config = {"rename_rules": self.rename_rules}
        
        self.dry_run = self.config.get('settings', {}).get('dry_run', False)
        self.recursive = self.config.get('settings', {}).get('recursive', True)

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.config = {"rename_rules": [], "settings": {}}
            self.rename_rules = []
            return
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.rename_rules = self.config.get('rename_rules', [])

    def _generate_safe_path(self, target_path):
        """Generate a safe, non-colliding path."""
        if not os.path.exists(target_path):
            return target_path
        
        base, ext = os.path.splitext(target_path)
        counter = 1
        new_path = f"{base}_oo_{counter}{ext}"
        
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_oo_{counter}{ext}"
            
        return new_path

    def process_filename(self, filename):
        """Apply all renaming rules to a single filename string."""
        curr_name = filename
        renamed = False
        
        for rule in self.rename_rules:
            rtype = rule.get('type')
            patterns = rule.get('patterns', [])
            
            if rtype == 'strip_prefix':
                for p in patterns:
                    if curr_name.lower().startswith(p.lower()):
                        curr_name = curr_name[len(p):]
                        renamed = True
            elif rtype == 'regex_cut':
                for p in patterns:
                    tmp = re.sub(p, "", curr_name, count=1, flags=re.IGNORECASE)
                    if tmp != curr_name: 
                        curr_name = tmp
                        renamed = True
            elif rtype == 'replace':
                rules = rule.get('rules', [])
                for r in rules:
                    old = r.get('old')
                    new = r.get('new', '')
                    if old and old in curr_name:
                        curr_name = curr_name.replace(old, new)
                        renamed = True
            elif rtype == 'regex_replace':
                rules = rule.get('rules', [])
                for r in rules:
                    pattern = r.get('pattern')
                    replacement = r.get('replacement', '')
                    if pattern:
                        tmp = re.sub(pattern, replacement, curr_name, flags=re.IGNORECASE)
                        if tmp != curr_name:
                            curr_name = tmp
                            renamed = True
            elif rtype == 'uppercase':
                tmp = curr_name.upper()
                if tmp != curr_name:
                    curr_name = tmp
                    renamed = True
        
        # Cleanup: strip leading/trailing dots/spaces
        if renamed:
            curr_name = curr_name.strip('. ')
            
        return curr_name if renamed else filename

    def run(self, target_path):
        if not os.path.exists(target_path):
            print(f"[Error] Path not found: {target_path}")
            return

        if os.path.isfile(target_path):
            self._rename_file(os.path.dirname(target_path), os.path.basename(target_path))
        else:
            if self.recursive:
                for root, dirs, files in os.walk(target_path, topdown=False):
                    for f in files:
                        self._rename_file(root, f)
            else:
                for f in os.listdir(target_path):
                    if os.path.isfile(os.path.join(target_path, f)):
                        self._rename_file(target_path, f)

    def _rename_file(self, root, filename):
        new_name = self.process_filename(filename)
        
        if new_name != filename and new_name:
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_name)
            
            if os.path.exists(new_path):
                new_path = self._generate_safe_path(new_path)
                new_name = os.path.basename(new_path)
                print(f"  [Conflict] Target exists, redirecting to: {new_name}")

            if not self.dry_run:
                try:
                    os.rename(old_path, new_path)
                    print(f"[RENAMED] {filename} -> {new_name}")
                except OSError as e:
                    print(f"  [ERROR] Failed to rename {filename}: {e}")
            else:
                print(f"[DRY-RUN] Would rename: {filename} -> {new_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Filename Renaming Tool")
    parser.add_argument("path", help="Target path (file or directory) to process")
    parser.add_argument("--config", "-c", default=os.path.join(CRAW_CONF, "rename_policy.json"), help="Path to the JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Do not perform actual renaming")
    parser.add_argument("--no-recursive", action="store_false", dest="recursive", help="Do not process subdirectories")
    
    args = parser.parse_args()
    
    tool = RenameTool(args.config)
    if args.dry_run:
        tool.dry_run = True
    if not args.recursive:
        tool.recursive = False
        
    tool.run(args.path)
