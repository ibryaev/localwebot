from aiogram import Dispatcher
from asyncio import run

from bot.handlers import rt as rt_handlers
from config import *

dp = Dispatcher()

async def main() -> None:
    dp.include_router(rt_handlers)
    print(1)
    await dp.start_polling(bot)

if __name__ == "__main__":
    run(main())
