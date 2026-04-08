---
name: reaction-simulator
description: Simulates "Reactionary Evolution" by generating surgical patches to overcome environmental constraints. Use when a new Scar is recorded in FOSSIL_RECORD.md and the codebase must adapt to survive.
---
# Reaction Simulator

This skill facilitates the "Reactionary Evolution" of the codebase. Instead of a top-down refactor, it generates surgical, minimal "Fix Scripts" (Python using `re.sub`) to mutate the code to survive new environmental constraints ("Scars").

## Core Workflow

1. **Analyze the Scar:** Read the most recent entries in `FOSSIL_RECORD.md`. Identify the "Physics" and "Constraint" that must be overcome.
    - **Cross-Site Intelligence:** Check if a similar scar exists for other sites. Prioritize "Transferable Physics" solutions (e.g., sharing common checkbox-bypass logic).
2. **Consult Schema Forest & Identify Target:** Read `SCHEMA_DEPENDENCY_FOREST.md`. Identify which Data Node or Operator is failing. Locate the specific method, class, or logic in the codebase (e.g., `crawler.py`) that corresponds to it. Use the Forest to map the "blast radius" (downstream dependents) of your proposed fix.
3. **Draft the Mutation:** Adopt the "Pragmatic Architect" persona. Generate a Python "Fix Script" that surgically mutates the code.
    - **Rule 1:** Prefer `re.sub` for precise method replacement.
    - **Rule 2:** Maintain the "Body" of the code; only change what is required for survival.
    - **Rule 3:** The patch should be self-executing (read the file, apply regex, write the file).
    - **Rule 4 (Reset Hierarchy):** Prioritize **History Preservation** and **Proactive Injection** over "Working from Zero." Only clear session data if explicitly required by the Scar's physics.
    - **Rule 5 (Locale Integrity):** Ensure the patch preserves popularity-based language preferences (e.g., Chinese/Japanese for Japan AV).
4. **Empirical Validation (Micro & Integration):** You are strictly forbidden from concluding the task without proving the patch works.
    - **Micro-Validation:** Write and execute a minimal debug script (e.g., `scripts/debug/test_patch.py`) to prove the error is gone.
    - **Semantic Integration:** Assert that the extracted payload contains **Business-Critical Data** (specifically checking for the implicit 'uploaded date' and sizes of magnet links).
    - **Cross-Site Regression Check:** If your patch modifies a "Shared Branch" Operator (as defined in `SCHEMA_DEPENDENCY_FOREST.md`), you MUST run a test on all other streams that depend on it to ensure you haven't broken existing pipelines.

## Output Standards

When the user asks to "React" to a scar:
1. Provide a brief explanation of how the patch overcomes the constraint.
2. Output the full content of the Python "Fix Script."
3. Provide the output of your Empirical Validation proving the fix and the semantic integrity of the data.

Refer to [patch_examples.md](references/patch_examples.md) for common mutation patterns.
