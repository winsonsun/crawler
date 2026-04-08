# The Fossil Record

A ledger of environmental constraints, failures, and the physical rules of the sandbox.

## Scar: 2026-04-08 Test Initialization
- **Trigger:** Running the script for the first time
- **Physics:** The system requires a fossil record file to exist to store constraints.
- **Constraint:** A FOSSIL_RECORD.md file must be maintained in the root directory.

## Scar: 2026-04-08 JavExample.com Privacy Modal
- **Trigger:** Attempting to locate search input on home page.
- **Physics:** A full-screen modal with ID 'privacy-overlay' blocks all user interaction until a 'Accept' button is clicked.
- **Constraint:** The crawler must detect and click the overlay button before any search or extraction logic can proceed.

## Scar: 2026-04-08 JavDB Cloudflare Turnstile
- **Trigger:** Accessing javdb.com search or home page.
- **Physics:** Cloudflare blocks automated access with a 'Just a moment...' challenge. It requires JavaScript execution and a significant wait time (or headful interaction) to resolve.
- **Constraint:** The current 'WAIT' strategy in OmniSolver is insufficient. We need to implement a more persistent wait or a headful session capture to acquire valid cookies.

## Scar: 2026-04-08 JavDB English Age Gate
- **Trigger:** Accessing /v/ detail pages on javdb.com.
- **Physics:** JavDB shows an English-language age gate ('You must be of legal age...') even if cookies were set on the home page. It requires clicking an 'Enter' or 'Confirm' button.
- **Constraint:** The current js_bypass needs to handle English variants of age gate buttons and verify that the page title or content has actually changed to the detail view.

## Scar: 2026-04-08 JavBus Persistent Age Gate
- **Trigger:** Accessing javbus.com search results.
- **Physics:** JavBus uses a stateful age gate that requires a checkbox ('我已經成年') to be checked BEFORE the '確認' button is clicked. It also relies on the 'existmag=all' cookie to persist preferences.
- **Constraint:** The JS bypass must use a delay between the checkbox click and the button click. We should also proactively inject 'existmag=all' into the session cookies to minimize gate encounters.

## Scar: 2026-04-08 Autonomous Bypass Evolution
- **Trigger:** High-frequency reCAPTCHA and complex anti-bot challenges on landing pages.
- **Physics:** Static JS bypasses are fragile against evolving challenges like Turnstile or reCAPTCHA.
- **Constraint:** Implemented a 3-tier bypass in `_fetch_soup_safe`: (1) Fast aiohttp, (2) Medium Static JS, (3) Slow OmniSolver (Vision-based). This ensures the crawler can autonomously recover from blocks without human intervention.

## Scar: 2026-04-08 Regressive OmniSolver Persona
- **Trigger:** Refactoring of OmniSolver and discovery loop.
- **Physics:** The 'China Driver License' expert persona and sequenced click logic were lost during architectural compression, leading to infinite 'Confirm' loops on JavBus.
- **Constraint:** Always preserve the 'Logical Question' persona in OmniSolver and ensure discovery loops handle stateful checkboxes with delays.
