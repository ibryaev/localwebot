from aiogram import Dispatcher
from asyncio import run

from config import *
import bot.schedulers as scheduler
from bot.triggers import rt as rt_triggers
from bot.handlers import rt as rt_handlers
from bot.callbacks import rt as rt_callbacks

dp = Dispatcher()

async def main() -> None:
    await db.connect()

    scheduler.check_webs_owner.start()
    scheduler.check_active_restrs.start()

    dp.include_router(rt_triggers)
    dp.include_router(rt_callbacks)
    dp.include_router(rt_handlers)

    print(1)
    await dp.start_polling(bot)

if __name__ == "__main__":
    run(main())
