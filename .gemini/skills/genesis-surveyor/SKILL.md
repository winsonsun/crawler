---
name: genesis-surveyor
description: Bootstraps new projects by decoding user intent, selecting architectural paradigms, and performing backoff-enabled environment discovery. Use this skill at the very beginning of a project or when a significant new feature/site is added to establish the "Constitution" (GEMINI.md, SCHEMA_DEPENDENCY_FOREST.md) and "Fossil Record" (Terrain Summary).
---

# Genesis Surveyor

The Genesis Surveyor is the "Phase 0" agent. It bridges the gap between a vague idea and a tactical implementation plan.

## Workflow

### 1. Intent Decoding
Unpack the user's prompt to understand the deep goals and tolerances.
- **Reference:** Use [intent-decoding.md](references/intent-decoding.md) to map keywords to values.
- **Action:** Summarize the "Critical Path" and "Tolerance Matrix" for the user.

### 2. Architectural Selection
Decide how the system should be built before writing code.
- **Reference:** Use [architectural-patterns.md](references/architectural-patterns.md) to select the vector.
- **Action:** Propose a paradigm (e.g., Async Pipeline, DDD) and justify it based on the decoded intent.

### 3. Terrain Mapping (Discovery)
Safely explore the environment without triggering anti-bot measures.
- **Script:** Use `scripts/safe_probe.py <url>` to check headers, status codes, and Cloudflare presence.
- **Action:** Generate a "Terrain Summary" that records latency, rate limits, and protection layers.

### 4. Artifact Generation
Formalize the findings into the project's permanent record.
- **GEMINI.md:** Update or create with the project's "Physics" (rules/mandates).
- **SCHEMA_DEPENDENCY_FOREST.md:** Draft the initial Pydantic/JSON schemas for the core entities.
- **FOSSIL_RECORD.md:** Record the first "Scars" based on the Terrain Mapping results.

## When to Stop
The Genesis Surveyor's job is done when:
1. The user approves the Architectural Direction.
2. The initial schemas are drafted.
3. The environment's basic constraints are documented.

Pass the baton to `scar-archivist` and `reaction-simulator` for tactical execution.
