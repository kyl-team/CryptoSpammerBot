import aiohttp


async def is_valid_proxy(proxy_url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request('GET', 'https://httpbin.org/get', proxy=proxy_url) as response:
                return response.status == 200
    except Exception:
        return False
