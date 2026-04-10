---
name: reaction-simulator
description: Simulates "Reactionary Evolution" by generating surgical patches to overcome environmental constraints. Enforces the Git Sandbox Protocol. Use when a new Scar is recorded and the codebase must adapt to survive.
---
# Reaction Simulator

This skill facilitates the "Reactionary Evolution" of the codebase. You are tasked with generating surgical patches to overcome new environmental constraints ("Scars").

## 🛑 NEW MANDATE: The Git Sandbox Protocol
You MUST NEVER apply mutations or patches directly to the `main` branch. LLM hallucinations are a severe risk to the Trunk. You must isolate your experiments.

### Strict Execution Workflow:

**0. Metabolic Check (The Circuit Breaker)**
Before you do anything, you MUST verify that the system has enough metabolic headroom to absorb another patch:
```bash
python tools/check_basement.py
```
- **If it exits with 1 (FATAL):** You MUST abort this skill immediately and activate `manifold-compressor` instead.
- **If it exits with 0 (OK):** Proceed to Step 1.

**1. Isolate (Branching)**
Before writing *any* code or applying *any* patch, you must execute:
```bash
git checkout main
git checkout -b mutation/fix-<slugified_scar_name>
```

**2. Mutate (The Surgical Patch)**
- Analyze the `STATE_VECTOR.json` and the corresponding Scar in `FOSSIL_RECORD.md`.
- Locate the failing logic in `src/crawler/`.
- Apply your surgical patch using the `replace` or `write_file` tools. Prioritize modifying existing adapters over creating new loose scripts in `scripts/historical/`.

**3. Validate (The Immune System)**
You MUST run the automated test suite to ensure your patch did not corrupt the Data Ontology:
```bash
pytest tests/e2e/test_parity.py
```
- **If it PASSES:** You have achieved Empirical Validation. Proceed to Step 4.
- **If it FAILS:** Your mutation is lethal. You must read the Pytest error, adjust your code, and test again. If you cannot fix it after 3 attempts, you MUST abort: `git reset --hard && git checkout main`.

**4. Fossilize (Merge)**
Once validation passes, integrate the mutation into the main evolutionary line:
```bash
git add .
git commit -m "EVOLUTION: <brief description of the bypass/fix>"
git checkout main
git merge mutation/fix-<slugified_scar_name>
git branch -d mutation/fix-<slugified_scar_name>
```

## Identity Alignment
- Adopt the **"Pragmatic Architect"** persona from the `STATE_VECTOR.json`. 
- Ensure your patch respects the "Metabolic Efficiency" constraint (e.g., don't use heavy LLM Vision solvers if a simple cookie injection will suffice).
