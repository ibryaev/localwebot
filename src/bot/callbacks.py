from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from emoji import replace_emoji, is_emoji

from config import *
from utils import *
from bot.data import *
import bot.handlers as handlers

rt = Router(name="callbacks")

###########################
#   Главное меню          #
#   управления паутиной   #
#   (kb.web_settings())   #
###########################

punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """
cyrillic_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
cyrillic_uppercase = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
cyrillic_letters = cyrillic_lowercase + cyrillic_uppercase

# Переименование паутины
# Два шага FSM: просим новое имя, потом эмодзи,
# и после записываем новые данные в БД

@rt.callback_query(F.data == "rename")
async def rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebRename.new_forename)
    await callback.message.edit_text("Введите новое имя паутины") # Вывод
    return await callback.answer()

@rt.message(WebRename.new_forename)
async def msg_rename_forename(message: Message, state: FSMContext):
    forename = replace_emoji(message.text, "")

    if len(forename) > 32:
        return await message.answer(
            # Вывод
            text=(
                 "Имя паутины не должно быть длинее 32 символов. Попробуйте снова."
                f"Может <code>{forename[:32]}</code>?"
            )
        )

    await state.update_data(forename=forename)
    await state.set_state(WebRename.new_emoji)

    await message.answer("Отправьте эмодзи, который будет значком этой паутины") # Вывод

@rt.message(WebRename.new_emoji)
async def msg_rename_emoji(message: Message, state: FSMContext):
    emoji = message.text

    if not is_emoji(emoji):
        return await message.answer("Вы отправили не эмодзи. Попробуйте снова.") # Вывод

    data = await state.get_data()

    user_id = message.from_user.id
    forename = data['forename']

    await state.clear()

    web = await db.get_web_tid(user_id)

    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.upd_web_name(web['web_id'], forename, emoji)

    if not result:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await handlers.get_web(message) # Вывод

# Удаление паутины
# но если она ещё содержит какие-то чаты - отвечаем ошибкой
# Да, можно удалять и патину, и чаты и не выводить никакие ошибки,
# но я специально сделал именно так

@rt.callback_query(F.data == "remove")
async def remove(callback: CallbackQuery):
    user_id = callback.from_user.id
    web = await db.get_web_tid(user_id)

    if web is None:
        return await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    if web['chats_tid']:
        return await callback.message.answer("Перед удалением паутины, Вам нужно исключить из неё все чаты.") # Вывод

    result = await db.rm_web(web['web_id'])

    if not result:
        return await callback.message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await callback.message.edit_text("🗑️ Вы <b>безвозвратно удалили</b> эту паутину!") # Вывод
    return await callback.answer()

# Передача владения над паутиной
# Пользователь вводит юзернейм кому хочет передать свою паутину (один шаг FSM),
# бот проверяет что такой человек вообще существует (по таблице users).
# Если такой человек существует - меняем данные в базе данных.
# punctuation и cyrillic_letters нужны просто чтобы не делать очевидно неправильные запросы

@rt.callback_query(F.data == "transfer")
async def transfer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    web = await db.get_web_tid(user_id)

    if web is None:
        return await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    await state.update_data(web=web)
    await state.set_state(WebTransferOwnership.new_tid_owner)

    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он обязан иметь переписку с ботом)</i>") # Вывод
    return await callback.answer()

@rt.message(WebTransferOwnership.new_tid_owner)
async def cb_msg_new_tid_owner(message: Message, state: FSMContext):
    new_owner_tusername = message.text.strip("@")
    error_wrong_username_format = False

    for mark in punctuation:
        if mark in new_owner_tusername:
            error_wrong_username_format = True
    for letter in cyrillic_letters:
        if letter in new_owner_tusername:
            error_wrong_username_format = True
    if error_wrong_username_format:
        return await message.answer("Неверный формат. Попробуйте снова.") # Вывод

    data = await state.get_data()

    web = data['web']
    web_id = web['web_id']
    new_owner_tid = await db.get_tid(new_owner_tusername)

    await state.clear()

    if new_owner_tid is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод

    is_new_owner_admin = await db.get_admin(new_owner_tid, web_id)

    if is_new_owner_admin is None:
        return await message.answer("Новый владелец паутины должен обладать в ней хоть какой-нибудь должностью.") # Вывод

    result = await db.upd_web_owner(web_id, message.from_user.id, new_owner_tid)

    if not result:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await message.answer("📤 Теперь эта паутина <b>не принадлежит</b> Вам!") # Вывод

#########################
#   Остальные коллбэки  #
#########################

# Владелец чата принял запрос на вступление в чужую паутину
# Также делает владельца этого чата хелпером в этой паутине

@rt.callback_query(F.data.startswith("accept_invite_"))
async def accept_invite(callback: CallbackQuery):
    user_tid = callback.data.split("_")[-1]
    chat_t = callback.message.chat
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)
    chat_owner_tid = chat_owner_t.id

    if callback.from_user.id != chat_owner_tid:
        return await callback.answer("Вы не владелец этого чата") # Вывод

    chat = await db.get_chat(chat_tid)

    if chat:
        await callback.message.edit_text("Предложение устарело.") # Вывод
        return await callback.answer()

    web = await db.get_web_tid(user_tid)
    web_id = web['web_id']
    chat = await db.mk_chat(chat_tid, web_id, chat_owner_tid)

    if chat is None:
        await callback.message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        return await callback.answer()

    await db.mk_admin(chat_owner_tid, web_id, "helper")

    # Вывод
    await callback.message.edit_text("✅ Это предложение было принято!")
    await callback.message.answer(f"✅ Чат <b>{chat_t.title}</b> успешно добавлен в паутину <b>{web['forename']}</b>!")
    await callback.answer()
