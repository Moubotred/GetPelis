import httpx
from lxml import html

async def fetch_metadata(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        tree = html.fromstring(resp.text)
        title = tree.xpath('//title/text()')
        return title[0] if title else "Sin título"
