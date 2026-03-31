from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from emoji import replace_emoji, is_emoji

from config import *
import bot.data as data
from bot.handlers import my_web

rt = Router(name="callbacks")

@rt.callback_query(F.data == "web_rename")
async def cb_web_rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(data.WebRename.new_forename)
    await callback.message.edit_text("Введите новое имя паутины:") # Вывод

@rt.message(data.WebRename.new_forename)
async def cb_msg_new_forename(message: Message, state: FSMContext):
    new_forename = replace_emoji(string=message.text, replace="")

    if len(new_forename) > 32:
        return await message.answer(
            # Вывод
            text=(
                 "❌ <b>Ошибка</b>\n"
                 "Имя сетки не должно быть длинее 32 символов и содержать какие-либо эмодзи.\n"
                f"Попробуйте <code>{new_forename[:32]}</code>?"
            )
        )

    await state.update_data(new_forename=new_forename)
    await state.set_state(data.WebRename.new_emoji)

    await message.answer("Отправьте эмодзи, который будет значком этой паутины:") # Вывод

@rt.message(data.WebRename.new_emoji)
async def cb_msg_new_emoji(message: Message, state: FSMContext):
    new_emoji = message.text

    if not is_emoji(new_emoji):
        return await message.answer("❌ <b>Ошибка</b>\nВы отправили не эмодзи.") # Вывод

    data = await state.get_data()

    id_user = message.from_user.id
    new_forename = data["new_forename"]

    await state.clear()

    result = id_web = await db.web_get_id(id_user)

    if result is None:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод
    elif result == -1:
        return await message.answer("❌ <b>Ошибка</b>\nУ Вас нет паутины.") # Вывод

    result = await db.web_rename(id_web, new_forename, new_emoji)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await my_web(message) # Вывод
