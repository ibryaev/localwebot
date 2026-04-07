#############################################################
#                                                           #
#   Этот скедулер раз в 24 часа проверяет                   #
#   что у всех паутин что аккаунт их владельца              #
#   существует. Если нет - делает владельца наследником.    #
#   Если наследника нет - удаляет паутину.                  #
#                                                           #
#############################################################

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import *

async def main():
    try:
        await db.cur.execute("SELECT * FROM webs")
        webs = await db.cur.fetchall()

        for web in webs:
            web_id = web['web_id']
            owner_tid = web['owner_tid']
            heir_tid = web['heir_tid']
            owner_t = await bot.get_chat(owner_tid)

            if not owner_t:
                # Если аккаунт владельца не (уже) существует
                if heir_tid is None:
                    # Наследник отсутствует
                    await db.rm_web(web_id)
                    await db.rm_user(owner_tid)
                    pass
                else:
                    # Наследник присутствует
                    await db.upd_web_heirtoowner(web_id, owner_tid, heir_tid)
                    await db.rm_user(owner_tid)
                    pass

    except Exception as e:
        print(f"error: schedulers: check_webs_owner.py: {e}")

check_webs_owner = AsyncIOScheduler()
check_webs_owner.add_job(main, "interval", hours=24)
