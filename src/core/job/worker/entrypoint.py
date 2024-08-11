import asyncio

from aiogram.types import BufferedInputFile
from pyrofork.errors import RPCError

from bot import bot
from core.job import storage
from database import Account, Proxy, Channel
from .report import WorkResult, format_date, format_report
from .state import TaskState
from .utils import slice_array
from .work import get_similar_channels, work
from ...accounts import get_client


async def start(user_id: int):
    channels: set[str] = set()

    async for channel in Channel.find():
        channels.add(channel.url)

    proxies = await Proxy.find().to_list()
    clients = []

    proxy_index = 0

    async for account in Account.find():
        if len(proxies) > 0:
            proxy = proxies[proxy_index % len(proxies)]
            proxy_data = {
                'scheme': 'http',
                'hostname': proxy.hostname,
                'port': proxy.port,
                'username': proxy.username,
                'password': proxy.password,
            }
        else:
            proxy_data = None
        client = get_client(account.phone, proxy=proxy_data, session_string=account.session)
        clients.append(client)
        if not client.is_connected:
            try:
                await client.connect()
            except RPCError as e:
                await bot.send_message(user_id,
                                       f'❌ Не удалось подключится к аккаунту <code>{account.phone}</code>, <b>[{e.CODE} {e.ID}]</b> <i>{e.MESSAGE}</i>. Попробуйте снова, или удалите и войдите в аккаунт заново.')
                return
        proxy_index += 1

    if storage.similar:
        channel_slices = slice_array(list(channels), len(clients))

        tasks = []
        for i in range(len(clients)):
            tasks.append(get_similar_channels(clients[i], channel_slices[i]))

        channel_groups = await asyncio.gather(*tasks)

        for group in channel_groups:
            for channel in group:
                channels.add(channel)

    channels_for_clients = slice_array(list(channels), len(clients))

    max_load = max(0, *[len(x) for x in channels_for_clients])
    if max_load > 20:
        await bot.send_message(user_id, f'⚠️ Максимальная нагрузка на аккаунт: {max_load} каналов')

    status_message = await bot.send_message(user_id, f'🤖 Задача в процессе')

    state = TaskState(status_message, len(channels))

    tasks = []
    for i in range(len(clients)):
        tasks.append(work(clients[i], channels_for_clients[i], state))

    results_arr = await asyncio.gather(*tasks)
    results: WorkResult = []
    for result_items in results_arr:
        results += result_items

    timestamp = format_date()
    report = format_report(results)

    report_document = BufferedInputFile(report.encode(),
                                        filename=f"report.md")
    await bot.send_document(user_id, report_document, caption=f'Отчет от {timestamp}')
