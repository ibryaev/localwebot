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

BOT_USERNAME = "localwebot"
BOT_FULL_NAME = "Setka (Localweb) — Бот для создания сеток чатов"
