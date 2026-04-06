from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder#, ReplyKeyboardBuilder

from config import *
from utils import *

async def go_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Обратно", callback_data="get_web", style="primary")]
    ])

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
        callback_data=f"about_{web_id}"
    ))
    if is_admin:
        inline_keyboard.add(InlineKeyboardButton(
            text="⬅️ Обратно",
            callback_data="get_web",
            style="primary"
        ))

    return inline_keyboard.adjust(1).as_markup()

async def admins(admins: list[dict], heir_tid: int) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    if not admins:
        inline_keyboard.add(InlineKeyboardButton(
            text="🔄 В этой сетке нет админов.",
            callback_data="admins",
            style="danger"
        ))
    else:
        for admin in admins:
            admin_t = await bot.get_chat(admin['admin_tid'])
            post = admin['post']
            suffix = ""
            if post == "owner":
                prefix = "👑"
            if post == "helper":
                prefix = "3️⃣"
            if post == "admin":
                prefix = "2️⃣"
            if post == "moder":
                prefix = "1️⃣"

            if heir_tid == admin_t.id:
                suffix = " 👑"

            inline_keyboard.add(InlineKeyboardButton(
                text=f"{prefix} {admin_t.full_name}{suffix}",
                callback_data=f"admin_{admin['admin_id']}"
            ))

    inline_keyboard.add(InlineKeyboardButton(
        text="🗑️ Убрать адм. чат",
        callback_data="rm_admin_chat",
        style="primary"
    ))
    inline_keyboard.add(InlineKeyboardButton(
        text="⬅️ Обратно",
        callback_data="get_web",
        style="primary"
    ))

    return inline_keyboard.adjust(2).as_markup()

async def admin(admin_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Повысить", callback_data=f"up_{admin_id}", style="success"),  # 1
         InlineKeyboardButton(text="⬇️ Понизить", callback_data=f"down_{admin_id}", style="danger"), # 1
         InlineKeyboardButton(text="🔥 Снять", callback_data=f"fire_{admin_id}", style="danger")],   # 1
        [InlineKeyboardButton(text="👑 Сделать наследником", callback_data=f"heir_{admin_id}"),      # 2
         InlineKeyboardButton(text="📤 Передать права", callback_data=f"transfer_{admin_id}")],      # 2
        [InlineKeyboardButton(text="⬅️ Обратно", callback_data="admins", style="primary")]           # 3
    ])
