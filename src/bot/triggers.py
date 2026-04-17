from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION

from config import *
from utils import *

rt = Router()

@rt.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_transition(event: ChatMemberUpdated) -> None:
    chat_tid = event.chat.id
    chat_owner = await get_chat_owner(chat_tid)

    await db.mk_user(user=event.from_user)
    await db.mk_user(chat=event.chat)
    await db.upd_chat_owner(chat_tid, chat_owner.id)

@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_my_join_transition(event: ChatMemberUpdated):
    chat_tid = event.chat.id
    chat_owner = await get_chat_owner(chat_tid)

    await db.mk_user(chat=event.chat)
    await db.upd_chat_owner(chat_tid, chat_owner.id)

    chat = await db.get_chat(chat_tid)
    if chat is not None:
        return await event.answer("&gt;_&lt;") # Вывод (">_<". Особенности HTML)

    # Вывод
    await event.answer(
        text=(
            f"{await rndemoji()} <b>Этот чат не состоит ни в какой паутине</b>\n"
             "Кто-нибудь, у кого она есть, должен написать команду <code>паутина</code>."
        )
    )
