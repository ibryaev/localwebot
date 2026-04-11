from aiogram.types import User
from random import choice
from babel.dates import format_date
from config import bot

async def rndemoji() -> str:
    '''
    Возвращает случайный эмодзи (олицетворение сети, связи, содружества и т. п.):  
    🌐 🕸️ ⛓️ 🤝 🔗 🧩 📡
    '''
    return choice(["🌐", "🕸️", "⛓️", "🤝", "🔗", "🧩", "📡"])

async def parse_date(date: float) -> str:
    '''Получает сырой unix timestamp, возвращает string используя форматирование ``d MMMM, yyyy г.`` (на русском)'''
    return format_date(date, format="d MMMM, yyyy г.", locale="ru")

async def get_chat_owner(chat_tid: int) -> User:
    '''Возвращает владельца данного чата'''
    admins = await bot.get_chat_administrators(chat_tid)
    for admin in admins:
        if admin.status == "creator":
            return admin.user

async def mklink(full_name: str, username: str) -> str:
    return f"<a href='https://t.me/{username}'>{full_name}</a>" if username else full_name
