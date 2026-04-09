---
name: manifold-compressor
description: Performs "State Compression" by refactoring accumulated patches and monolith logic into clean, hierarchical representations. Use when technical debt (v-scripts) or monolith complexity exceeds the AI's context efficiency ("Basement Checkin" phase).
---
# Manifold Compressor

This skill manages "State Compression" and "Basement Refactoring." It reduces the dimensionality of the project by abstracting surgical patches into a clean, hierarchical architecture, optimizing the AI's context window.

## Core Workflow

1. **Pre-flight Baseline & Schema Review:** Read `SCHEMA_DEPENDENCY_FOREST.md`. Identify the Canonical Universal Schemas (The Canopy) you are protecting. Before any compression, generate and save the JSON output hash of a known, representative entity using the current (old) architecture.
2. **Detect Saturation:** Analyze code, data, and the **Project Workspace** for high volume of patches, "Flat Records," or scattered utility scripts.
3. **Representation Audit (Deep Re-evaluation):** 
    - **Fidelity Gap Analysis:** Identify missing visual data from the source.
    - **Entropy Audit:** Detect semantic overlap (e.g., raw strings vs. typed values).
    - **Project Workspace Audit:** Diagnose scattered scripts (e.g., loose `.py` files in root), misnamed folders, and logic duplication. Exclude the `data/` folder from structural refactoring.
    - **Business Alignment:** Rank data importance based on downstream tool usage (Deluge/Stash).
    - **Impact Analysis:** Consult `SCHEMA_DEPENDENCY_FOREST.md` to trace the cascade of your refactor. Evaluate if modifying an Operator breaks multiple downstream streams.
4. **Advanced Synthesis:**
    - **Persona Preservation:** Verify that "Logical Personas" (e.g., the China Driver License expert or specific sequenced click logic) are not stripped away as "redundant code."
    - **Semantic Deduplication:** Merge overlapping concepts into canonical typed fields.
    - **Protocol Synthesis:** When auditing the FOSSIL_RECORD.md or analyzing multiple reactionary scripts, do not just merge the code. You must synthesize the underlying environmental constraints into a named Protocol (e.g., if you see 3 scripts bypassing Cloudflare in different ways, you must define an overarching ChallengeSolver_Protocol that ranks these bypasses by cost). You must then enforce this Protocol as a permanent architectural boundary.
    - **Pollution Scrubbing:** Use LLM to strip marketing "noise" that provides zero utility.
    - **Script Semantic Clustering:** Propose moving loose files into semantic domains (e.g., `scripts/debug/`, `tools/maintenance/`).
    - **Virtual Symlinks vs. Duplication:** For tools needing multi-context access, evaluate whether to use a wrapper script (Virtual Symlink) or duplicate the logic. Ask the user for preference if ambiguous.
    - **Feature Hoisting:** If a specific site adapter has a high-value field missing in others, update the Universal Schema.
5. **Automate the Migration:**
    - Use the LLM to generate a **Normalizer Agent** that surgically transforms the messy JSON.
    - Move "Fossil Data" (raw scrapes) to separate storage to keep the primary entity lean.
6. **Basement Checkin & Macro-Validation:** Finalize the refactor.
    - **Move Site Logic:** Extract site-specific CSS selectors and bypasses to `src/crawler/sites/`.
    - **Extract Shared Library:** Move generic functions (lock management, HTTP headers) to `src/crawler/lib/`.
    - **Generalize Adapters:** Ensure all site-specific logic follows the common `BaseSiteAdapter` interface.
    - **Hash Parity Check (CRITICAL):** Run the scrape for the baseline entity using the *new* architecture. If the resulting data hash does not match the baseline hash from Step 1, the compression is invalid and must be corrected or rolled back.
7. **Prune History:** Consolidate `FOSSIL_RECORD.md` summaries and clean up the `historical/` folder to restore AI context efficiency.

## Output Standards

When performing a "Basement Checkin":
1. Provide a "Refactor Blueprint" listing the proposed file moves and structural changes.
2. Maintain all "Survival Traits" (the anti-bot bypasses and locks) from the original patches.
3. Consolidate the `FOSSIL_RECORD.md` to reflect the new architecture.

Refer to [refactor_patterns.md](references/refactor_patterns.md) for architectural templates.
