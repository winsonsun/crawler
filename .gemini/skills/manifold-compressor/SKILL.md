---
name: manifold-compressor
description: Performs "State Compression" by refactoring accumulated patches and monolith logic into clean, hierarchical representations. Use when technical debt (v-scripts) or monolith complexity exceeds the AI's context efficiency ("Basement Checkin" phase).
---
# Manifold Compressor

This skill manages "State Compression" and "Basement Refactoring." It reduces the dimensionality of the project by abstracting surgical patches into a clean, hierarchical architecture, optimizing the AI's context window.

## Core Workflow

1. **Detect Saturation:** Analyze code, data, and the **Project Workspace** for high volume of patches, "Flat Records," or scattered utility scripts.
2. **Representation Audit (Deep Re-evaluation):** 
    - **Fidelity Gap Analysis:** Identify missing visual data from the source.
    - **Entropy Audit:** Detect semantic overlap (e.g., raw strings vs. typed values).
    - **Project Workspace Audit:** Diagnose scattered scripts (e.g., loose `.py` files in root), misnamed folders, and logic duplication. Exclude the `data/` folder from structural refactoring.
    - **Business Alignment:** Rank data importance based on downstream tool usage (Deluge/Stash).
3. **Advanced Synthesis:**
    - **Semantic Deduplication:** Merge overlapping concepts into canonical typed fields.
    - **Pollution Scrubbing:** Use LLM to strip marketing "noise" that provides zero utility.
    - **Script Semantic Clustering:** Propose moving loose files into semantic domains (e.g., `scripts/debug/`, `tools/maintenance/`).
    - **Virtual Symlinks vs. Duplication:** For tools needing multi-context access, evaluate whether to use a wrapper script (Virtual Symlink) or duplicate the logic. Ask the user for preference if ambiguous.
    - **Feature Hoisting:** If a specific site adapter has a high-value field missing in others, update the Universal Schema.
4. **Automate the Migration:**
    - Use the LLM to generate a **Normalizer Agent** that surgically transforms the messy JSON.
    - Move "Fossil Data" (raw scrapes) to separate storage to keep the primary entity lean.
5. **Basement Checkin:** Finalize the refactor and restore AI context efficiency.
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
