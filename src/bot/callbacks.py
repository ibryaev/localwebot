from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from emoji import replace_emoji, is_emoji

from config import *
from bot.data import *
from bot.handlers import my_web

rt = Router(name="callbacks")
#punctuation = ["!", "\"", "#", "$", "%", "&", "\'", "(", ")", "*", "+", ",", "-", ".", "/", ":", ;<=>?@[\]^_`{|}~"""]
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """

@rt.callback_query(F.data == "rename")
async def cb_rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebRename.new_forename)
    await callback.message.edit_text("Введите новое имя паутины") # Вывод

@rt.message(WebRename.new_forename)
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
    await state.set_state(WebRename.new_emoji)

    await message.answer("Отправьте эмодзи, который будет значком этой паутины") # Вывод

@rt.message(WebRename.new_emoji)
async def cb_msg_new_emoji(message: Message, state: FSMContext):
    new_emoji = message.text

    if not is_emoji(new_emoji):
        return await message.answer("❌ <b>Ошибка</b>\nВы отправили не эмодзи.") # Вывод

    data = await state.get_data()

    id_user = message.from_user.id
    new_forename = data['new_forename']

    await state.clear()

    id_web = await db.web_get_id(id_user)

    if id_web is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.web_rename(id_web, new_forename, new_emoji)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await my_web(message) # Вывод


@rt.callback_query(F.data == "remove")
async def cb_remove(callback: CallbackQuery):
    id_user = callback.from_user.id
    web = await db.web_get(id_user)

    if web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    if web['tid_chats']:
        return await callback.message.answer("❌ <b>Ошибка</b>\nПеред удалением сетки, Вам нужно удалить из неё все чаты.") # Вывод

    result = await db.rmweb(web['id_web'])

    if not result:
        return await callback.message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await callback.message.edit_text("🗑️ Вы <b>безвозвратно удалили</b> эту паутину!") # Вывод


@rt.callback_query(F.data == "transfer")
async def cb_transfer(callback: CallbackQuery, state: FSMContext):
    id_user = callback.from_user.id
    id_web = await db.web_get_id(id_user)

    if id_web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    await state.update_data(id_web=id_web)
    await state.set_state(WebTransferOwnership.new_tid_owner)

    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он должен иметь переписку с ботом)</i>") # Вывод

@rt.message(WebTransferOwnership.new_tid_owner)
async def cb_msg_new_tid_owner(message: Message, state: FSMContext):
    new_owner_username = message.text.strip("@")

    for mark in punctuation:
        if mark in new_owner_username:
            return await message.answer("❌ <b>Ошибка</b>\nЮзернейм может состоять только из символов <code>A-z</code>, <code>0-9</code> и <code>_</code>.") # Вывод

    data = await state.get_data()

    id_web = data['id_web']
    new_tid_owner = await db.get_tid(new_owner_username)

    await state.clear()

    if new_tid_owner is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод

    is_new_owner_admin = await db.admin_get(id_web, new_tid_owner)

    if is_new_owner_admin is None:
        return await message.answer("❌ <b>Ошибка</b>\nНовый владелец паутины должен обладать в ней хоть какой-нибудь должностью.") # Вывод

    result = await db.web_transfer_ownership(id_web, message.from_user.id, new_tid_owner)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await message.answer("📤 Теперь эта паутина <b>не принадлежит</b> Вам!") # Вывод
