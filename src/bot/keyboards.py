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
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🗂️ Моя паутина")],
        [KeyboardButton(text=f"{await rndemoji()} Создать паутину", style="success"), #
         KeyboardButton(text="➕ Добавить в чат", style="primary")],                  # 
        [KeyboardButton(text="📚 Команды")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

async def web_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data="rename")],
        [InlineKeyboardButton(text="🛡️ Администрация", callback_data="admins")],
        [InlineKeyboardButton(text="📤 Передать", callback_data="transfer", style="danger"), #
         InlineKeyboardButton(text="🗑️ Удалить", callback_data="remove", style="danger")]    #
    ])

async def send_invite_to_web(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Отправить предложение", callback_data=f"send_invite_{user_id}")]
    ])
