from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from emoji import replace_emoji, is_emoji

from config import *
from bot.data import *
from bot.handlers import cmd_my_web

rt = Router(name="callbacks")
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """

@rt.callback_query(F.data == "rename")
async def cb_rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebRename.new_forename)
    await callback.message.edit_text("Введите новое имя паутины") # Вывод

@rt.message(WebRename.new_forename)
async def cb_msg_new_forename(message: Message, state: FSMContext):
    forename = replace_emoji(message.text, "")

    if len(forename) > 32:
        return await message.answer(
            # Вывод
            text=(
                 "❌ <b>Ошибка</b>\n"
                 "Имя сетки не должно быть длинее 32 символов и содержать какие-либо эмодзи.\n"
                f"Попробуйте <code>{forename[:32]}</code>?"
            )
        )

    await state.update_data(forename=forename)
    await state.set_state(WebRename.new_emoji)

    await message.answer("Отправьте эмодзи, который будет значком этой паутины") # Вывод

@rt.message(WebRename.new_emoji)
async def cb_msg_new_emoji(message: Message, state: FSMContext):
    emoji = message.text

    if not is_emoji(emoji):
        return await message.answer("❌ <b>Ошибка</b>\nВы отправили не эмодзи.") # Вывод

    data = await state.get_data()

    user_id = message.from_user.id
    forename = data['forename']

    await state.clear()

    web = await db.get_web_id(user_id)

    if web is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.upd_web_name(web['web_id'], forename, emoji)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await cmd_my_web(message) # Вывод


@rt.callback_query(F.data == "remove")
async def cb_remove(callback: CallbackQuery):
    user_id = callback.from_user.id
    web = await db.get_web_id(user_id)

    if web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    if web['chats_tid']:
        return await callback.message.answer("❌ <b>Ошибка</b>\nПеред удалением сетки, Вам нужно удалить из неё все чаты.") # Вывод

    result = await db.rm_web(web['web_id'])

    if not result:
        return await callback.message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await callback.message.edit_text("🗑️ Вы <b>безвозвратно удалили</b> эту паутину!") # Вывод


@rt.callback_query(F.data == "transfer")
async def cb_transfer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    web = await db.get_web_id(user_id)

    if web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    await state.update_data(web_id=web['web_id'])
    await state.set_state(WebTransferOwnership.new_tid_owner)

    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он должен иметь переписку с ботом)</i>") # Вывод

@rt.message(WebTransferOwnership.new_tid_owner)
async def cb_msg_new_tid_owner(message: Message, state: FSMContext):
    new_owner_username = message.text.strip("@")

    for mark in punctuation:
        if mark in new_owner_username:
            return await message.answer("❌ <b>Ошибка</b>\nЮзернейм может состоять только из символов <code>A-z</code>, <code>0-9</code> и <code>_</code>.") # Вывод

    data = await state.get_data()

    web_id = data['web_id']
    new_owner_tid = await db.get_tid(new_owner_username)

    await state.clear()

    if new_owner_tid is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод

    is_new_owner_admin = await db.get_admin(new_owner_tid, web_id)

    if is_new_owner_admin is None:
        return await message.answer("❌ <b>Ошибка</b>\nНовый владелец паутины должен обладать в ней хоть какой-нибудь должностью.") # Вывод

    result = await db.upd_web_owner(web_id, message.from_user.id, new_owner_tid)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await message.answer("📤 Теперь эта паутина <b>не принадлежит</b> Вам!") # Вывод
