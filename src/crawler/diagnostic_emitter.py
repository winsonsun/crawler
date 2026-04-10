import os
import json
import traceback
from datetime import datetime
import sys

def emit_fatal_scar(trigger: str, exception: Exception, html_snippet: str = None, exit_on_fatal: bool = False):
    """
    The Nervous System's pain receptor.
    When a fatal block occurs (Cloudflare, Missing DOM, etc.), this function:
    1. Dumps the traceback and context to data/diagnostics/latest_crash.json
    2. Emits a machine-readable string to stdout instructing the Gemini CLI to activate.
    """
    diagnostics_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'diagnostics'))
    os.makedirs(diagnostics_dir, exist_ok=True)
    crash_file = os.path.join(diagnostics_dir, 'latest_crash.json')
    
    error_type = type(exception).__name__
    error_msg = str(exception)
    tb = traceback.format_exc()
    
    diagnostic_data = {
        "timestamp": datetime.now().isoformat(),
        "trigger": trigger,
        "error_type": error_type,
        "error_message": error_msg,
        "traceback": tb,
        "html_snippet": html_snippet[:2000] if html_snippet else "None provided."
    }
    
    with open(crash_file, 'w', encoding='utf-8') as f:
        json.dump(diagnostic_data, f, indent=2)
        
    # The Machine-Readable CLI Trigger
    print("\n" + "="*80)
    print("🚨 [SYSTEM FATAL] ENVIRONMENTAL SCAR DETECTED 🚨")
    print("="*80)
    print(f"Trigger: {trigger}")
    print(f"Error: {error_type} - {error_msg}")
    print("\n[AI_DIRECTIVE] -> @GeminiCLI:")
    print(f"1. Read {crash_file}")
    print("2. Activate skill: scar-archivist to record this failure.")
    print("3. Activate skill: reaction-simulator to build the fix.")
    print("="*80 + "\n")
    
    if exit_on_fatal:
        sys.exit(1)
