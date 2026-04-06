from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from emoji import replace_emoji, is_emoji
from asyncio import sleep

from config import *
from utils import *
import bot.keyboards as kb

rt = Router(name="callbacks")

###########################
#   Главное меню          #
#   управления паутиной   #
#   (kb.web_settings())   #
###########################

class WebRename(StatesGroup):
    forename = State()
    emoji = State()
class WebTransferOwnership(StatesGroup):
    owner_tid = State()

admin_type_str = {
    "owner": "Владелец",
    "helper": "Хелпер",
    "admin": "Админ",
    "moder": "Модер"
}
admin_type_intstr = {
    4: "owner",
    3: "helper",
    2: "admin",
    1: "moder"
}
admin_type_strint = {
    "owner": 4,
    "helper": 3,
    "admin": 2,
    "moder": 1
}
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^`{|}~ """
cyrillic_lowercase = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
cyrillic_uppercase = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
cyrillic_letters = cyrillic_lowercase + cyrillic_uppercase

# Переименование паутины
# Два шага FSM: просим новое имя, потом эмодзи,
# и после записываем новые данные в БД

@rt.callback_query(F.data == "rename")
async def rename(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WebRename.forename)

    # Вывод
    await callback.message.edit_text("Введите новое имя паутины")
    return await callback.answer()

@rt.message(WebRename.forename)
async def rename_msg_forename(message: Message, state: FSMContext):
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
    await state.set_state(WebRename.emoji)

    await message.answer("Отправьте эмодзи, который будет значком этой паутины") # Вывод

@rt.message(WebRename.emoji)
async def rename_msg_emoji(message: Message, state: FSMContext):
    emoji = message.text

    if not is_emoji(emoji):
        return await message.answer("Вы отправили не эмодзи. Попробуйте снова.") # Вывод

    data = await state.get_data()

    user_tid = message.from_user.id
    forename = data['forename']

    await state.clear()

    web = await db.get_web_tid(user_tid)

    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.upd_web_name(web['web_id'], forename, emoji)

    if not result:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    old_forename = web['forename']
    old_emoji = web['emoji'] or await rndemoji()

    await message.answer(
        text=(
            "✏️ <b>Паутина была переименована</b>\n"
            f"{old_emoji} {old_forename} → {emoji} {forename}"
        ),
        reply_markup=await kb.go_back()
    )

# Удаление паутины
# но если она ещё содержит какие-то чаты - отвечаем ошибкой
# Да, можно удалять и патину, и чаты и не выводить никакие ошибки,
# но я специально сделал именно так

@rt.callback_query(F.data == "remove")
async def remove(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    if web['chats_tid']:
        # Вывод
        await callback.message.answer("Перед удалением паутины, Вам нужно исключить из неё все чаты.")
        return await callback.answer()

    result = await db.rm_web(web['web_id'])

    if not result:
        # Вывод
        await callback.message.answer("Непредвиденная ошибка. Попробуйте позже.")
        return await callback.answer()

    # Вывод
    await callback.message.edit_text(
        text="🗑️ Вы <b>безвозвратно удалили</b> эту паутину!",
        reply_markup=await kb.go_back()
    )
    return await callback.answer()

# Передача владения над паутиной
# Пользователь вводит юзернейм кому хочет передать свою паутину (один шаг FSM),
# бот проверяет что такой человек вообще существует (по таблице users).
# Если такой человек существует - меняем данные в базе данных.
# punctuation и cyrillic_letters нужны просто чтобы не делать очевидно неправильные запросы

@rt.callback_query(F.data == "transfer")
async def transfer(callback: CallbackQuery, state: FSMContext):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    await state.update_data(web=web)
    await state.set_state(WebTransferOwnership.owner_tid)

    # Вывод
    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он обязан иметь переписку с ботом)</i>")
    return await callback.answer()

@rt.message(WebTransferOwnership.owner_tid)
async def transfer_msg_owner_tid(message: Message, state: FSMContext):
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

#   #   #   #   #   #   #   #   #
#   Панель управления админами  #
#   #   #   #   #   #   #   #   #

async def admin_output(admin: dict, admin_tid: int, post: str, callback: CallbackQuery):
    admin_id = admin['admin_id']
    admin_t = await bot.get_chat(admin_tid)
    admin_tusername = admin_t.username
    admin_tfull_name = admin_t.full_name
    admin_tlink = f"<a href='https://t.me/{admin_tusername}'>{admin_tfull_name}</a>" if admin_tusername else admin_tfull_name
    if admin_tusername:
        admin_tlink = f"<a href='https://t.me/{admin_tusername}'>{admin_tfull_name}</a>"
    else:
        admin_tlink = f"<a href='tg://openmessage?user_id={admin_tid}'>{admin_tfull_name}</a>"
    post = admin_type_str[post]
    restrs_count = admin['restrs_count']
    date_reg = await date_c(admin['date_reg'])

    await callback.message.edit_text(
        text=(
            f"🛡️ <b>{admin_tlink}</b> — <b>{post}</b>\n"
            f"Был нанят: <b>{date_reg}</b> | Выдано наказаний: <b>{restrs_count}</b>\n\n"
        ),
        reply_markup=await kb.admin(admin_id)
    )
    return await callback.answer()


# Отвязывает админский чат от паутины (если он есть)

@rt.callback_query(F.data == "rm_admin_chat")
async def rm_admin_chat(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    web_id = web['web_id']

    if web['admin_chat_tid']:
        admin_chat_tid = web['admin_chat_tid']
    else:
        await callback.answer(
            # Вывод
            text="У Вашей паутины и так нет админского чата.",
            show_alert=True
        )

    admin_chat_t = await bot.get_chat(admin_chat_tid)
    admin_chat_tusername = admin_chat_t.username
    admin_chat_ttitle = admin_chat_t.title
    admin_chat_tlink = f"{admin_chat_ttitle} (@{admin_chat_tusername})" if admin_chat_tusername else admin_chat_ttitle

    result = await db.upd_web_admin_chat_tid(web_id, None)

    if not result:
        return await callback.message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    await callback.answer(
        text=(
            f"Вы отняли у чата {admin_chat_tlink} статус админского. "
             "Теперь у Вашей паутины нет админского чата."
        ),
        show_alert=True
    )

# Список всех админов
# Выводит список всех админов в паутине, где каждый админ - inline-кнпока.
# При нажатии на кнопку админа, показывает панель управления этим конкретным админом

@rt.callback_query(F.data == "admins")
async def admins(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    web_id = web['web_id']
    forename = web['forename']
    heir_tid = web['heir_tid']

    admins = await db.get_web_admins(web_id)

    # Вывод
    await callback.message.edit_text(
        text=f"🛡️ Админы паутины <b>{forename}</b>",
        reply_markup=await kb.admins(admins, heir_tid)
    )
    await callback.answer()

# Управление конкретным админом

@rt.callback_query(F.data.startswith("admin_"))
async def admin(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    admin_id = callback.data.split("_")[-1]
    admin = await db.get_admin_id(admin_id)

    if admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.")
        return await callback.answer()

    admin_tid = admin['admin_tid']

    if user_tid == admin_tid:
        return await callback.answer("Это Вы") # Вывод

    await admin_output(admin, admin_tid, admin['post'], callback) # Вывод

# Повышение конкретного админа

@rt.callback_query(F.data.startswith("up_"))
async def admin_up(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    web_id = web['web_id']
    admin_id = callback.data.split("_")[-1]
    admin = await db.get_admin_id(admin_id)

    if admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.")
        return await callback.answer()

    admin_tid = admin['admin_tid']
    old_post = admin['post']
    user_admin = await db.get_admin(user_tid, web['web_id'])
    user_post = user_admin['post']
    new_post = ""

    if admin_type_strint[user_post] < 3:
        return await callback.answer(f"Недостаточно прав ({admin_type_str[user_post]}/{admin_type_str['helper']})") # Вывод

    if old_post == "owner":
        return await callback.answer(
            # Вывод
            text="Нельзя менять права владельцу чата.",
            show_alert=True
        )
    elif old_post == "helper":
        if admin_type_strint[user_post] <= admin_type_strint[old_post]:
            return await callback.answer(
                # Вывод
                text="Вы не можете менять права админу, который выше или равен Вам.",
                show_alert=True
            )
        else:
            return await callback.answer(
                text=(
                    # Вывод
                    "В одной паутине может быть только один владелец.\n"
                    "Если Вы хотите передать этому человеку права на паутину, то нажмите на соответствующую кнопку."
                ),
                show_alert=True
            )
    elif old_post == "admin":
        if user_post != "owner":
            return await callback.answer(
                # Вывод
                text="Назначать новых хелперов может только владелец паутины.",
                show_alert=True
            )
        else:
            new_post = admin_type_intstr[admin_type_strint[old_post] + 1]
            result = await db.upd_admin_post(admin_tid, web_id, new_post)

            if not result:
                return await callback.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    elif old_post == "moder":
        new_post = admin_type_intstr[admin_type_strint[old_post] + 1]
        result = await db.upd_admin_post(admin_tid, web_id, new_post)

        if not result:
            return await callback.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await admin_output(admin, admin_tid, new_post, callback) # Вывод 

# Понижение конкретного админа

@rt.callback_query(F.data.startswith("down_"))
async def admin_down(callback: CallbackQuery):
    user_tid = callback.from_user.id
    web = await db.get_web_tid(user_tid)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()

    web_id = web['web_id']
    admin_id = callback.data.split("_")[-1]
    admin = await db.get_admin_id(admin_id)

    if admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.")
        return await callback.answer()

    admin_tid = admin['admin_tid']
    old_post = admin['post']
    user_admin = await db.get_admin(user_tid, web['web_id'])
    user_post = user_admin['post']
    new_post = ""

    if admin_type_strint[user_post] < 3:
        return await callback.answer(f"Недостаточно прав ({admin_type_str[user_post]}/{admin_type_str['helper']})") # Вывод

    if old_post == "owner":
        return await callback.answer(
            # Вывод
            text="Нельзя менять права владельцу чата.",
            show_alert=True
        )
    elif old_post == "helper":
        if user_post != "owner":
            return await callback.answer(
                # Вывод
                text="Снимать хелперов может только владелец паутины.",
                show_alert=True
            )
        else:
            new_post = admin_type_intstr[admin_type_strint[old_post] - 1]
            result = await db.upd_admin_post(admin_tid, web_id, new_post)

            if not result:
                return await callback.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    elif old_post == "admin":
        new_post = admin_type_intstr[admin_type_strint[old_post] - 1]
        result = await db.upd_admin_post(admin_tid, web_id, new_post)

        if not result:
            return await callback.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    elif old_post == "moder":
        return await callback.answer(
            text="Если Вы хотите снять этого человека с должности, то нажмите на соответствующую кнопку.",
            show_alert=True
        )

    await admin_output(admin, admin_tid, new_post, callback) # Вывод 

#########################
#   Остальные коллбэки  #
#########################

# Коллбэк-альтернатива хэндлеровскому get_web()

@rt.callback_query(F.data == "get_web")
async def get_web(callback: CallbackQuery):
    user_t = callback.from_user
    user_tid = user_t.id
    await db.mk_user(user_tid, user_t.username)

    web = await db.get_web_tid(user_tid)

    if web is None:
        await callback.message.edit_text("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод
        return await callback.answer()

    await callback.message.edit_text("Подождите, идёт загрузка...")

    chats_tid = web['chats_tid']
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "В этой паутине нет чатов."
    else:
        seq = 1
        for chat_tid in chats_tid:
            chat_t = await bot.get_chat(chat_tid)
            chat_tusername = chat_t.username
            chat_ttitle = chat_t.title
            chat_tlink = f"<a href='https://t.me/{chat_tusername}'>{chat_ttitle}</a>" if chat_tusername else chat_ttitle
            chats_tid_str += f"{seq}. <b>{chat_tlink}</b>\n"
            seq += 1
            await sleep(2.0) # Чтобы Телеграм не жаловался на большое количество обращений

    # Вывод
    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    web_id = web['web_id']
    date_reg = await date_c(web['date_reg'])

    await callback.message.edit_text(
        text=(
            f"{emoji} <b>{forename}</b>\n"
            f"Дата создания: <b>{date_reg}</b> | ID: <b>#{web_id}</b>\n\n"
            "Чаты:\n"
            f"{chats_tid_str}"
        ),
        reply_markup=await kb.web_settings() 
    )
    await callback.answer()

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
