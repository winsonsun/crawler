---
name: reaction-simulator
description: Simulates "Reactionary Evolution" by generating surgical patches to overcome environmental constraints. Use when a new Scar is recorded in FOSSIL_RECORD.md and the codebase must adapt to survive.
---
# Reaction Simulator

This skill facilitates the "Reactionary Evolution" of the codebase. Instead of a top-down refactor, it generates surgical, minimal "Fix Scripts" (Python using `re.sub`) to mutate the code to survive new environmental constraints ("Scars").

## Core Workflow

1. **Analyze the Scar:** Read the most recent entries in `FOSSIL_RECORD.md`. Identify the "Physics" and "Constraint" that must be overcome.
2. **Identify the Target:** Locate the specific method, class, or logic in the codebase (e.g., `crawler.py`) that is failing.
3. **Draft the Mutation:** Adopt the "Pragmatic Architect" persona. Generate a Python "Fix Script" that surgically mutates the code.
    - **Rule 1:** Prefer `re.sub` for precise method replacement.
    - **Rule 2:** Maintain the "Body" of the code; only change what is required for survival.
    - **Rule 3:** The patch should be self-executing (read the file, apply regex, write the file).
4. **Validation:** Review the patch to ensure it addresses the Scar while maintaining the minimal delta.

## Output Standards

When the user asks to "React" to a scar:
1. Provide a brief explanation of how the patch overcomes the constraint.
2. Output the full content of the Python "Fix Script."
3. Instruct the user on how to run it.

Refer to [patch_examples.md](references/patch_examples.md) for common mutation patterns.
