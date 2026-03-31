from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder#, ReplyKeyboardBuilder

from config import *
from utils import *

async def add_to_chat() -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Добавить в чат",
            url=f"https://t.me/{BOT_USERNAME}?startgroup",
            style='primary'
        )]
    ])

    return inline_keyboard

async def main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🗂️ Моя паутина")],
        [KeyboardButton(text=f"{await rndemoji()} Создать паутину", style="success"), #
         KeyboardButton(text="➕ Добавить в чат", style="primary")],                  # 
        [KeyboardButton(text="📚 Помощь")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

    return keyboard

async def web_settings() -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data="web_rename"),       #
         InlineKeyboardButton(text="❌ Удалить", callback_data="rmweb", style="danger")], #
        [InlineKeyboardButton(text="🛡️ Администрация", callback_data="admins")]
    ])

    return inline_keyboard
