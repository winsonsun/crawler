---
name: manifold-compressor
description: Performs "State Compression" by refactoring accumulated patches and monolith logic into clean, hierarchical representations. Use when technical debt (v-scripts) or monolith complexity exceeds the AI's context efficiency ("Basement Checkin" phase).
---
# Manifold Compressor

This skill manages "State Compression" and "Basement Refactoring." It reduces the dimensionality of the project by abstracting surgical patches into a clean, hierarchical architecture, optimizing the AI's context window.

## Core Workflow

1. **Detect Saturation:** Analyze the project for a high volume of `v-scripts`, overgrown methods in `crawler.py`, or repeated logic.
2. **Abstract Business Logic:** Distinguish between the "Universal Procedure" (what we want to do) and "Environmental Hacks" (how we survive the site).
3. **Execute the "Basement Checkin":**
    - **Move Site Logic:** Extract site-specific CSS selectors and bypasses to `src/crawler/sites/`.
    - **Extract Shared Library:** Move generic functions (lock management, HTTP headers) to `src/crawler/lib/`.
    - **Generalize Adapters:** Ensure all site-specific logic follows the common `BaseSiteAdapter` interface.
4. **Prune History:** Consolidate `FOSSIL_RECORD.md` summaries and clean up the `historical/` folder to restore AI context efficiency.

## Output Standards

When performing a "Basement Checkin":
1. Provide a "Refactor Blueprint" listing the proposed file moves and structural changes.
2. Maintain all "Survival Traits" (the anti-bot bypasses and locks) from the original patches.
3. Consolidate the `FOSSIL_RECORD.md` to reflect the new architecture.

Refer to [refactor_patterns.md](references/refactor_patterns.md) for architectural templates.
