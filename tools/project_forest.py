import os
import sys

# Add the src folder to path so we can import ontology
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawler.ontology import UniversalMediaSchema, UniversalActorSchema, Magnet, Performer

FOREST_TEMPLATE = """# System Data Schema Dependency Forest

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

{canopy_tables}

### 3.1 LLM Anti-Hallucination Contract
*Generated from Pydantic `json_schema_extra['llm_constraint']` and Field descriptions. The LLM MUST strictly adhere to these validation rules.*

| Canonical Entity | LLM Extraction Rule & Validation Constraint |
| :--- | :--- |
{llm_contracts}

## 4. The Operator Stream (The Branches)
*These are the functional transformers that map one schema to the next.*

| Operator / Function | Transformation | Failure Mode / Edge Case |
| :--- | :--- | :--- |
| **`ChallengeSolver_Protocol`** | `PhysicsStateSchema` (Blocked) -> Verified | Failed to solve reCAPTCHA. |
| **`_fetch_soup_safe()`** | `PhysicsStateSchema` -> `RawHTML_Stream` | Blocked by CAPTCHA; Timeout. |
| **`merge_detail()`** | Raw Data -> `UniversalMediaSchema` | Key mismatch; overwrite errors. |
"""

def generate_canopy_markdown(models):
    canopy_md = ""
    llm_md = ""
    
    for model in models:
        model_name = model.__name__
        doc = model.__doc__ or ""
        
        canopy_md += f"### {model_name}\n"
        canopy_md += f"*{doc}*\n\n"
        canopy_md += "| Field | Type | Description |\n"
        canopy_md += "| :--- | :--- | :--- |\n"
        
        fields = model.model_fields
        for field_name, field_info in fields.items():
            type_hint = str(field_info.annotation).replace('typing.', '')
            desc = field_info.description or ""
            canopy_md += f"| `{field_name}` | `{type_hint}` | {desc} |\n"
            
        canopy_md += "\n"
        
        # Add LLM constraints
        constraint = model.model_config.get("json_schema_extra", {}).get("llm_constraint", "")
        if constraint:
            llm_md += f"| **`{model_name} (Global)`** | {constraint} |\n"
            
        for field_name, field_info in fields.items():
            desc = field_info.description or ""
            if "MUST" in desc or "DO NOT" in desc or "critical" in desc.lower():
                llm_md += f"| **`{model_name} -> {field_name}`** | {desc} |\n"

    return canopy_md, llm_md

def main():
    models = [UniversalMediaSchema, UniversalActorSchema, Magnet, Performer]
    canopy_tables, llm_contracts = generate_canopy_markdown(models)
    
    final_md = FOREST_TEMPLATE.format(
        canopy_tables=canopy_tables,
        llm_contracts=llm_contracts
    )
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SCHEMA_DEPENDENCY_FOREST.md'))
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_md)
        
    print(f"✅ Successfully projected Ontology into {output_path}")

if __name__ == "__main__":
    main()
