# System Data Schema Dependency Forest

This document maps the flow of data through the crawler system. It is organized as a dependency forest, illustrating how raw inputs (Intent) are transformed through physical environments (WWW) into raw extractions, and finally normalized into canonical Universal Schemas. 

*Rule of Cascading Change:* A change in a parent schema/node inherently breaks or forces an update to all downstream dependents. A change in a leaf node requires updating its upstream extractor.

## 1. Intent & Environment Schemas (The Roots)
*These schemas define "What we want" and "How we execute it." They are independent and feed into the pipeline.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`CLI_ConfigSchema`** | The parsed `argparse` execution configuration. | None | Entire Pipeline | Defines active streams. |
| **`SiteRegistry_Schema`** | The matrix of site capabilities. | None | `IntentSchema` | Dictates site selection. |
| **`IntentSchema`** | Target IDs or search terms. | `CLI_ConfigSchema` | `SearchQueryStream` | Alters starting URLs. |
| **`PhysicsStateSchema`** | Browser profile, injected cookies, UAs. | None | `RawHTML_Stream` | Impacts anti-bot failure rate. |

## 2. Extraction & Transitory Schemas (The Trunk)
*Raw data pulled from the hostile web environment before normalization.*

| Schema / Data Node | Purpose | Upstream Dependencies | Downstream Dependents | Triggers / Influences |
| :--- | :--- | :--- | :--- | :--- |
| **`RawHTML_Stream`** | Raw DOM string. | `IntentSchema` | Raw Extractors | Any UI change breaks downstream. |
| **`RawDetailJSON_Schema`** | Site-specific extracted details. | `RawHTML_Stream` | `UniversalMediaSchema` | **High Fragility.** |
| **`RawActorProfileJSON_Schema`** | Site-specific star details. | `RawHTML_Stream` | `UniversalActorSchema` | UI changes break actor profiles. |

## 3. Canonical Universal Schemas (The Canopy)
*These are the refined, normalized entities stored in `data/`. Driven by `src/crawler/ontology.py`. DO NOT EDIT BY HAND.*

### UniversalMediaSchema
*Trunk Node: Canonical representation of a single release (data/media_detail/).*

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `<class 'str'>` | The exact ID format of the site (e.g., ABC-123). Do not strip hyphens. |
| `title` | `<class 'str'>` | Full title of the release |
| `date` | `Optional[str]` | Formatted as YYYY-MM-DD or null. DO NOT hallucinate today's date if missing. |
| `cover` | `Optional[str]` | URL to the primary cover image |
| `performers` | `List[src.crawler.ontology.Performer]` | List of recognized performers |
| `magnets` | `List[src.crawler.ontology.Magnet]` | List of physical file releases |

### UniversalActorSchema
*Trunk Node: Canonical JSON representing an actor's aliases and profile (data/actress/).*

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `<class 'str'>` | Canonical internal Actor ID |
| `name` | `<class 'str'>` | Primary actor name |
| `aliases` | `List[str]` | Flattened list of string aliases. DO NOT include brackets or nested objects. Remove titles. |
| `profile_image` | `Optional[str]` | URL to the actor's avatar/profile image |

### Magnet
*Leaf Node: Represents the physical file payload for download.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `link` | `<class 'str'>` | The magnet link or URL |
| `size` | `<class 'str'>` | Extracted precise file size (e.g., '4.2GB'). Do not infer sizes. |
| `date` | `<class 'str'>` | Upload date, critical for recency sorting |
| `title` | `Optional[str]` | Title of the magnet release if available |
| `number` | `Optional[str]` | The number/ID associated with this magnet release |

### Performer
*Leaf Node: Represents an actor/actress linked to media.*

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `<class 'str'>` | The unique canonical ID |
| `name` | `<class 'str'>` | The primary canonical name. Prefer Japanese, then English. |



### 3.1 LLM Anti-Hallucination Contract
*Generated from Pydantic `json_schema_extra['llm_constraint']` and Field descriptions. The LLM MUST strictly adhere to these validation rules.*

| Canonical Entity | LLM Extraction Rule & Validation Constraint |
| :--- | :--- |
| **`UniversalMediaSchema (Global)`** | The central hub. Relies on accurate merging of search + detail data. |
| **`UniversalMediaSchema -> date`** | Formatted as YYYY-MM-DD or null. DO NOT hallucinate today's date if missing. |
| **`UniversalActorSchema (Global)`** | MUST be a flattened list of strings for aliases. DO NOT include brackets or nested objects. |
| **`UniversalActorSchema -> aliases`** | Flattened list of string aliases. DO NOT include brackets or nested objects. Remove titles. |
| **`Magnet (Global)`** | MUST extract precise file sizes (e.g., 4.2GB) and upload dates if available. Do not infer sizes. |
| **`Magnet -> date`** | Upload date, critical for recency sorting |
| **`Performer (Global)`** | MUST extract the primary canonical name. If multiple languages exist, prefer Japanese, then English. |


## 4. The Operator Stream (The Branches)
*These are the functional transformers that map one schema to the next.*

| Operator / Function | Transformation | Failure Mode / Edge Case |
| :--- | :--- | :--- |
| **`ChallengeSolver_Protocol`** | `PhysicsStateSchema` (Blocked) -> Verified | Failed to solve reCAPTCHA. |
| **`_fetch_soup_safe()`** | `PhysicsStateSchema` -> `RawHTML_Stream` | Blocked by CAPTCHA; Timeout. |
| **`merge_detail()`** | Raw Data -> `UniversalMediaSchema` | Key mismatch; overwrite errors. |
