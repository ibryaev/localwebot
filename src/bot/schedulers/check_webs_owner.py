#############################################################
#                                                           #
#   Этот планировщик раз в 24 часа проверяет                #
#   что у всех паутин что аккаунт их владельца              #
#   существует. Если нет - делает владельца наследником.    #
#   Если наследника нет - удаляет паутину.                  #
#                                                           #
#############################################################

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import *

async def main():
    try:
        await db.cur.execute("SELECT * FROM webs")
        webs = await db.cur.fetchall()

        for web in webs:
            web_id = web['web_id']
            forename = web['forename']
            owner_tid = web['owner_tid']
            heir_tid = web['heir_tid']
            chats_tid = web['chats_tid']
            admin_chat_tid = web['admin_chat_tid']

            try:
                await bot.get_chat(owner_tid)
            except TelegramBadRequest:
                # Если аккаунт владельца (уже) нe существует
                if heir_tid is None:
                    # Наследник отсутствует
                    await db.rm_web(web_id)
                    await db.rm_user(owner_tid)
                    for chat_tid in chats_tid:
                        try:
                            await bot.send_message(
                                chat_id=chat_tid,
                                text=(
                                    f"Аккаунт владелца паутины <b>{forename}</b>, "
                                    "в котором состоял этот чат, не найден. "
                                    "Также у этой паутины не был назначен наследник. <b>Паутина была удалена.</b>"
                                )
                            )
                        except Exception:
                            continue
                    pass
                else:
                    # Наследник присутствует
                    await db.upd_web_heirtoowner(web_id, owner_tid, heir_tid)
                    await db.rm_user(owner_tid)
                    try:
                        await bot.send_message(
                            chat_id=admin_chat_tid,
                            text=(
                                f"Аккаунт владелца паутины <b>{forename}</b> не найден. "
                                "<b>Теперь владельцем паутины становиться её наследник.</b>"
                            )
                        )
                    except Exception:
                        pass
                    pass
            except TelegramForbiddenError:
                pass

    except Exception as e:
        print(f"error: schedulers: check_webs_owner.py: {e}")

check_webs_owner = AsyncIOScheduler()
check_webs_owner.add_job(main, "interval", hours=24)
