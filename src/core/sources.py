import re

import aiohttp
from bs4 import BeautifulSoup, Tag

from database import ChannelService, Channel


async def update_channels(service: ChannelService, data: dict[str, ...] | None = None) -> int:
    channels: set[str] = set()

    match service:
        case 'tgstat.ru':
            async with aiohttp.ClientSession() as session:
                async with session.get('https://uk.tgstat.com/ratings/channels/crypto/public', headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "max-age=0",
                    "priority": "u=0, i",
                    "sec-ch-ua": '"Chromium";v="124", "DuckDuckGo";v="124", "Not-A.Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "cross-site",
                    "sec-fetch-user": "?1",
                    "sec-gpc": "1",
                    "upgrade-insecure-requests": "1"
                }) as response:
                    text = await response.text()
                    bs4 = BeautifulSoup(text, 'html.parser')
                    card_holder = bs4.select_one('#sticky-center-column')
                    cards: list[Tag] = card_holder.find_all('div')
                    pattern = re.compile(r'https://uk\.tgstat\.com/channel/@(\w+)/stat')
                    for card in cards:
                        link_elements = card.find_all('a')
                        for link_element in link_elements:
                            if link_element and link_element.attrs:
                                url: str | None = link_element.attrs.get('href')
                                if url:
                                    match = pattern.match(url.strip())
                                    if match:
                                        channels.add(match.group(1))
        case 'telemetr.io':
            async with aiohttp.ClientSession() as session:
                async with session.get('https://telemetr.io/en/catalog/global/cryptocurrencies', headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-language": "en-US,en;q=0.6",
                    "cache-control": "no-cache",
                    "pragma": "no-cache",
                    "priority": "u=0, i",
                    "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Brave\";v=\"127\", \"Chromium\";v=\"127\"",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "\"Windows\"",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "same-origin",
                    "sec-fetch-user": "?1",
                    "sec-gpc": "1",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
                }) as response:
                    text = await response.text()
                    bs4 = BeautifulSoup(text, 'html.parser')
                    elements = bs4.select(".channel-name__attribute > span > span")
                    for element in elements:
                        channels.add(element.text)
        case 'telemetr.me':
            for channel in ['stukach_trading', 'telecrypto_ua', 'joinchat', 'cryptozarr', 'sharktradeandcrypto',
                            'ukripta', 'enjoy_crypto_guild', 'cryptoukrainian7', 'crypto_salo', 'lwallet_channel',
                            'jabascript', 'cryptocristalll', 'cryptosscamm', 'just_invest44', 'nikeyl', 'crypto_k_s',
                            'cryptobelief', 'joinchat', 'crossirpin', 'cryptofox_me', 'satoshinakamotocrypto1',
                            'crypto_klauss', 'cryptomillionersx', 'proskura_crypto', 'ffvan_crypto', 'cryptocrowfeeds',
                            'cruptoukrop', 'ukrypti', 'lutaemcrypto', 'money_for_pizza', 'crypto_svit',
                            'varenik14crypto', 'bodry_finance_blog', 'cryptokraina', 'cit_group', 'treading_book',
                            'crypto_xpert4you', 'rozhok_crypto']:
                channels.add(channel)
        case _:
            raise ValueError(f'Unknown service: {service}')

    for channel in channels:
        document = Channel(url=channel, service=service)
        await document.insert()

    return len(channels)
