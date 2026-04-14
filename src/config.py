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
    # Преобразует тех. название должности админа в пользовательское
    "owner": "Владелец",
    "helper": "Хелпер",
    "admin": "Админ",
    "moder": "Модер",
    "user": "Пользователь"
}
post_intstr = {
    # Преобразует цифру 0-4 в должность админа (по иерархии)
    4: "owner",
    3: "helper",
    2: "admin",
    1: "moder",
    0: "user"
}
post_strint = {
    # Преобразует должность админа в цифру 0-4 (по иерархии)
    "owner": 4,
    "helper": 3,
    "admin": 2,
    "moder": 1,
    "user": 0
}

punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """      # Используется только в transfer_msg_owner_tid() #
cyrillic_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'                                                    # Взяты из библиотеки (модуля)
cyrillic_uppercase = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'                                                    # string и адатированы
cyrillic_letters = cyrillic_lowercase + cyrillic_uppercase # Используется только в transfer_msg_owner_tid() #
