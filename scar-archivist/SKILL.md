# Scar Archivist Skill

## Overview
The Scar Archivist is responsible for recording environmental failures, anti-bot measures, and data corruption events into the system's memory.

## 🛑 NEW MANDATE: Do not write Markdown manually.
You MUST NOT manually edit `FOSSIL_RECORD.md` or `STATE_VECTOR.json`. Manual edits cause formatting errors and metabolic drain.

## Execution Instructions
When a new failure is encountered, you MUST run the `record_scar.py` tool.

### Command Syntax:
```bash
python tools/record_scar.py \
  --title "Brief name of the issue (e.g., JavDB Cloudflare Block)" \
  --trigger "The action that caused the failure (e.g., Requesting /v/ endpoint)" \
  --physics "The underlying site rule (e.g., Turnstile requires JS execution)" \
  --constraint "The architectural fix required (e.g., Must use OmniSolver or headful profile)"
```

### Post-Execution
The script will automatically:
1. Format and append the entry to `FOSSIL_RECORD.md`.
2. Slugify the title and add it to the `current_scars` array in `STATE_VECTOR.json`.

After running the command, transition immediately to the `reaction-simulator` or `manifold-compressor` to resolve the recorded constraint.
