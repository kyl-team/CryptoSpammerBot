import aiohttp

from database import ChannelService, Channel


async def update_channels(service: ChannelService, data: dict[str, ...] | None = None) -> int:
    match service:
        case 'tgstat.ru':
            channels: set[str] = set()
            async with aiohttp.ClientSession() as session:
                async with session.get('https://uk.tgstat.com/ratings/channels/crypto', headers={
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
            for channel in channels:
                document = Channel(url=channel, service=service)
                await document.insert()
            return len(channels)
        case 'telemetr.io':
            raise NotImplementedError('WIP')
        case 'telemetr.me':
            if not data or 'session_id' not in data:
                raise ValueError('Missing session_id')

            session_id = data['session_id']

            raise NotImplementedError('WIP')
        case _:
            raise ValueError(f'Unknown service: {service}')
