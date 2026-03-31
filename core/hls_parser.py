import httpx

try:
    import m3u8
    HAS_M3U8 = True
except ImportError:
    HAS_M3U8 = False


def parse_m3u8(url: str, headers: dict | None = None) -> str:
    """Return the highest-quality variant stream URL from an M3U8 playlist.
    Falls back to the original URL if parsing fails or m3u8 not installed."""
    if not HAS_M3U8:
        return url
    try:
        resp = httpx.get(url, headers=headers or {}, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        playlist = m3u8.loads(resp.text)
        if playlist.is_variant:
            # Pick highest bandwidth
            best = max(playlist.playlists, key=lambda p: p.stream_info.bandwidth or 0)
            uri = best.uri
            if not uri.startswith('http'):
                from urllib.parse import urljoin
                uri = urljoin(url, uri)
            return uri
        return url
    except Exception:
        return url
