import asyncio
import os
from urllib.parse import urljoin, urlparse, unquote
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from core.media_file import MediaFile, MEDIA_EXTENSIONS, sanitize_filename

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    import httpx
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


DEFAULT_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)


def _ext(url: str) -> str:
    path = urlparse(url).path
    return os.path.splitext(path)[1].lstrip('.').lower()


def _is_media(url: str) -> bool:
    """Check media extension, ignoring query strings and fragments."""
    path = urlparse(url).path
    # Strip percent-encoding before splitext so Chinese chars don't confuse it
    path = unquote(path)
    ext = os.path.splitext(path)[1].lstrip('.').lower()
    return ext in MEDIA_EXTENSIONS

# alias used in playwright handlers
_is_media_url = _is_media


def _make_media(url: str, page_url: str) -> MediaFile:
    return MediaFile(url=url, page_url=page_url)


def _parse_html(html: str, base_url: str) -> List[str]:
    """Extract media URLs from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, 'lxml')
    found = set()

    for tag in soup.find_all('a', href=True):
        url = urljoin(base_url, tag['href'])
        if _is_media(url):
            found.add(url)

    for attr in ('src', 'data-src', 'data-url'):
        for tag in soup.find_all(attrs={attr: True}):
            url = urljoin(base_url, tag[attr])
            if _is_media(url):
                found.add(url)

    return list(found)


async def _sniff_playwright(url: str, user_agent: str, request_delay: float) -> List[str]:
    found = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        # Intercept ALL network requests (catches signed CDN URLs, XHR, etc.)
        async def on_request(request):
            req_url = request.url
            if _is_media_url(req_url):
                found.add(req_url)

        # Also intercept responses to catch redirected media URLs
        async def on_response(response):
            resp_url = response.url
            ct = response.headers.get('content-type', '')
            if _is_media_url(resp_url):
                found.add(resp_url)
            # Catch by content-type for URLs without file extensions
            elif any(t in ct for t in ('audio/', 'video/', 'application/octet-stream')):
                if resp_url.startswith('http'):
                    found.add(resp_url)

        page.on('request', on_request)
        page.on('response', on_response)

        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        # Wait for JS players and dynamic content to finish loading
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except Exception:
            pass  # networkidle may never fire on ad-heavy pages
        await asyncio.sleep(request_delay)

        html = await page.content()

        # Also scan all <a href> and data attributes in rendered DOM
        # including data-url, data-src, data-audio, data-file attributes
        extra_urls = await page.evaluate(
            "(" + "() => {"
            + "const exts=['mp3','mp4','wav','flac','ogg','m4a','aac','opus','avi','mkv','webm','m3u8'];"
            + "const found=new Set();"
            + "const attrs=['href','src','data-src','data-url','data-audio','data-file','data-link','data-mp3','data-download'];"
            + "const sel=attrs.map(a=>'['+a+']').join(',');"
            + "document.querySelectorAll(sel).forEach(el=>{"
            + "  attrs.forEach(attr=>{"
            + "    const val=el.getAttribute(attr);"
            + "    if(val){const p=val.split('?')[0].toLowerCase();"
            + "      if(exts.some(e=>p.endsWith('.'+e))){"
            + "        found.add(val.startsWith('http')?val:new URL(val,window.location.href).href);"
            + "      }}"
            + "  });"
            + "});"
            + "return[...found];"
            + "})"
        )
        found.update(extra_urls)

        await browser.close()

    found.update(_parse_html(html, url))
    return list(found)


def _sniff_static(url: str, user_agent: str) -> List[str]:
    headers = {'User-Agent': user_agent}
    resp = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    return _parse_html(resp.text, url)


class SnifferEngine:
    def __init__(
        self,
        user_agent: str = DEFAULT_UA,
        request_delay: float = 0.5,
        use_headless: bool = True,
    ):
        self.user_agent = user_agent
        self.request_delay = request_delay
        self.use_headless = use_headless

    def sniff(self, url: str) -> List[MediaFile]:
        from core.alist_sniffer import sniff_alist

        async def _run_all():
            # Try AList API first
            try:
                results = await sniff_alist(url, self.user_agent)
                if results:
                    return results
            except Exception:
                pass
            # Fallback: Playwright generic sniffer
            if self.use_headless and HAS_PLAYWRIGHT:
                urls = await _sniff_playwright(url, self.user_agent, self.request_delay)
                seen = set()
                results = []
                for u in urls:
                    if u not in seen:
                        seen.add(u)
                        results.append(_make_media(u, url))
                return results
            # Static fallback
            if HAS_BS4:
                urls = _sniff_static(url, self.user_agent)
                seen = set()
                results = []
                for u in urls:
                    if u not in seen:
                        seen.add(u)
                        results.append(_make_media(u, url))
                return results
            raise RuntimeError('Neither Playwright nor httpx+bs4 is available.')

        return asyncio.run(_run_all())


class SnifferWorker(QThread):
    results_ready = pyqtSignal(list)   # List[MediaFile]
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        user_agent: str = DEFAULT_UA,
        request_delay: float = 0.5,
        use_headless: bool = True,
    ):
        super().__init__()
        self.url = url
        self.engine = SnifferEngine(
            user_agent=user_agent,
            request_delay=request_delay,
            use_headless=use_headless,
        )

    def run(self):
        try:
            self.status.emit(f'Sniffing {self.url} ...')
            results = self.engine.sniff(self.url)
            self.status.emit(f'Found {len(results)} media file(s).')
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))
