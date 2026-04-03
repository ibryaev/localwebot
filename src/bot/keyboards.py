from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
#from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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
        [KeyboardButton(text="🗂️ Моя паутина")],
        [KeyboardButton(text=f"{emoji} Создать паутину", style="success"),
         KeyboardButton(text="➕ Добавить в чат", style="primary")],
        [KeyboardButton(text="📚 Команды")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

async def web_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data="rename")],
        [InlineKeyboardButton(text="🛡️ Администрация", callback_data="admins")],
        [InlineKeyboardButton(text="📤 Передать", callback_data="transfer", style="danger"),
         InlineKeyboardButton(text="🗑️ Удалить", callback_data="remove", style="danger")]
    ])

async def accept_invite_web(user_tid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Принять", callback_data=f"accept_invite_{user_tid}")]
    ])
