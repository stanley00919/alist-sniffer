import asyncio
from urllib.parse import urlparse, unquote, quote
from typing import List
import httpx

from core.media_file import MediaFile, MEDIA_EXTENSIONS


async def sniff_alist(page_url: str, user_agent: str = '') -> List[MediaFile]:
    """
    Sniff an AList V3 page.
    Uses Playwright to obtain session cookies, then calls /api/fs/list.
    Each file entry includes a 'sign' token used to build the download URL.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []

    ua = user_agent or (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )

    parsed = urlparse(page_url)
    base_url = f'{parsed.scheme}://{parsed.netloc}'
    alist_path = unquote(parsed.path)

    # Step 1: load page with Playwright to acquire session cookies
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()
        await page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(1)
        cookies = await context.cookies()
        await browser.close()

    cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
    hdrs = {
        'User-Agent': ua,
        'Referer': page_url,
        'Cookie': cookie_str,
        'Origin': base_url,
        'Content-Type': 'application/json',
    }

    # Step 2: call /api/fs/list — returns file list with sign tokens
    async with httpx.AsyncClient(headers=hdrs, follow_redirects=True, timeout=20) as client:
        r = await client.post(
            f'{base_url}/api/fs/list',
            json={
                'path': alist_path,
                'password': '',
                'page': 1,
                'per_page': 0,
                'refresh': False,
            }
        )
        if r.status_code != 200:
            return []
        data = r.json()
        if data.get('code') != 200:
            return []
        content = data.get('data', {}).get('content') or []

    # Step 3: build MediaFile list using sign token from list response
    results: List[MediaFile] = []
    for f in content:
        name = f.get('name', '')
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        if ext not in MEDIA_EXTENSIONS:
            continue
        size = f.get('size', 0)
        sign = f.get('sign', '')
        file_path = alist_path.rstrip('/') + '/' + name
        dl_url = base_url + '/d' + quote(file_path)
        if sign:
            dl_url += f'?sign={sign}'
        results.append(MediaFile(
            url=dl_url,
            filename=name,
            size=size,
            media_type=ext,
            page_url=page_url,
        ))

    return results
