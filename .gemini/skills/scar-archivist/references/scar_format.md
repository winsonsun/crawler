# Scar Format

All entries in the `FOSSIL_RECORD.md` file must strictly adhere to the following Markdown format to ensure consistency and readability for both humans and AI agents.

## Schema

```markdown
## Scar: [YYYY-MM-DD] [Brief Title]
- **Trigger:** [A short description of what action caused the failure]
- **Physics:** [The underlying environmental rule or reason for the failure]
- **Constraint:** [The boundary this places on the architecture or the required adaptation strategy]
```

## Example

```markdown
## Scar: 2026-04-08 Cloudflare Turnstile Modal on JavDB
- **Trigger:** Accessing the `/search` endpoint on JavDB.
- **Physics:** Simple HTTP requests return a 403 Forbidden. JavaScript evaluation is required, and a hidden checkbox must be clicked to bypass the challenge.
- **Constraint:** The lightweight `aiohttp` fast-path is obsolete for this endpoint. We must incur the memory/CPU cost of `crawl4ai` or Playwright to evaluate the JS and inject cookies. Time-to-first-byte is delayed by 3-5 seconds.
```