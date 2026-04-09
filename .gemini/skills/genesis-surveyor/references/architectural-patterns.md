# Architectural Evolving Direction Reference

Choose the architectural paradigm based on the decoded Intent and the Terrain Summary.

## 1. Async Pipeline (Preferred for Crawlers)
- **Best for:** High throughput, multiple data sources, I/O bound tasks.
- **Implementation:** `asyncio` or `trio` in Python. Modular stages: Fetch -> Parse -> Transform -> Store.
- **Pros:** Excellent resource utilization.
- **Cons:** Complex error handling across stages.

## 2. Domain-Driven Design (DDD)
- **Best for:** Complex business logic (e.g., Star ranking systems, cross-site entity linking).
- **Implementation:** Repository pattern for storage, Service layer for orchestration, Value Objects for schemas.
- **Pros:** High ontological integrity, very maintainable.
- **Cons:** Over-engineered for simple scrapers.

## 3. State Machine Navigation
- **Best for:** Complex UI interactions (e.g., clicking age verification, handling popups, solving captchas).
- **Implementation:** A formal state machine where each node is a page type.
- **Pros:** Predictable behavior, easy to debug "where" a crawler got stuck.
- **Cons:** Rigid if the site structure changes drastically.

## 4. Semantic Adaptability (Omni-Solver Vector)
- **Best for:** Brittle sites with frequently changing CSS selectors.
- **Implementation:** LLM-Vision (Gemini) to identify interactive elements and extract data.
- **Pros:** Minimal maintenance, survives DOM mutations.
- **Cons:** High API cost, slower than CSS selectors.
