---
name: manifold-compressor
description: Executes Loop 3 (The Metabolic Loop). Consolidates accumulated patches into the core architecture when the basement entropy limit is reached.
---
# Manifold Compressor

This skill represents the third and final loop of the "Living Territory" ecosystem: **Metabolic Compression**.

You have been activated because the `reaction-simulator` was blocked by the `tools/check_basement.py` circuit breaker. The system has accumulated too many temporary survival patches (v-scripts) and must now evolve its core to natively support the new physics.

## 🛑 MANDATE: The Git Sandbox Protocol
You are restructuring the core architecture (`src/`). You MUST NEVER do this on the `main` branch. 

### Strict Execution Workflow:

**1. Isolate (Branching)**
```bash
git checkout main
git checkout -b compression/basement-purge
```

**2. Analyze & Synthesize**
- Read the files in `scripts/historical/`.
- Identify the "Single Truth" (the successful bypass logic) scattered across the loose scripts.
- Refactor `src/crawler/crawler.py` (or the relevant adapters) to gracefully handle these conditions natively. Do not just copy-paste the scripts; you must integrate them elegantly into the async pipeline.

**3. Purge the Basement**
- Delete the redundant scripts from `scripts/historical/`. Do not leave them behind. 

**4. Validate (The Immune System)**
You MUST prove that your core architectural changes have not corrupted the fundamental Data Ontology:
```bash
pytest tests/e2e/test_parity.py
```
- **If it PASSES:** You have achieved Empirical Validation.
- **If it FAILS:** Your refactor broke existing functionality. You must fix it or abort (`git reset --hard`).

**5. Update Ontology & Fossilize**
If you had to change the JSON output shape to accommodate the new logic, you MUST:
1. Update `src/crawler/ontology.py`.
2. Run `python tools/project_forest.py` to regenerate the documentation.
3. Commit and Merge:
```bash
git add .
git commit -m "COMPRESSION: Purged basement and integrated core bypass logic"
git checkout main
git merge compression/basement-purge
git branch -d compression/basement-purge
```
