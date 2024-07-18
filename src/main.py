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
    await bot.start()


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        if sys.platform == 'linux' or sys.platform == 'darwin':
            import uvloop

            uvloop.install()
        else:
            asyncio.run(main())
