from aiogram import Dispatcher
from asyncio import run

from bot.handlers import rt as rt_handlers
from bot.callbacks import rt as rt_callbacks
from config import *

dp = Dispatcher()

async def main() -> None:
    await db.connect()
    dp.include_router(rt_handlers)
    dp.include_router(rt_callbacks)
    print(1)
    await dp.start_polling(bot)

if __name__ == "__main__":
    run(main())
