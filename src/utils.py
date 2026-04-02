from random import choice
from datetime import datetime
from config import bot

async def rndemoji() -> str:
    '''Возвращает случайный эмодзи, олицетворяющий сеть, связь, содружество и т. п.'''
    return choice(["🌐", "🕸️", "⛓️", "🤝"])

async def date_c(date: datetime) -> str:
    '''Получает сырой unix timestamp, возвращает string используя форматирование %c'''
    return datetime.strftime(date, "%c")

async def get_chat_owner(chat_id: int) -> int:
    '''Возвращает TID владельца данного чата'''
    admins = await bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin.status == 'creator':
            owner = admin.user
            return owner
