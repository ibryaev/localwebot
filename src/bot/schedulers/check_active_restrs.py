#############################################################
#                                                           #
#   Этот планировщик раз в 60 секунд проверяет              #
#   и удаляет из базы данных истекшие                       #
#   муты и баны. В случае истечения бана бот                #
#   уведомляет об этом пользователя в ЛС.                   #
#                                                           #
#############################################################

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import *

async def main():
        try:
            await db.cur.execute(
                "DELETE FROM restrs WHERE date_until IS NOT NULL AND date_until <= NOW() RETURNING *",
            )
            deleted_restrs = await db.cur.fetchall()
            await db.conn.commit()

            for restr in deleted_restrs:
                if restr['restr'] != "ban":
                    continue

                web = await db.get_web(restr['web_id'])

                try:
                    await bot.send_message(
                        chat_id=restr['user_tid'],
                        text=f"⛓️‍💥 Ваш глобальный бан в паутине чатов <b>{web['forename']}</b> окончен!"
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"error: database: check_active_restrs(): {e}")
            await db.conn.rollback()

check_active_restrs = AsyncIOScheduler()
check_active_restrs.add_job(main, "interval", seconds=60)
