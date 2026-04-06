# -*- coding: utf-8 -*-
import re
from pathlib import Path

def parse_video_block(block_text: str) -> dict:
    """Parse a javdb detail markdown block into a metadata dict."""
    out = {}

    # Header: id and title
    m = re.search(r'^##\s+\*\*(?P<id>[^*]+)\*\*\s+\*\*(?P<title>.+?)\*\*', block_text, flags=re.M)
    if m:
        out['id'] = m.group('id').strip()
        out['title'] = m.group('title').strip()

    # Cover image (first image)
    m_cover = re.search(r'!\[[^\]]*\]\((https?://[^\)]+)\)', block_text)
    if m_cover:
        out['cover_image'] = m_cover.group(1)

    # Play or page URL: look for links containing '/v/'
    m_play = re.search(r'\]\((https?://[^\)]+/v/[A-Za-z0-9_-]+(?:[^\)]*)?)\)', block_text)
    if m_play:
        out['play_url'] = m_play.group(1)
        m_norm = re.search(r'(https?://[^/]+/v/[A-Za-z0-9_-]+)', out['play_url'])
        if m_norm:
            out['page_url'] = m_norm.group(1)

    # ID line fallback
    if 'id' not in out:
        m = re.search(r'\*\*ID:\*\*\s*\[([^\]]+)\]\([^\)]*\)-?([0-9A-Za-z-]*)', block_text)
        if m:
            prefix = m.group(1).strip()
            suffix = m.group(2).strip()
            out['id'] = prefix + (('-' + suffix) if suffix else '')

    # Released Date (YYYY-MM-DD)
    m = re.search(r'\*\*Released Date:\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', block_text)
    if m:
        out['released_date'] = m.group(1)

    # Duration minutes
    m = re.search(r'\*\*Duration:\*\*\s*([0-9]+)\s*minute', block_text)
    if m:
        try:
            out['duration_minutes'] = int(m.group(1))
        except Exception:
            pass

    # Maker and Publisher
    def link_field(key):
        mm = re.search(rf'\*\*{re.escape(key)}:\*\*\s*\[([^\]]+)\]\((https?://[^\)]+)\)', block_text)
        if mm:
            return {'name': mm.group(1).strip(), 'url': mm.group(2).strip()}
    maker = link_field('Maker')
    publisher = link_field('Publisher')
    if maker:
        out['maker'] = maker
    if publisher:
        out['publisher'] = publisher

    # Tags
    tags_line_match = re.search(r'\*\*Tags:\*\*([^\n]+)', block_text)
    if tags_line_match:
        tags_line = tags_line_match.group(1)
        tags = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', tags_line)
        out['tags'] = [{'name': t[0].strip(), 'url': t[1]} for t in tags]
    else:
        out['tags'] = []

    # Actors
    actors_match = re.search(r'\*\*Actor\(s\):\*\*\s*(.+)', block_text)
    if actors_match:
        actors_line = actors_match.group(1)
        actors = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', actors_line)
        out['actors'] = [{'name': a[0].strip(), 'url': a[1]} for a in actors]
    else:
        out['actors'] = []

    # Sample large images: _l_ pattern
    samples = re.findall(r'\]\((https?://[^\s\)]+_l_[0-9]+\.(?:jpg|png))\)', block_text)
    if not samples:
        samples = re.findall(r'(https?://[^\s\)]+_l_[0-9]+\.(?:jpg|png))', block_text)
    seen = set(); samples_filtered = []
    for u in samples:
        if u not in seen:
            seen.add(u); samples_filtered.append(u)
    out['sample_images'] = samples_filtered

    # Magnet links within block — capture only the raw magnet URI, stopping at whitespace, quotes or parentheses
    magnets = re.findall(r'(magnet:\?[^\s\)\"\']+)', block_text)
    # normalize and trim common trailing punctuation
    cleaned = []
    for m in magnets:
        mm = m.rstrip('),.;')
        cleaned.append(mm)
    out['magnet_links'] = cleaned

    # Also extract structured magnet entries by matching the link's display text and the magnet URI.
    # Display text often contains multiple lines: name, size and file count.
    magnet_entries = []
    # match markdown links where the target is a magnet URI; capture display text (which may contain newlines)
    for m in re.finditer(r"\[\s*(.+?)\s*\]\s*\((magnet:[^\s\)\"']+)", block_text, flags=re.S):
        display = m.group(1).strip()
        uri = m.group(2).strip()
        # split display into lines and clean
        lines = [ln.strip() for ln in display.splitlines() if ln.strip()]
        name = lines[0] if lines else ''
        rest = ' '.join(lines[1:]) if len(lines) > 1 else ''

        # try to find size like '989MB' or '1.30GB'
        total_size = None
        msize = re.search(r'([0-9]+(?:\.[0-9]+)?\s*(?:GB|MB|KB))', display, flags=re.I)
        if msize:
            total_size = msize.group(1)

        # try to find file count like '1 file(s)'
        file_count = None
        mcount = re.search(r'([0-9]+)\s*file', display, flags=re.I)
        if mcount:
            try:
                file_count = int(mcount.group(1))
            except Exception:
                file_count = None

        magnet_entries.append({
            'uri': uri.rstrip('),.;'),
            'name': name,
            'total_size': total_size,
            'file_count': file_count,
        })

    out['magnet_entries'] = magnet_entries

    # raw duration string
    m = re.search(r'\*\*Duration:\*\*\s*([0-9]+\s*minute\(s\))', block_text)
    if m:
        out['duration'] = m.group(1)

    return out


def find_block(text: str, id_hint: str = None) -> str | None:
    headers = list(re.finditer(r'^##\s+\*\*(.+?)\*\*', text, flags=re.M))
    if not headers:
        return None
    if id_hint:
        for i, h in enumerate(headers):
            if id_hint in h.group(1):
                start = h.start()
                end = headers[i+1].start() if i+1 < len(headers) else len(text)
                return text[start:end]
    h = headers[0]
    i = 0
    start = h.start()
    end = headers[1].start() if len(headers) > 1 else len(text)
    return text[start:end]


def parse_from_text(text: str, id_hint: str = None) -> dict:
    block = find_block(text, id_hint=id_hint)
    if not block:
        return {}
    return parse_video_block(block)


def parse_from_file(path: str | Path, id_hint: str = None) -> dict:
    p = Path(path)
    txt = p.read_text(encoding='utf-8')
    return parse_from_text(txt, id_hint=id_hint)
