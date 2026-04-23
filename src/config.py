from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from dotenv import load_dotenv; load_dotenv()
from os import getenv

from database import Database

BOT_TOKEN=getenv('BOT_TOKEN')

DB_HOST=getenv('DB_HOST')
DB_DBNAME=getenv('DB_DBNAME')
DB_PORT=getenv('DB_PORT')
DB_USER=getenv('DB_USER')
DB_PASSWORD=getenv('DB_PASSWORD')

bot = Bot(
    token=BOT_TOKEN,
    session=AiohttpSession(
        # Локальный прокси. Порт указан тот, что используется клиентом Hiddify
        proxy="http://127.0.0.1:12334"
    ),
    default=DefaultBotProperties(
        parse_mode="HTML",
        link_preview_is_disabled=True
    )
)
db = Database()

BOT_TID = 8751189083
BOT_USERNAME = "localwebot"
BOT_FULL_NAME = "Setka (Localweb) — Бот для создания сеток чатов"

post_str = {
    # Преобразует технические названия должности админа в пользовательские
    "owner": "Владелец паутины",
    "heir": "Наследник",
    "admin": "Администратор",
    "adminjr": "Младший администратор",
    "moder": "Модератор",
    "helper": "Помощник",
    "user": "Пользователь"
}
post_strstr = {
    # Преобразует пользовательские названия должности админа в технические
    post_str['owner']: "owner",
    post_str['heir']: "heir",
    post_str['admin']: "admin",
    post_str['adminjr']: "adminjr",
    post_str['moder']: "moder",
    post_str['helper']: "helper",
    post_str['user']: "user"
}
post_intstr = {
    # Преобразует цифру 0-5 в должность админа (по иерархии)
    5: "owner",
    4: "admin",
    3: "adminjr",
    2: "moder",
    1: "helper",
    0: "user"
}
post_strint = {
    # Преобразует должность админа в цифру 0-5 (по иерархии)
    "owner": 5,
    "admin": 4,
    "adminjr": 3,
    "moder": 2,
    "helper": 1,
    "user": 0
}

punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """
cyrillic_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
cyrillic_uppercase = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
cyrillic_letters = cyrillic_lowercase + cyrillic_uppercase
