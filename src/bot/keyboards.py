from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder#, ReplyKeyboardBuilder

from config import *
from utils import *

async def add_to_chat() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Добавить в чат",
            url=f"https://t.me/{BOT_USERNAME}?startgroup",
            style='primary'
        )]
    ])

async def main_menu() -> ReplyKeyboardMarkup:
    emoji = await rndemoji()

    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text= "🗂️ Моя паутина")]       ,                    # 1
        [KeyboardButton(text=f"{emoji} Создать паутину", style="success") , # 2
         KeyboardButton(text= "➕ Добавить в чат"      , style="primary")], # 2
        [KeyboardButton(text= "📚 Команды")]                                # 3
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

async def web_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data="rename")],                  # 1
        [InlineKeyboardButton(text="🛡️ Администрация", callback_data="admins")],                  # 2
        [InlineKeyboardButton(text="📤 Передать"     , callback_data="transfer", style="danger"), # 3
         InlineKeyboardButton(text="🗑️ Удалить"      , callback_data="remove"  , style="danger")] # 3
    ])

async def send_invite_to_web(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Отправить предложение", callback_data=f"send_invite_{user_id}")]
    ])

async def admins(admins: list[dict]) -> InlineKeyboardMarkup:
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
            inline_keyboard.add(InlineKeyboardButton(
                text=admin_t.full_name,
                callback_data=f"admin_{admin['admin_id']}"
            ))

    return inline_keyboard.adjust(3).as_markup()

async def admin(admin_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Повысить", callback_data=f"up_{admin_id}", style="success"),   # 1
         InlineKeyboardButton(text="⬇️ Понизить", callback_data=f"down_{admin_id}", style="danger")], # 1
        [InlineKeyboardButton(text="🔥 Снять", callback_data=f"transfer_{admin_id}")],                # 2
        [InlineKeyboardButton(text="👑 Сделать наследником", callback_data=f"heir_{admin_id}"),       # 3
         InlineKeyboardButton(text="📤 Передать права", callback_data=f"transfer_{admin_id}")]        # 3
    ])
