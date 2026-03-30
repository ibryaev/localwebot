from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

bot = Bot(
    token="8751189083:AAEaYJgYQAAjVJ3cCpwutYsyxUmHjF2SAJ0",
    session=AiohttpSession(
        # Локальный прокси. Порт указан тот, что используется клиентом Hiddify
        proxy="http://127.0.0.1:12334"
    ),
    default=DefaultBotProperties(
        parse_mode="HTML",
        link_preview_is_disabled=True
    )
)

BOT_USERNAME = "localwebot"
