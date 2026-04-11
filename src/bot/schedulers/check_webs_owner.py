#############################################################
#                                                           #
#   Этот планировщик раз в 24 часа проверяет                #
#   что аккаунт владельца паутины существует.               #
#   Если нет - делает владельца наследником.                #
#   Если наследника нет или у него есть своя паутина -      #
#   удаляет паутину.                                        #
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
                await bot.get_chat(owner_tid) # Получаем инфу об аккаунте владельца
                
            except TelegramBadRequest:
                # Если аккаунт владельца (уже) нe существует
                
                # Проверка, может ли наследник принять паутину
                can_inherit = False
                if heir_tid is not None and await db.get_web_by_owner_tid(heir_tid) is None:
                    # Если наследник есть и у него нет своей паутины - наследуем
                        can_inherit = True

                if can_inherit:
                    await db.upd_web_heirtoowner(web_id, heir_tid)
                    await db.rm_user(owner_tid)
                    heir = await db.get_user_by_tid(heir_tid)

                    if admin_chat_tid:
                        try:
                            await bot.send_message(
                                chat_id=admin_chat_tid,
                                text=(
                                    f"Аккаунт владельца паутины <b>{forename}</b> не найден. "
                                    f"<b>Теперь владельцем паутины становится её наследник - {heir['link']}.</b>"
                                )
                            )
                        except Exception:
                            pass
                else:
                    # Наследника нет, либо у него УЖЕ ЕСТЬ своя паутина
                    await db.rm_web(web_id)
                    await db.rm_user(owner_tid)
                    
                    # Формируем причину для рассылки
                    if heir_tid is not None:
                        text_reason = "Назначенный наследник уже имеет собственную паутину, поэтому не смог перенять права."
                    else:
                        text_reason = "Также у этой паутины не был назначен наследник."
                        
                    for chat_tid in chats_tid:
                        try:
                            await bot.send_message(
                                chat_id=chat_tid,
                                text=(
                                    f"Аккаунт владельца паутины <b>{forename}</b>, "
                                    "в которой состоял этот чат, был удалён.\n"
                                    f"{text_reason} <b>Паутина была распущена.</b>"
                                )
                            )
                        except Exception:
                            continue

            except TelegramForbiddenError:
                # Если владелец заблокал бота, но аккаунт существует
                pass # Ничего не трогаем

    except Exception as e:
        print(f"error: schedulers: check_webs_owner.py: {e}")

check_webs_owner = AsyncIOScheduler()
check_webs_owner.add_job(main, "interval", seconds=20)
