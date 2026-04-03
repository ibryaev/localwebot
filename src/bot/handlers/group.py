from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION

import bot.keyboards as kb
from config import *
from utils import *
from data import *

rt = Router(name="handlers_group")

@rt.message(F.text == "паутина")
async def mk_chat(message: Message):
    user = message.from_user
    chat_t = message.chat

    if chat_t.type not in ("group", "supergroup"):
        return

    user_id = user.id
    user_username = user.username
    chat_tid = chat_t.id
    chat_owner = await get_chat_owner(chat_tid)
    chat_owner_tid = chat_owner.id

    await db.mk_user(user_id, user_username)
    await db.mk_user(chat_tid, chat_t.username)
    await db.upd_chat_owner(chat_tid, chat_owner_tid)

    chat = await db.get_chat(chat_tid)

    if chat is None:
        web = await db.get_web_tid(user_id)

        if web is None:
            return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывыд

        if user_id != chat_owner_tid:
            return await message.reply(
                # Вывод
                text="Этот чат не состоит ни в какой паутине.",
                reply_markup=await kb.send_invite_to_web(user_id)
            )

        chat = await db.mk_chat(chat_tid, web['web_id'], chat_owner_tid)

        if chat is None:
            return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

        return await message.reply(f"✅ Чат <b>{chat_t.title} </b> успешно добавлен в сетку <b>{web['forename']}</b>!")

        # owner = f"@{owner.username}" or f"<a href='tg://user?id={owner.id}'>{owner.full_name}</a>"
        # user = f"@{user_username}" or f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
        # return await message.reply(
        #     #Вывод
        #     text=(
        #         f"{await rndemoji()} <b>{owner}, обратите внимание!</b>\n{user} предлагает Вам добавить свой чат в его сетку <b></b>"
        #     )
        # )

    # Вывод
    web = await db.get_web_tid(chat_owner_tid)

    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    owner = f"@{chat_owner.username}" or f"<a href='tg://user?id={chat_owner_tid}'>{chat_owner.full_name}</a>"
    date_reg = await date_c(web['date_reg'])

    return await message.reply(
        text=(
            f"{emoji} Этот чат состоит в паутине <b>{forename}</b>\n"
            f"Владелец: <b>{owner}</b> | Дата регистрации: <b>{date_reg}</b>"
        )
    )


@rt.message(F.text == "повысить")
async def up(message: Message):
    chat = message.chat
    
    if chat.type not in ("group", "supergroup"):
        return

    reply = message.reply_to_message

    if not reply:
        return

    owner = await get_chat_owner(chat.id)
    owner_tid = owner.id

    web = await db.get_web_tid(owner_tid)

    if web is None:
        return

    web_id = web['web_id']

    admins = await db.get_web_admins(web_id)
    admins_tid = []
    for admin in admins:
        admins_tid.append(admin['admin_tid'])

    user_id = message.from_user.id

    if user_id not in admins_tid:
        return
    else:
        user_admin = await db.get_admin(user_id, web_id)
        if admin_type_strint[user_admin['post']] < 2:
            return await message.reply("Недостаточно прав.")
        else:
            target_id = reply.from_user.id
            target_admin = await db.get_admin(target_id)

    if message.from_user.id != owner.id:
        return 


@rt.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_transition(event: ChatMemberUpdated) -> None:
    user = event.from_user
    chat = event.chat
    chat_id = chat.id
    chat_owner = await get_chat_owner(chat_id)

    await db.mk_user(user.id, user.username)
    await db.mk_user(chat.id, chat.username)
    await db.upd_chat_owner(chat_id, chat_owner.id)

@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_my_join_transition(event: ChatMemberUpdated):
    chat = event.chat
    chat_id = chat.id
    chat_owner = await get_chat_owner(chat_id)

    await db.mk_user(chat_id, chat.username)
    await db.upd_chat_owner(chat_id, chat_owner.id)

    chat = await db.get_chat(chat_id)

    if chat is not None:
        return await event.answer(">_<") # Вывод

    # Вывод
    await event.answer(
        text=(
            f"{await rndemoji()} <b>Этот чат не состоит ни в какой паутине</b>\n"
             "Кто-нибудь, у кого она есть, должен написать команду <code>паутина</code>."
        )
    )
