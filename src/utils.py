from aiogram.types import User, Message, CallbackQuery
from random import choice
from datetime import datetime
from babel.dates import format_datetime
from config import *

async def rndemoji() -> str:
    '''
    Возвращает случайный эмодзи (олицетворение сети, связи, содружества и т. п.):  
    🌐 🕸️ ⛓️ 🤝 🔗 🧩 📡
    '''
    return choice(["🌐", "🕸️", "⛓️", "🤝", "🔗", "🧩", "📡"])

async def parse_date(date: float, format: str = "d MMMM, yyyy г.") -> str:
    '''Получает сырой unix timestamp, возвращает string используя форматирование ``d MMMM, yyyy г.`` (на русском)'''
    if date == 1: 
        return "бессрочно"
    
    try:
        date = datetime.fromtimestamp(date)
    except TypeError:
        pass

    return format_datetime(date, format=format, locale="ru")

async def get_chat_owner(chat_tid: int) -> User:
    '''Возвращает владельца данного чата'''
    admins = await bot.get_chat_administrators(chat_tid)
    for admin in admins:
        if admin.status == "creator":
            return admin.user

async def mklink(full_name: str, username: str) -> str:
    return f"<a href='https://t.me/{username}'>{full_name}</a>" if username else full_name

async def parse_time(time_str: str, timestamp: float = None) -> tuple[float, str]:
    '''
    Конвертирует время из формата например "30 мин" в timestamp.  
    Если указать ``timestamp``, то функция вернёт ``timestamp + time_str``. Иначе ``datime.now().timestamp() + time_str``
    '''
    time_str = time_str.split(" ")

    if len(time_str) != 2:
        return None
    if not time_str[0].isdigit():
        return None

    d = int(time_str[0])
    s = time_str[1]
    multiply = 1

    match s.removesuffix("."):
        case "м" | "мин" | "минута" | "минут" | "минуты":
            multiply = 60
            if str(d)[-1] == "1":
                s = "минуту"
            elif str(d)[-1] in ("2", "3", "4"):
                s = "минуты"
            else:
                s = "минут"
        case "ч" | "час" | "часов" | "часа":
            multiply = 3_600
            if str(d)[-1] == "1":
                s = "час"
            elif str(d)[-1] in ("2", "3", "4"):
                s = "часа"
            else:
                s = "часов"
        case "д" | "дн" | "день" | "дня" | "дней":
            multiply = 86_400
            if str(d)[-1] == "1":
                s = "день"
            elif str(d)[-1] in ("2", "3", "4"):
                s = "дня"
            else:
                s = "дней"
        case "н" | "нед" | "неделя" | "неделей" | "недели":
            multiply = 604_800
            if str(d)[-1] == "1":
                s = "неделю"
            elif str(d)[-1] in ("2", "3", "4"):
                s = "недели"
            else:
                s = "неделей"
        case "мес" | "месяц" | "месяцев" | "месяца":
            multiply = 2_592_000
            if str(d)[-1] == "1":
                s = "месяц"
            elif str(d)[-1] in ("2", "3", "4"):
                s = "месяца"
            else:
                s = "месяцев"
        case "год":
            multiply = 31_536_000
            s = "год"
        case _:
            return None

    if timestamp is None:
        timestamp = datetime.now().timestamp()

    date = timestamp + float(d * multiply)
    date_str = f"{d} {s}"

    if date >= timestamp + (31_536_000.0 + 86_400.0):
        date_str = "бессрочно"
    elif date < timestamp + 30.0:
        date = timestamp + 60.0
        date_str = "1 минуту"

    return date, date_str

async def grep_username(text: str, split_sep: str = " ", split_maxsplit: int = -1) -> str:
    '''Парсит текст на начилие ОДНОГО Telegram @юзернейма'''
    text = text.split(split_sep, split_maxsplit)

    for word in text:
        if word.startswith("@"):
            username = word.removeprefix("@")

            for mark in punctuation:
                if mark in username:
                    return None

            for letter in cyrillic_letters:
                if letter in username:
                    return None

            return username

    return None

async def on_every_message(message: Message = None, callback: CallbackQuery = None):
    if bool(message) == bool(callback):
        raise ValueError()

    if message:
        await db.mk_user(user=message.from_user)
        if message.reply_to_message:
            await db.mk_user(user=message.reply_to_message.from_user)
        if message.chat.type in ("group", "supergroup"):
            await db.mk_user(chat=message.chat)

    elif callback:
        await db.mk_user(user=callback.from_user)
        if callback.message.chat.type in ("group", "supergroup"):
            await db.mk_user(chat=callback.message.chat)
