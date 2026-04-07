# Scene Crawler

A professional-grade command-line tool for crawling, parsing, and managing media metadata. Optimized with target-state idempotency, high-quality filtering, and seamless integration with Stash and Deluge.

## Key Features

- **Architectural Caching**: Smart idempotency skips already-downloaded scenes and images.
- **Stash Integration**: Automated metadata and cover enrichment for Stash servers with whitelist filtering.
- **Deluge Automation**: Automated management of torrents (filtering by age, size, and repository status).
- **SSH Repository Scanning**: Fast, stat-based scanning of remote video libraries to build canonical lists.
- **Freshness Control**: Configurable "max-age" filtering to keep your download queue relevant.

## Setup

1.  **Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -e .
    pip install "aiohttp-client-cache[sqlite]"
    ```

## Configuration (`config/crawler.json`)

The crawler uses a central JSON file for environment-specific defaults. Edit this file to manage your server addresses:

```json
{
  "magnet_max_age_days": 365,
  "rebuild_host": "winsonsun@100.64.26.2",
  "rebuild_path": "/mnt/cig/video/{category}",
  "stash_url": "http://100.64.26.2:9999/graphql",
  "deluge_url": "http://100.64.26.2:8112",
  "deluge_pass": "deluge",
  "deluge_batch_size": 50
}
```

---

## 1. Main Crawler Usage

### Basic Crawling
```bash
# Crawl specific IDs
crawler MIST-001 OFJE-588 --run-parse --run-download --download-image

# Lightweight "Native" mode (Fastest, bypasses browser)
crawler MIST-001 --native-fetch --run-parse
```

### Discovery & Collection Scanning
```bash
# Discover first 4 pages of latest releases
crawler --discover --pages 4 --site javbus --run-parse

# Scan an actor's entire career (uses active_scan.json)
crawler "葵つかさ" --collection-scan --site javbus --run-parse
```

### Repository Management
Build canonical JSON lists of your local library by scanning your server via SSH:
```bash
# Generate ain_list.json with file sizes for quality filtering
crawler --rebuild-list ain
```

### Stash Enrichment
Sync metadata and covers to your Stash server. If `--ain-list` is provided, it **whitelists** only the videos you actually own on disk.
```bash
crawler --sync-to-stash "葵つかさ" --ain-list data/list/ain_list.json
```

---

## 2. Deluge Maintenance Tool (`scripts/deluge_filter.py`)

Manage your Deluge server queue intelligently.

- **Quality Filter**: Keeps torrents if they are >500MB larger than your archived version.
- **Junk Filter**: Automatically removes stale `[javdb.com]` items (<100MB, older than 2 days).
- **Redundancy Filter**: Identifies items you've already archived.

```bash
# Generate a deletion plan (Dry run)
python3 scripts/deluge_filter.py

# Physically remove redundant items from server and disk
python3 scripts/deluge_filter.py --deletion-plan

# Upload new magnets from canonical_scene_id.json (Only if missing from Repo & Deluge)
python3 scripts/deluge_filter.py --upload-new
```

---

## 3. Utility Tools

### `scripts/group_magnets.py`
Groups the flat `to-be-downloaded.txt` into a structured `canonical_scene_id.json`.
- Resolves messy filenames to Canonical IDs.
- Removes duplicates.
- Filters out items already present in your `data/list/` repository.
```bash
python3 scripts/group_magnets.py
```

### `scripts/maintenance_filter_magnets.py`
Cleans your `to-be-downloaded.txt` based on release dates.
```bash
# Remove magnets for scenes older than 90 days
python3 scripts/maintenance_filter_magnets.py --days 90
```

### `scripts/rename_tool.py`
A standalone tool to batch rename local files using the project's canonical naming policy.
```bash
python3 scripts/rename_tool.py /path/to/your/videos --dry-run
```

---

## Project Structure
- `src/crawler/`: Core logic, parsers, and Stash/Deluge clients.
- `config/`: Configuration (Managed by `CRAW_CONF`).
- `data/`: Local storage for profiles, metadata, and images (Managed by `CRAW_DATA`).
- `scripts/`: Maintenance and management utilities.
- `tests/`: Architectural and functional test suites.
