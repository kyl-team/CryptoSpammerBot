import asyncio
import logging
import sys
from contextlib import suppress

import bot
import database
from routers import commands_router, queries_router

logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('pyrofork').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

bot.dp.include_routers(commands_router, queries_router)


async def main():
    await database.connect()
    # account = await Account.find_one()
    #
    # client = Client(
    #     name=account.phone,
    #     session_string=account.session,
    #     in_memory=True
    # )
    # await client.connect()
    #
    # async for dialog in client.get_dialogs(2):
    #     if dialog.chat.id == 178220800:
    #         async for msg in client.get_chat_history(dialog.chat.username):
    #             print(msg.date.strftime("%d.%m.%Y %H:%M:%S"), msg.text)

    await bot.start()


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        if sys.platform == 'linux' or sys.platform == 'darwin':
            import uvloop

            uvloop.run(main())
        else:
            asyncio.run(main())
