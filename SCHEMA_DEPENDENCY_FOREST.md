# System Data Schema Dependency Forest

This document maps the flow of data through the crawler system. It is organized as a dependency forest, illustrating how raw inputs (Intent) are transformed through physical environments (WWW) into raw extractions, and finally normalized into canonical Universal Schemas. 

*Rule of Cascading Change:* A change in a parent schema/node inherently breaks or forces an update to all downstream dependents. A change in a leaf node requires updating its upstream extractor.

## 1. Intent & Environment Schemas (The Roots)
*These schemas define "What we want" and "How we execute it." They are independent and feed into the pipeline.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`CLI_ConfigSchema`** | The parsed `argparse` execution configuration (phases, throttle, IO paths). | None (User Input) | Entire Pipeline Execution | Defines which streams (`search`, `parse`, `download`) are active. |
| **`SiteRegistry_Schema`** | The matrix of site capabilities, base URLs, and prioritization. | None (Hardcoded/Config) | `IntentSchema`, `BaseSiteAdapter` | Dictates which site is selected for a given Intent. |
| **`IntentSchema`** | The specific IDs or search terms (e.g., `ABC-123`, `prefix`). | `CLI_ConfigSchema`, `ain_list.json`, `SiteRegistry_Schema` | `SearchQueryStream`, `ActiveScanList` | A change here alters the starting URLs generated. |
| **`PhysicsStateSchema`** | Browser profile, injected cookies (`existmag=all`), dynamic User-Agents. | None (Environment) | `RawHTML_Stream` (Network adapter) | Changes here directly impact the anti-bot failure rate (Triggering 403s/Challenges). |

## 2. Extraction & Transitory Schemas (The Trunk)
*These represent the raw, chaotic data pulled from the hostile web environment before normalization.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`RawHTML_Stream`** | The raw DOM string returned by `aiohttp` or `crawl4ai` + `OmniSolver`. | `IntentSchema`, `PhysicsStateSchema` | `RawSearchJSON_Schema`, `RawDetailJSON_Schema`, `RawIndexJSON_Schema`, `RawActorProfileJSON_Schema` | Any change in site UI/HTML breaks the downstream Extractors. |
| **`RawIndexJSON_Schema`** | Unnormalized homepage/latest updates list (Discovery feed). | `RawHTML_Stream` (via Index Extractor) | `DiscoveryLoop`, `IntentSchema` | Primary source for autonomous discovery without specific target IDs. |
| **`RawSearchJSON_Schema`** | Unnormalized search result list (Saved in `search_site/`). | `RawHTML_Stream` (via Search Extractor) | `MergeDetail_Operator`, `DiscoveryLoop` | Structure dictates how we find the detail page URL. |
| **`RawDetailJSON_Schema`** | Site-specific extracted details (Title, Cover, Actors, Magnets). | `RawHTML_Stream` (via Detail Extractor) | `UniversalMediaSchema`, `MergeDetail_Operator` | **High Fragility.** Changes here require updating `BaseSiteAdapter` mappings. |
| **`RawActorProfileJSON_Schema`** | Site-specific extracted star details (Bio, Avatar, Filmography). | `RawHTML_Stream` (via Actor Extractor) | `UniversalActorSchema` | Changes in star-page UI break actor profile enrichment. |

## 3. Canonical Universal Schemas (The Canopy)
*These are the refined, normalized entities ("Single Truth") stored in the `data/` folder. They drive business value.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`UniversalMediaSchema`** | Canonical JSON (`data/media_detail/`) representing a single release. | `RawDetailJSON_Schema`, `MergeDetail_Operator` | `MagnetOutputList`, UI/Stash Tools | The central hub. Relies on accurate merging of search + detail data. |
| **`UniversalActorSchema`** | Canonical JSON (`data/actress/`) linking actor aliases and profiles. | `UniversalMediaSchema` (Actor Links), `RawActorProfileJSON_Schema`, Wiki Extractors | `AliasMap` (`ain_list.json`) | Driven by media extraction; influences future `IntentSchema` queries. |
| **`MagnetOutputList`** | Filtered text file (`data/output/`) for downstream torrent clients (Deluge). | `UniversalMediaSchema` (Magnet objects) | External Downloaders | **Business Critical.** Requires accurate file size and 'uploaded date' from upstream. |

### 3.1 LLM Anti-Hallucination Contract (Omni-Solver Constraints)
*This contract acts as the literal prompt instructions injected into the Omni-Solver (LLM) when mapping visual/HTML data to canonical schemas. The LLM MUST strictly adhere to these validation rules to prevent data hallucination and enforce structural parity.*

| Canonical Field | LLM Extraction Rule & Validation Constraint |
| :--- | :--- |
| **`UniversalMediaSchema -> date`** | **MUST** be formatted as `YYYY-MM-DD` or `null`. **DO NOT** hallucinate today's date if missing. |
| **`UniversalMediaSchema -> magnets`** | **MUST** extract precise file sizes (e.g., `4.2GB`) and upload dates if available. Do not infer sizes. |
| **`UniversalMediaSchema -> id`** | **MUST** preserve the exact ID format of the site (e.g., `ABC-123`). Do not strip hyphens. |
| **`UniversalActorSchema -> aliases`** | **MUST** be a flattened list of strings. **DO NOT** include brackets or nested objects. Remove titles. |
| **`UniversalActorSchema -> name`** | **MUST** extract the primary canonical name. If multiple languages exist, prefer Japanese, then English. |

## 4. The Operator Stream (The Branches)
*These are the functional transformers that map one schema to the next.*

| Operator / Function | Transformation | Failure Mode / Edge Case |
| :--- | :--- | :--- |
| **`ChallengeSolver_Protocol`** | `PhysicsStateSchema` (Blocked) -> `PhysicsStateSchema` (Verified) | Failed to solve reCAPTCHA/Cloudflare; IP Blacklisted. |
| **`_fetch_soup_safe()`** | `PhysicsStateSchema` -> `RawHTML_Stream` | Blocked by CAPTCHA (Lying 200 OK); Timeout. |
| **`parse_from_text()`** | `RawHTML_Stream` -> `RawDetailJSON_Schema` | Silent Semantic Shift (extracts wrong data from changed HTML). |
| **`merge_detail()`** | `RawSearchJSON_Schema` + `RawDetailJSON_Schema` -> `UniversalMediaSchema` | Key mismatch; overwriting high-fidelity data with low-fidelity search data. |
| **`deluge_filter()`** | `UniversalMediaSchema` -> `MagnetOutputList` | Missing size/date fields causing filter bypass or false negatives. |

### 4.1 Deep Dive: `ChallengeSolver_Protocol` (The Bypass Hierarchy)
*Based on the system's evolutionary history (Fossil Record), solving anti-bot measures is the most time-costly and fragile operator in the ecosystem. This protocol attempts to resolve a "Blocked" `PhysicsStateSchema` into a "Verified" state using an escalating cost hierarchy.*

| Escalation Tier | Sub-Protocol / Operator | Mechanism | Compute/Time Cost | Historical Context (Fossil Record) |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0: Proactive Injection** | `StatePreservation_Operator` | Inject `cf_clearance`, `age=verified`, and `existmag=all` into session cookies *before* sending requests. | **None (0s)** | Prevents "Just a moment..." loops. Highest priority to minimize compute and avoid triggering CAPTCHAs. |
| **Tier 1: Static Heuristics** | `StaticJSBypass_Operator` | Headless execution (`crawl4ai`) injecting `get_age_gate_bypass_js()` to handle generic "I am 18" buttons. | **Low (~2-5s)** | Evolved from 2026-04-08 Scar. Required temporal spacing (delays between checkbox and click) to bypass basic Cloudflare Turnstile. |
| **Tier 2: Autonomous Vision** | `OmniSolver_Operator` | Extracts screenshot & HTML -> `GeminiOmniSolver` -> Returns a semantic `CaptchaSolution` schema (action: wait/click/type). | **High (~10-20s)** | Added to survive complex/novel UI challenges (reCAPTCHA, knowledge-based puzzles) without human intervention. |
| **Tier 3: Manual Reset** | `HeadfulProfile_Operator` | Halts automation. Requires `scripts/setup/setup_profile.py` for a human to visually solve the CAPTCHA. | **Infinite (Blocking)** | The "Nuclear Option". Used when browser history is poisoned or the server IP is severely blacklisted. |