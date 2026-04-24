from aiogram.types import User, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from random import choice
from datetime import datetime
from babel.dates import format_datetime
from string import digits
from asyncio import sleep
from config import *

async def rndemoji() -> str:
    '''
    Возвращает случайный эмодзи (олицетворение сети, связи, содружества и т. п.):  
    🌐 🕸️ ⛓️ 🤝 🔗 🧩 📡
    '''
    return choice(["🌐", "🕸️", "⛓️", "🤝", "🔗", "🧩", "📡"])

async def parse_date(date: float, format: str = "d MMMM, yyyy г.") -> str:
    '''Получает сырой unix timestamp, возвращает string используя форматирование ``d MMMM, yyyy г.`` (на русском)'''
    try:
        date = datetime.fromtimestamp(date, tz)
    except TypeError:
        if date is None:
            return "бессрочно"
        pass

    return format_datetime(date, format, locale="ru")

async def get_chat_owner(chat_tid: int) -> User:
    '''Возвращает владельца данного чата'''
    admins = await bot.get_chat_administrators(chat_tid)
    for admin in admins:
        if admin.status == "creator":
            return admin.user

async def mklink(full_name: str, username: str) -> str:
    return f"<a href='https://t.me/{username}'>{full_name}</a>" if username else full_name

async def parse_time(time_str: list[str, str], timestamp: float = None) -> tuple[float, str]:
    '''
    Конвертирует время из формата например "30 мин" в timestamp.  
    Если указать ``timestamp``, то функция вернёт ``timestamp + time_str``. Иначе ``datime.now().timestamp() + time_str``
    '''
    time_str = time_str[1].split(" ")

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
        case _:
            return None

    if timestamp is None:
        timestamp = datetime.now(tz).timestamp()

    date = timestamp + float(d * multiply)
    date_str = f"{d} {s}"

    if date >= timestamp + (31_536_000.0 + 86_401.0):
        date_str = "бессрочно"
    elif date < timestamp + 30.0:
        date = timestamp + 60.0
        date_str = "1 минуту"

    return date, date_str

async def grep_username(text: str, no_clean: bool = False, split_sep: str = " ", split_maxsplit: int = -1) -> str:
    '''Парсит текст на начилие ОДНОГО Telegram @юзернейма, который встречается в нём первым'''
    text = text.split(split_sep, split_maxsplit)

    for word in text:
        if word.startswith(("@", "tg://openmessage?user_id=")) or "t.me/" in word:
            username = word.removeprefix("@").removeprefix("tg://openmessage?user_id=").removeprefix("https://t.me/").removeprefix("t.me/")

            for punctuation_mark in punctuation:
                if punctuation_mark in username:
                    return None

            for cyrillic_letter in cyrillic_letters:
                if cyrillic_letter in username:
                    return None

            if username.startswith("_"):
                return None

            if not username.isdigit():
                for digit in digits:
                    if username.startswith(digit):
                        return None

            if no_clean:
                return word

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

async def get_sender_and_target(message: Message) -> tuple[dict, dict]:
    # Создание/поиск отправителя в БД
    sender_user = await db.mk_user(user=message.from_user)

    # Поиск получателя
    target_user = {}
    if message.reply_to_message:
        target_user = await db.mk_user(user=message.reply_to_message.from_user)
    else:
        # Если сообщение не ответ, то парсинг соо
        target_username = await grep_username(message.text.split("\n")[0]) # Попытка найти в тексте @юзернейм (grep_username())
        if target_username is None:
            # @юз не найден
            await message.reply("Нужно ответить на сообщение нужного пользователя или указать в сообщении его @юзернейм или @телеграмайди.") # Вывод
            return None
        elif target_username.isdigit():
            # Если найденный @юз является TID
            target_user = await db.get_user_by_tid(int(target_username)) # Сначала попытка найти в БД
            if target_user is None:
                # Если нет в БД, то обращение к Telegram API методу get_chat()
                await sleep(2)
                try:
                    target_user = await bot.get_chat(target_username)
                except TelegramBadRequest or TelegramForbiddenError or target_user is None and message.chat.type in ("group", "supergroup"):
                    # Если не получилось получить через get_chat(), то,
                    # в случае если это групповой чат, попытка найти человека через метод get_chat_member()
                    await sleep(2)
                    try:
                        target_user = await bot.get_chat_member(message.chat.id, target_username)
                    except TelegramBadRequest or TelegramForbiddenError:
                        target_user = None
        else:
            # @юз найден
            target_user = await db.get_user_by_username(target_username)

    # Проверка на наличие всех нужных записей
    if None in (target_user, sender_user): # LOL      hoiv yv8ty gvgb0ujnu 9hb97yb         --- Серафим даун 4/14/26
        await message.reply("Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод
        return None

    return sender_user, target_user

async def get_chat_and_web(message: Message) -> tuple[dict, dict]:
    # Получение чата из таблиц users & chats
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        await message.reply("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод
        return {}, {}
    # Получаю паутину
    web = await db.get_web(chat['web_id'])
    if web is None:
        await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        return {}, chat

    return chat, web

async def mk_chats_tid_str(chats_tid: list[int], admin_chat_tid: int) -> str:
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "<b>В этой паутине нет чатов.</b>"
    else:
        seq = 1
        for chat_tid in chats_tid:
            chat = await db.get_user_by_tid(chat_tid)
            chat_link = chat['link']
            chats_tid_str += f"{seq}. <b>{chat_link}</b>"
            if admin_chat_tid == chat_tid:
                chats_tid_str += " <i>(адм)</i>"
            chats_tid_str += "\n"
            seq += 1

    return chats_tid_str
