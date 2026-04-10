from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION

from config import *
from utils import *

rt = Router()

@rt.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_transition(event: ChatMemberUpdated) -> None:
    user_t = event.from_user
    chat_t = event.chat
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)

    await db.mk_user(user_t.id, user_t.username)
    await db.mk_user(chat_tid, chat_t.username)
    await db.upd_chat_owner(chat_tid, chat_owner_t.id)

@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_my_join_transition(event: ChatMemberUpdated):
    chat_t = event.chat
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)

    await db.mk_user(chat_tid, chat_t.username)
    await db.upd_chat_owner(chat_tid, chat_owner_t.id)

    chat = await db.get_chat(chat_tid)

    if chat is not None:
        return await event.answer("&gt;_&lt;") # Вывод (">_<". Особенности HTML)

    # Вывод
    emoji = await rndemoji()

    await event.answer(
        text=(
            f"{emoji} <b>Этот чат не состоит ни в какой паутине</b>\n"
             "Кто-нибудь, у кого она есть, должен написать команду <code>паутина</code>."
        )
    )
