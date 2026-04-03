from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from emoji import replace_emoji, is_emoji

from config import *
from utils import *
from bot.data import *
from bot.handlers import cmd_my_web
import bot.keyboards as kb

rt = Router(name="callbacks")
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """

@rt.callback_query(F.data == "rename")
async def rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebRename.new_forename)
    await callback.message.edit_text("Введите новое имя паутины") # Вывод
    return await callback.answer()

@rt.message(WebRename.new_forename)
async def msg_forename(message: Message, state: FSMContext):
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
async def msg_emoji(message: Message, state: FSMContext):
    emoji = message.text

    if not is_emoji(emoji):
        return await message.answer("❌ <b>Ошибка</b>\nВы отправили не эмодзи.") # Вывод

    data = await state.get_data()

    user_id = message.from_user.id
    forename = data['forename']

    await state.clear()

    web = await db.get_web_tid(user_id)

    if web is None:
        return await message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.upd_web_name(web['web_id'], forename, emoji)

    if not result:
        return await message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await cmd_my_web(message) # Вывод


@rt.callback_query(F.data == "admins")
async def cb_admins(callback: CallbackQuery):
    user = callback.from_user
    user_id = user.id
    await db.mk_user(user_id, user.username)

    web = await db.get_web_tid(user_id)

    if web is None:
        return await callback.message.edit_text("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    admins = await db.get_web_admins(web['web_id'])

    # Вывод
    forename = web['forename']

    await callback.message.edit_text(
        text=f"🛡️ Администрация паутины <b>{forename}</b>",
        reply_markup=await kb.admins(admins)
    )
    return await callback.answer()

@rt.callback_query(F.data.startswith("admin_"))
async def cb_admin(callback: CallbackQuery):
    admin_id = callback.data.split("_")[-1]
    admin = await db.get_admin_id(admin_id)
    admin_tid = admin['admin_tid']

    if callback.from_user.id == admin_tid:
        return await callback.answer("Это вы")

    # Вывод
    admin_t = await bot.get_chat(admin_tid)
    admin_username = admin_t.username
    admin_full_name = admin_t.full_name
    admin_name = f"<a href='https://t.me/{admin_username}'>{admin_full_name}</a>" if admin_username else admin_full_name
    post = admin['post']
    date_reg = await date_c(admin['date_reg'])

    await callback.message.edit_text(
        text=(
            f"🛡️ <b>{admin_name}</b> — {admin_type_str[post]}\n"
            f"Был нанят: <b>{date_reg}</b> | ID: <b>#{admin_id}</b>\n\n"
        ),
        reply_markup=await kb.admin(admin_id)
    )
    return await callback.answer()


@rt.callback_query(F.data == "transfer")
async def transfer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    web = await db.get_web_tid(user_id)

    if web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    await state.update_data(web_id=web['web_id'])
    await state.set_state(WebTransferOwnership.new_tid_owner)

    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он должен иметь переписку с ботом)</i>") # Вывод
    return await callback.answer()

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


@rt.callback_query(F.data == "remove")
async def remove(callback: CallbackQuery):
    user_id = callback.from_user.id
    web = await db.get_web_tid(user_id)

    if web is None:
        return await callback.message.answer("❌ Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    if web['chats_tid']:
        return await callback.message.answer("❌ <b>Ошибка</b>\nПеред удалением сетки, Вам нужно удалить из неё все чаты.") # Вывод

    result = await db.rm_web(web['web_id'])

    if not result:
        return await callback.message.answer("❌ <b>Непредвиденная ошибка</b>\nПопробуйте позже.") # Вывод

    await callback.message.edit_text("🗑️ Вы <b>безвозвратно удалили</b> эту паутину!") # Вывод
    return await callback.answer()
