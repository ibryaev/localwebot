from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder#, ReplyKeyboardBuilder

from config import *
from utils import *

async def add_to_chat() -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardBuilder()

    inline_keyboard.add(InlineKeyboardButton(
        text="➕ Добавить в чат",
        url=f"https://t.me/{BOT_USERNAME}?startgroup",
        style='primary'
    ))

    return inline_keyboard.as_markup()

async def main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=f"{await rndemoji()} Создать паутину", style="success"), KeyboardButton(text="➕ Добавить в чат", style="primary")],
        [KeyboardButton(text="🗂️ Моя паутина")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите опцию..."
    )

    return keyboard
