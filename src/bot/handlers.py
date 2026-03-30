from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

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
        text="Установка меню",
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
async def create_web(message: Message):
    await message.reply("1")

@rt.message(F.text == "➕ Добавить в чат")
async def add_to_chat(message: Message):
    await message.answer(
        text="Добавляй бота в нужные чаты и пиши там команду <code>паутина</code> 🕸️",
        reply_markup=await kb.add_to_chat()
    )
