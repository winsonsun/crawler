import os
import sys
import json
import math

def get_dynamic_entropy_limit():
    """
    Calculates the system's tolerance for technical debt (loose scripts) 
    based on the active Persona's DNA in the STATE_VECTOR.
    """
    vector_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'STATE_VECTOR.json'))
    
    # Absolute maximum loose scripts allowed before catastrophic failure
    ABSOLUTE_MAX_SCRIPTS = 20
    # Default fallback if state vector is missing/corrupted
    DEFAULT_LIMIT = 5 
    
    if not os.path.exists(vector_path):
        return DEFAULT_LIMIT, "Unknown Persona"

    try:
        with open(vector_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
        posture = state.get("active_posture", "Unknown")
        dna = state.get("identity_dna", {})
        
        # How much does the persona value clean, consolidated code? (0.0 to 1.0)
        metabolic_efficiency = dna.get("metabolic_efficiency", 0.5)
        
        # The equation: Higher efficiency = Lower tolerance for mess.
        # If efficiency is 0.9, tolerance is 10% of Max (2 scripts).
        # If efficiency is 0.2, tolerance is 80% of Max (16 scripts).
        calculated_limit = math.ceil(ABSOLUTE_MAX_SCRIPTS * (1.0 - metabolic_efficiency))
        
        # Ensure a minimum of 1 to allow at least one patch before forcing compression
        return max(1, calculated_limit), posture
        
    except Exception as e:
        print(f"Warning: Could not parse STATE_VECTOR DNA: {e}")
        return DEFAULT_LIMIT, "Corrupted Persona"

def main():
    basement_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'historical'))
    vector_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'STATE_VECTOR.json'))
    
    if not os.path.exists(basement_dir):
        print("✅ Basement is clean (directory does not exist).")
        sys.exit(0)

    # 1. Identify Active Sparks for Shielding
    active_sparks = []
    if os.path.exists(vector_path):
        with open(vector_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
            active_sparks = state.get("active_sparks", [])
            # Normalize sparks for easier matching (e.g., "Mycelial Network")
            active_sparks = [s.split('(')[0].strip().lower() for s in active_sparks]

    # 2. Evaluate Scripts and Check for Resonance
    py_files = [f for f in os.listdir(basement_dir) if f.endswith('.py')]
    debt_files = []
    shielded_files = []
    
    for f_name in py_files:
        full_path = os.path.join(basement_dir, f_name)
        is_resonant = False
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read(500) # Only check the header
                for spark in active_sparks:
                    if f"resonance: {spark}" in content.lower():
                        is_resonant = True
                        break
        except Exception: pass
        
        if is_resonant:
            shielded_files.append(f_name)
        else:
            debt_files.append(f_name)

    current_entropy = len(debt_files)
    
    # 3. Dynamically derive limit from the Persona's DNA
    entropy_limit, active_posture = get_dynamic_entropy_limit()
    
    if current_entropy >= entropy_limit:
        print("\n" + "="*80)
        print("🚨 [METABOLIC FATAL] BASEMENT ENTROPY LIMIT EXCEEDED 🚨")
        print("="*80)
        print(f"Active Posture: {active_posture}")
        print(f"Current Entropy: {current_entropy} (Debt) | Shielded: {len(shielded_files)} (Resonant)")
        print(f"Dynamic Limit: {entropy_limit} files")
        print(f"\nThe technical debt has breached the {active_posture}'s tolerance.")
        print(f"Note: {len(shielded_files)} scripts were shielded by Active Sparks.")
        print("\n[AI_DIRECTIVE] -> @GeminiCLI:")
        print("1. ABORT the current `reaction-simulator` task immediately.")
        print("2. Activate skill: `manifold-compressor` to consolidate the basement into `src/`.")
        print("="*80 + "\n")
        sys.exit(1)
    else:
        status_msg = f"✅ Metabolic State OK. Posture: {active_posture} | Entropy: {current_entropy}/{entropy_limit}"
        if shielded_files:
            status_msg += f" | Shielded: {len(shielded_files)}"
        print(status_msg)
        sys.exit(0)

if __name__ == "__main__":
    main()
