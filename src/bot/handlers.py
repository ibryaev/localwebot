from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
import datetime

import bot.keyboards as kb
from config import *
from utils import *

rt = Router(name="handlers")

@rt.message(CommandStart(ignore_case=True))
@rt.message(F.text == f"помощь")
async def cmd_start_help(message: Message):
    botme = await bot.get_me(60)
    bot_full_name = botme.full_name

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
            "🛡️ <b>Глобальная модерация:</b> Админ из одного чата, будет админом во всех чатах сетки. Подробнее - команда <code>модерация</code>.\n\n"
            "<b>Один</b> человек может иметь <b>одну</b> паутину,\n"
            "<b>один</b> чат может состоять в <b>одной</b> паутине!\n\n"
            "Создай паутину используя меню, добавляй бота в нужные чаты и пиши там команду <code>паутина</code> 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text[2:] == "Создать паутину")
@rt.message(F.text[3:] == "Создать паутину")
async def web_create(message: Message):
    user = message.from_user
    web = await db.web_read(user.id)

    if web is not None:
        return await message.answer("❌ <b>Ошибка</b>\nУ Вас уже есть паутина.") # Вывод

    web = await db.mkweb(
        forename=user.full_name,
        tid_owner=user.id,
        owner_username=user.username
    )

    if web is None:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    # Вывод
    forename = web['forename']
    id_web = web['id_web']

    await message.reply(
        text=(
            f"✅ Паутина <b>\"{forename}\" #{id_web}</b> успешно создана!\n\n"
            "Можете заняться её первоначальной настройкой, нажав на кнопку <code>🗂️ Моя паутина</code> "
            "или сразу добавить в неё первые чаты 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text == "➕ Добавить в чат")
async def add_to_chat(message: Message):
    await message.answer(
        text="📥 Добавляй бота в нужные чаты и пиши там команду <code>паутина</code>",
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text == "🗂️ Моя паутина")
async def my_web(message: Message):
    web = await db.web_read(message.from_user.id)

    if web is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод


    tid_chats = web['tid_chats']
    tid_chats_str = ""
    if not tid_chats:
        tid_chats_str = "<i>Пусто</i>"
    else:
        seq = 1
        for cid in tid_chats:
            chat = await bot.get_chat(cid)
            tid_chats_str += "<b>" + seq + ".</b> " + f"<a href='https://t.me/{chat.username}'>{chat.full_name}</a>\n"
            seq += 1

    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    id_web = web['id_web']
    date_reg = datetime.datetime.strftime(web['date_reg'], "%c")

    await message.answer(
        text=(
            f"{emoji} <b>{forename}</b> #{id_web}\n"
            f"Дата создания: <b>{date_reg}</b>\n\n"
            "<b>Чаты:</b>\n"
            f"{tid_chats_str}"
        ),
        reply_markup=await kb.web_settings() 
    )
