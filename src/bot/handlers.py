from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION

import bot.keyboards as kb
from config import *
from utils import *

rt = Router(name="handlers")

@rt.message(CommandStart(ignore_case=True))
async def cmd_start(message: Message):
    user = message.from_user
    await db.mk_user(user.id, user.username)

    botme = await bot.get_me(60)
    bot_full_name = botme.full_name

    # Вывод
    await message.answer(
        text="⚙️ <i>Установка меню</i>",
        reply_markup=await kb.main_menu()
    )

    await message.answer(
        text=(
            f"{await rndemoji()} <b>{bot_full_name}</b>\n\n"
            "Этот бот позволяет объединить несколько чатов в одну паутину, "
            "позволяя централизировать несколько проектов или объединяться с другими чатами.\n\n"
            "🔨 <b>Глобальный бан:</b> Если забаненный в одном чате человек, "
            "войдёт в другой чат, но из той же сетки, то бот автоматически забанит его и там.\n"
            "🔇 <b>Глобальный мут:</b> Замученный в одном чате человек, не сможет писать сообщения в другой чате, из той же сетки.\n"
            "👟 <b>Глобальный кик:</b> Кик человека из одного чата, кикнет его из всех чатов этой сетки.\n"
            "🛡️ <b>Глобальная модерация:</b> Админ из одного чата, будет админом во всех чатах сетки.\n\n"
            "<b>Один</b> человек может иметь <b>одну</b> паутину,\n"
            "<b>один</b> чат может состоять в <b>одной</b> паутине!\n\n"
            "Создай паутину используя меню, добавляй бота в нужные чаты и пиши там команду <code>паутина</code> 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )


@rt.message(F.text[2:] == "Создать паутину")
@rt.message(F.text[3:] == "Создать паутину")
async def cmd_mk_web(message: Message):
    user = message.from_user
    await db.mk_user(user.id, user.username)

    user = message.from_user
    web = await db.get_web_tid(user.id)

    if web is not None:
        return await message.answer("❌ <b>Ошибка</b>\nУ Вас уже есть паутина.") # Вывод

    web = await db.mk_web(
        forename=user.full_name,
        owner_tid=user.id
    )

    if web is None:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    # Вывод
    forename = web['forename']
    web_id = web['web_id']

    await message.reply(
        text=(
            f"✅ Паутина <b>{forename} (#{web_id})</b> успешно создана!\n\n"
            "Можете заняться её первоначальной настройкой, нажав на кнопку <code>🗂️ Моя паутина</code> "
            "или сразу добавить в неё первые чаты 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text == "➕ Добавить в чат")
async def cmd_add_to_chat(message: Message):
    user = message.from_user
    await db.mk_user(user.id, user.username)

    # Вывод
    await message.answer(
        text="📥 Добавляй бота в нужные чаты и пиши там команду <code>паутина</code>",
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text == "🗂️ Моя паутина")
async def cmd_my_web(message: Message):
    user = message.from_user
    await db.mk_user(user.id, user.username)

    web = await db.get_web_tid(message.from_user.id)

    if web is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    chats_tid = web['chats_tid']
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "В этой сетке нет чатов."
    else:
        seq = 1
        for cid in chats_tid:
            chat = await bot.get_chat(cid)
            chat_username = chat.username
            chat_full_name = chat.full_name
            chat_name = f"<a href='https://t.me/{chat_username}'>{chat_full_name}</a>" if chat_username else chat_full_name
            chats_tid_str += f"<b>{seq}.</b> " + chat_name + "\n"
            seq += 1

    # Вывод
    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    web_id = web['web_id']
    date_reg = await date_c(web['date_reg'])

    await message.answer(
        text=(
            f"{emoji} <b>{forename}</b>\n"
            f"Дата создания: <b>{date_reg}</b> | ID: <b>#{web_id}</b>\n\n"
            "<b>Чаты:</b>\n"
            f"{chats_tid_str}"
        ),
        reply_markup=await kb.web_settings() 
    )


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


@rt.message(F.text == "паутина")
async def cmd_mk_chat(message: Message):
    user = message.from_user
    chat_t = message.chat
    user_id = user.id
    user_username = user.username
    chat_tid = chat_t.id
    chat_towner = await get_chat_owner(chat_tid)
    chat_owner_tid = chat_towner.id

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
    owner = f"@{chat_towner.username}" or f"<a href='tg://user?id={chat_owner_tid}'>{chat_towner.full_name}</a>"
    date_reg = await date_c(web['date_reg'])

    return await message.reply(
        text=(
            f"{emoji} Этот чат состоит в паутине <b>{forename}</b>\n"
            f"Владелец: <b>{owner}</b> | Дата регистрации: <b>{date_reg}</b>"
        )
    )
