from aiogram import Router
from aiogram.types import ChatMemberUpdated, ChatPermissions, User
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION

from config import *
from utils import *

rt = Router()

@rt.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_transition(event: ChatMemberUpdated) -> None:
    chat_tid = event.chat.id
    user_tid = event.from_user.id

    await db.mk_user(user=event.from_user)
    await db.mk_user(chat=event.chat)

    chat_chat = await db.get_chat(event.chat.id)
    if chat_chat is None: return
    user_user = await db.get_user_by_tid(user_tid)

    user_restrs = await db.get_restrs_by_user_tid_in_web(user_tid, chat_chat['web_id'])
    for restr in user_restrs:
        if restr['restr'] == "ban":
            try:
                await bot.ban_chat_member(
                    chat_id=chat_tid,
                    user_id=user_tid,
                    until_date=restr['date_until']
                )
                await event.answer(f"⛔ <b>{user_user['link']} забанен в паутине!</b> Я его уже прогнал 😎")
            except Exception: # Если у бота нет прав
                continue
        if restr['restr'] == "mute":
            try:
                await bot.restrict_chat_member(
                    chat_id=chat_tid,
                    user_id=user_tid,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_edit_tag=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_manage_topics=False
                    ),
                    use_independent_chat_permissions=True,
                    until_date=restr['date_until']
                )
                await event.answer(f"🔇 <b>{user_user['link']}</b> замьючен в паутине.")
            except Exception: # Если у бота нет прав
                continue

@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_my_join_transition(event: ChatMemberUpdated):
    chat_tid = event.chat.id

    chat_administrators = await bot.get_chat_administrators(chat_tid)
    for admin in chat_administrators:
        await db.mk_user(user=admin.user)
        if admin.status == "creator":
            await db.upd_chat_owner(chat_tid, admin.user.id)
    
    await db.mk_user(chat=event.chat)

    chat = await db.get_chat(chat_tid)
    if chat is not None:
        return await event.answer("&gt;_&lt;") # Вывод (">_<". Особенности HTML)

    # Вывод
    await event.answer(
        text=(
            f"{await rndemoji()} <b>Этот чат не состоит ни в какой паутине</b>\n"
             "Кто-нибудь, у кого она есть, должен написать команду <code>+паутина</code>."
        )
    )
