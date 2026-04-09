# User Intention Decoding Reference

This guide helps translate vague user prompts into structured technical requirements.

## 1. Value Matrix Extraction

Identify the primary and secondary values in the user request.

| Prompt Keyword | Primary Value | Technical Implication |
| :--- | :--- | :--- |
| "better local caching" | Data Immortality / Efficiency | Persistent storage (SQLite/JSON), hash-based deduplication, local file verification. |
| "categorize by stars" | Ontological Integrity | Entity relationships (Actor <-> Media), hierarchical metadata. |
| "fast/quick" | Throughput | Parallelization, optimized DOM parsing, minimal rendering. |
| "reliable/stable" | Resilience | Heavy error handling, retries, backoff, proxy rotation. |
| "beautiful/clean" | Aesthetic/Representational Efficiency | Minimalist schemas, consistent naming, semantic deduplication. |

## 2. Critical Path Identification

What is the one thing that *must* work for the project to be considered successful?

- **Identity:** Unique IDs for entities.
- **Availability:** Access to the raw data source.
- **Integrity:** Verification of downloaded assets (e.g., magnet hashes).

## 3. Tolerance Assessment

Determine what the system can afford to lose or compromise.

- **Compute Cost vs. Human Effort:** Is it okay to spend more on LLM tokens to avoid writing complex CSS selectors? (In this project, YES).
- **Latency vs. Accuracy:** Is it okay to wait for a 5-second backoff to ensure we don't get IP banned? (In this project, YES).
