---
name: scar-archivist
description: Detects and records environmental failures, anti-bot measures, and data corruption events into a FOSSIL_RECORD.md file. Use when a script fails, a site changes, or a new constraint is discovered.
---
# Scar Archivist

This skill operationalizes the "Living Territory" philosophy by recording environmental constraints and failures ("Scars") into a persistent `FOSSIL_RECORD.md` file. It stops treating errors as "bugs to be fixed" and treats them as "Physics rules of the sandbox."

## Core Workflow

1. **Analyze the Failure:** Review the user's provided error, stack trace, or description of the failure.
2. **Abstract the Physics:** Determine the underlying environmental rule that caused the failure (e.g., "JavBus implemented a new Turnstile CAPTCHA").
3. **Determine the Constraint:** Identify the boundary this places on the architecture (e.g., "Requests library is obsolete here; must use a headed browser or inject pre-solved cookies").
4. **Record the Scar:** Use the bundled `scripts/record_scar.py` to append the abstracted scar to the workspace's `FOSSIL_RECORD.md`.

## Output Standards

When analyzing a failure, do not immediately write code to fix it. Your job is to document the constraint first.

Reference the standard format for a scar in [scar_format.md](references/scar_format.md).

## Usage

To record a scar:
```bash
python scripts/record_scar.py "[Brief Title]" "[What action caused the failure]" "[The underlying environmental rule]" "[The boundary this places on the architecture]"
```
