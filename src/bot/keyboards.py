from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder#, ReplyKeyboardBuilder

from config import *
from utils import *

################
#    Кнопки    #
################

async def button_go_back(inline_keyboard: InlineKeyboardBuilder) -> InlineKeyboardButton:
    return inline_keyboard.add(InlineKeyboardButton(
        text="⬅️ Обратно",
        callback_data="get_web",
        style="primary"
    ))

####################
#    Клавиатуры    #
####################

prefixes = {
    "owner": "🤴",
    "admin": "4️⃣",
    "adminjr": "3️⃣",
    "moder": "2️⃣",
    "helper": "1️⃣",
}

 # # # # # # # # # #

async def go_back() -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()
    await button_go_back(inline_keyboard)
    return inline_keyboard.as_markup()

async def add_to_chat() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Добавить в чат",
            url=f"https://t.me/{BOT_USERNAME}?startgroup",
            style="primary"
        )]
    ])

async def main_menu() -> ReplyKeyboardMarkup:
    emoji = await rndemoji()

    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text= "🗂️ Мои паутины")]       ,                    # 1
        [KeyboardButton(text=f"{emoji} Создать паутину", style="success") , # 2
         KeyboardButton(text= "➕ Добавить в чат"      , style="primary")], # 2
        [KeyboardButton(text= "📚 Команды")]                                # 3
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

async def web_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data="rename"),                   # 1
         InlineKeyboardButton(text="📃 Изменить описание", callback_data="about")],               # 1
        [InlineKeyboardButton(text="🛡️ Администрация", callback_data="admins")],                  # 2
        [InlineKeyboardButton(text="📤 Передать"     , callback_data="transfer", style="danger"), # 3
         InlineKeyboardButton(text="🗑️ Удалить"      , callback_data="remove"  , style="danger")] # 3
    ])

async def accept_invite_web(user_tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Принять", callback_data=f"accept_invite_{user_tid}")]
    ])

async def about(web_id: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    inline_keyboard.add(InlineKeyboardButton(
        text="ℹ️ О паутине",
        callback_data=f"about_{web_id}",
        style="primary"
    ))
    if is_admin:
        await button_go_back(inline_keyboard)

    return inline_keyboard.adjust(1).as_markup()

async def admins(admins: list[dict], owner_tid: int, heir_tid: int) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    if not admins or (len(admins) == 1 and admins[0]['admin_tid'] == owner_tid):
        # Если админов нет (среди админов числится только владелец паутины)
        inline_keyboard.row(InlineKeyboardButton(
            text="🔄 Админов нет",
            callback_data="admins",
            style="danger"
        ))

    else:
        for admin in admins:
            admin_tid = admin['admin_tid']
            
            admin_db = await db.get_user_by_tid(admin_tid)
            admin_name = admin_db['full_name'] if admin_db else str(admin_tid) # Если админа нет в бд таблице users (по сути технически невозможно), то просто показываю его TID
            
            post = admin['post']
            prefix = prefixes[post]
            suffix = " 👑" if admin_tid == heir_tid else ""

            inline_keyboard.add(InlineKeyboardButton(
                text=f"{prefix} {admin_name}{suffix}",
                callback_data=f"admin_{admin['admin_id']}"
            ))
        
        # Сначала выравниваем только кнопки админов по 2 в ряд
        inline_keyboard.adjust(2)

    inline_keyboard.row( # Только что выучил новую функцию для клавиатур в aiogram - row()
        InlineKeyboardButton(text="👑 Убрать наследника", callback_data="rm_heir", style="danger"),
        InlineKeyboardButton(text="🗯 Убрать адм. чат", callback_data="rm_admin_chat", style="danger"),
        width=2
    )

    await button_go_back(inline_keyboard)

    return inline_keyboard.as_markup()

async def admin(admin_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Повысить", callback_data=f"up_{admin_id}", style="success"),  # 1
         InlineKeyboardButton(text="⬇️ Понизить", callback_data=f"down_{admin_id}", style="danger"), # 1
         InlineKeyboardButton(text="🔥 Снять", callback_data=f"fire_{admin_id}", style="danger")],   # 1
        [InlineKeyboardButton(text="👑 Сделать наследником", callback_data=f"heir_{admin_id}"),      # 2
         InlineKeyboardButton(text="📤 Передать права", callback_data=f"transfer_{admin_id}")],      # 2
        [InlineKeyboardButton(text="⬅️ Обратно", callback_data="admins", style="primary")]           # 3
    ])

async def report_admin(report_id: str) -> InlineKeyboardMarkup:
    report = await db.get_report(report_id)
    chat_tid_clear = str(report['chat_tid']).removeprefix("-100")
    link = f"https://t.me/c/{chat_tid_clear}/{report['message_tid_bot_user']}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сообщение", url=link)],                                        # 1
        [InlineKeyboardButton(text="✅ Отметить", callback_data=f"check_{report_id}", style="success")]             # 2
    ])

async def report_user(report_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Бан", callback_data=f"ban_{report_id}"),                    # 1
         InlineKeyboardButton(text="🔇 Мут", callback_data=f"mute_{report_id}"),                   # 1
         InlineKeyboardButton(text="➖ Сообщение", callback_data=f"rmmes_{report_id}")],           # 1
        [InlineKeyboardButton(text="✅ Отметить", callback_data=f"check_{report_id}", style="success")]             # 2
    ])
