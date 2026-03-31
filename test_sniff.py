import asyncio
from core.alist_sniffer import sniff_alist

results = asyncio.run(sniff_alist(
    'https://www.asmrgay.com/asmr/'
    '%E4%B8%AD%E6%96%87%E9%9F%B3%E5%A3%B0/'
    '%E6%AD%A5%E9%9D%9E%E7%83%9F/'
    '%E7%AC%AC%E4%B8%80%E5%AD%A3/001-100'
))
for r in results:
    print(f'{r.filename} ({r.size_str})')
    print(f'  -> {r.url[:80]}...')
print(f'\nTotal: {len(results)}')
