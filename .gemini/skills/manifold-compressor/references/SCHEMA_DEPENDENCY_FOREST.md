# System Data Schema Dependency Forest

This document maps the flow of data through the crawler system. It is organized as a dependency forest, illustrating how raw inputs (Intent) are transformed through physical environments (WWW) into raw extractions, and finally normalized into canonical Universal Schemas. 

*Rule of Cascading Change:* A change in a parent schema/node inherently breaks or forces an update to all downstream dependents. A change in a leaf node requires updating its upstream extractor.

## 1. Intent & Environment Schemas (The Roots)
*These schemas define "What we want" and "How we execute it." They are independent and feed into the pipeline.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`CLI_ConfigSchema`** | The parsed `argparse` execution configuration (phases, throttle, IO paths). | None (User Input) | Entire Pipeline Execution | Defines which streams (`search`, `parse`, `download`) are active. |
| **`IntentSchema`** | The specific IDs or search terms (e.g., `ABC-123`, `prefix`). | `CLI_ConfigSchema`, `ain_list.json` | `SearchQueryStream`, `ActiveScanList` | A change here alters the starting URLs generated. |
| **`PhysicsStateSchema`** | Browser profile, injected cookies (`existmag=all`), dynamic User-Agents. | None (Environment) | `RawHTML_Stream` (Network adapter) | Changes here directly impact the anti-bot failure rate (Triggering 403s/Challenges). |

## 2. Extraction & Transitory Schemas (The Trunk)
*These represent the raw, chaotic data pulled from the hostile web environment before normalization.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`RawHTML_Stream`** | The raw DOM string returned by `aiohttp` or `crawl4ai` + `OmniSolver`. | `IntentSchema`, `PhysicsStateSchema` | `RawSearchJSON_Schema`, `RawDetailJSON_Schema` | Any change in site UI/HTML breaks the downstream Extractors. |
| **`RawSearchJSON_Schema`** | Unnormalized search result list (Saved in `search_site/`). | `RawHTML_Stream` (via Search Extractor) | `MergeDetail_Operator`, `DiscoveryLoop` | Structure dictates how we find the detail page URL. |
| **`RawDetailJSON_Schema`** | Site-specific extracted details (Title, Cover, Actors, Magnets). | `RawHTML_Stream` (via Detail Extractor) | `UniversalMediaSchema`, `MergeDetail_Operator` | **High Fragility.** Changes here require updating `BaseSiteAdapter` mappings. |

## 3. Canonical Universal Schemas (The Canopy)
*These are the refined, normalized entities ("Single Truth") stored in the `data/` folder. They drive business value.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`UniversalMediaSchema`** | Canonical JSON (`data/media_detail/`) representing a single release. | `RawDetailJSON_Schema`, `MergeDetail_Operator` | `MagnetOutputList`, UI/Stash Tools | The central hub. Relies on accurate merging of search + detail data. |
| **`UniversalActorSchema`** | Canonical JSON (`data/actress/`) linking actor aliases and profiles. | `UniversalMediaSchema` (Actor Links), Wiki Extractors | `AliasMap` (`ain_list.json`) | Driven by media extraction; influences future `IntentSchema` queries. |
| **`MagnetOutputList`** | Filtered text file (`data/output/`) for downstream torrent clients (Deluge). | `UniversalMediaSchema` (Magnet objects) | External Downloaders | **Business Critical.** Requires accurate file size and 'uploaded date' from upstream. |

## 4. The Operator Stream (The Branches)
*These are the functional transformers that map one schema to the next.*

| Operator / Function | Transformation | Failure Mode / Edge Case |
| :--- | :--- | :--- |
| **`_fetch_soup_safe()`** | `PhysicsStateSchema` -> `RawHTML_Stream` | Blocked by CAPTCHA (Lying 200 OK); Timeout. |
| **`parse_from_text()`** | `RawHTML_Stream` -> `RawDetailJSON_Schema` | Silent Semantic Shift (extracts wrong data from changed HTML). |
| **`merge_detail()`** | `RawSearchJSON_Schema` + `RawDetailJSON_Schema` -> `UniversalMediaSchema` | Key mismatch; overwriting high-fidelity data with low-fidelity search data. |
| **`deluge_filter()`** | `UniversalMediaSchema` -> `MagnetOutputList` | Missing size/date fields causing filter bypass or false negatives. |