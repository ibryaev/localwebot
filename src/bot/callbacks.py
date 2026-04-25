from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ChatPermissions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from emoji import replace_emoji, is_emoji

from config import *
from utils import *
import bot.keyboards as kb

rt = Router(name="callbacks")

# Отмена активного действия (FSM) (/cancel)
# Отменяет FSM, типа передача прав владельца, переименование паутины и т. д.

@rt.message(Command("cancel", ignore_case=True))
async def cancel(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private": return
    await on_every_message(message=message)

    current_state = await state.get_state()
    if current_state is None:
        return await message.answer("У Вас нет активных действий.") # Вывод

    await state.clear()
    await message.answer("Активное действие отменено.") # Вывод

###########################
#   Главное меню          #
#   управления паутиной   #
#   kb.web_settings()     #
###########################

class WebRename(StatesGroup):
    # rename()
    forename = State()
    emoji = State()
class WebDescription(StatesGroup):
    # about()
    description = State()
class WebTransferOwnership(StatesGroup):
    # transfer()
    owner_tid = State()

# Переименование паутины
# Два шага FSM: просим новое имя, потом эмодзи,
# и после записываем новые данные в БД

@rt.callback_query(F.data == "rename")
async def rename(callback: CallbackQuery, state: FSMContext):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")

    # Вывод
    await state.set_state(WebRename.forename)
    await callback.message.edit_text("Введите новое имя паутины")
    return await callback.answer()

@rt.message(WebRename.forename)
async def rename_msg_forename(message: Message, state: FSMContext):
    forename = replace_emoji(message.text, "")
    if not forename:
        return await message.answer("Имя паутины не должно быть пустым. Попробуйте снова.")
    if len(forename) > 64:
        return await message.answer(
            # Вывод
            text=(
                 "Имя паутины не должно быть длинее 64 символов. Попробуйте снова. "
                f"Может <code>{forename[:64]}</code>?"
            )
        )

    await state.update_data(forename=forename)

    # Вывод
    await state.set_state(WebRename.emoji)
    await message.answer("Отправьте эмодзи, который будет значком этой паутины")

@rt.message(WebRename.emoji)
async def rename_msg_emoji(message: Message, state: FSMContext):
    emoji = message.text
    if not is_emoji(emoji):
        return await message.answer("Вы отправили не эмодзи. Попробуйте снова.") # Вывод

    data = await state.get_data()
    await state.clear()

    user_tid = message.from_user.id
    forename = data['forename']

    web = await db.get_web_by_owner_tid(user_tid)
    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    result = await db.upd_web_name(web['web_id'], forename, emoji)
    if not result: return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

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

# Изменение описания паутины
# Один шаг FSM: просим новое описание
# и после записываем новые данные в БД

@rt.callback_query(F.data == "about")
async def about(callback: CallbackQuery, state: FSMContext):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")

    # Вывод
    await state.set_state(WebDescription.description)
    await callback.message.edit_text("Введите новое описание этой паутины")
    return await callback.answer()

@rt.message(WebDescription.description)
async def about_msg_description(message: Message, state: FSMContext):
    descr = message.text
    if len(descr) > 200:
        return await message.answer(
            # Вывод
            text=(
                 "Описание не должно быть длинее 200 символов. Попробуйте снова. "
                f"Урезанное описание:\n<pre>{descr[:200]}</pre>"
            )
        )

    await state.clear()

    user_tid = message.from_user.id
    web = await db.get_web_by_owner_tid(user_tid)
    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    web_id = web['web_id']

    result = await db.upd_web_descr(web_id, descr)
    if not result: return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    await message.answer(
        text="📃 Описание паутины было изменено.",
        reply_markup=await kb.about(web_id, True)
    )

# Удаление паутины
# но если она ещё содержит какие-то чаты - отвечаем ошибкой
# Да, можно удалять и патину, и чаты и не выводить никакие ошибки,
# но я специально сделал именно так

@rt.callback_query(F.data == "remove")
async def remove(callback: CallbackQuery):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    if web['chats_tid']:
        # Вывод
        await callback.answer(
            text="Перед удалением паутины, Вам нужно исключить из неё все чаты.",
            show_alert=True
        )
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
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    await state.update_data(web=web)

    # Вывод
    await state.set_state(WebTransferOwnership.owner_tid)
    await callback.message.edit_text("Введите @юзернейм нового владельца <i>(он обязан иметь переписку с ботом)</i>")
    return await callback.answer()

@rt.message(WebTransferOwnership.owner_tid)
async def transfer_msg_owner_tid(message: Message, state: FSMContext):
    owner_username = await grep_username(message.text)
    if owner_username is None:
        return await message.answer("Неверный формат. Попробуйте снова.") # Вывод

    data = await state.get_data()
    await state.clear()

    web = data['web']
    web_id = web['web_id']
    owner_tid = await db.get_tid(owner_username)
    if owner_tid is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод

    if await db.get_admin_by_tid(owner_tid, web_id) is None:
        return await message.answer("Новый владелец паутины должен обладать в ней хоть какой-нибудь должностью.") # Вывод
    if await db.get_web_by_owner_tid(owner_tid) is not None:
        return await message.answer("У этого пользователя уже есть своя паутина. Один человек может иметь только одну паутину.") # Вывод

    if not await db.upd_web_owner(web_id, owner_tid, message.from_user.id):
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await message.answer("📤 Теперь эта паутина <b>не принадлежит</b> Вам!") # Вывод

#   #   #   #   #   #   #   #   #
#   Панель управления админами  #
#   #   #   #   #   #   #   #   #

async def admin_output(admin: dict, post: str, heir_tid: int, callback: CallbackQuery):
    '''Функция, которая обновляет сообщение управления конкретным админом'''
    admin_id = admin['admin_id']
    admin_tid = admin['admin_tid']
    admin_db = await db.get_user_by_tid(admin_tid)
    admin_link = admin_db['link'] if admin_db else f"<code>{admin_tid}</code>"
    post = post_str[post]
    heir_text = ""
    if admin_tid == heir_tid:
        heir_text = " 👑"
    restrs_count = admin['restrs_count']
    date_reg = await parse_date(admin['date_reg'])

    await callback.message.edit_text(
        text=(
            f"🛡️ <b>{admin_link}</b> — <b>{post}</b>{heir_text}\n"
            f"Был нанят: <b>{date_reg}</b> | Выдано наказаний: <b>{restrs_count}</b>\n\n"
        ),
        reply_markup=await kb.admin(admin_id)
    )
    return await callback.answer()


# Отвязывает админский чат от паутины (если он есть)

@rt.callback_query(F.data == "rm_admin_chat")
async def rm_admin_chat(callback: CallbackQuery):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    web_id = web['web_id']

    if web['admin_chat_tid']:
        admin_chat_tid = web['admin_chat_tid']
    else:
        return await callback.answer(
            # Вывод
            text="У Вашей паутины и так нет админского чата.",
            show_alert=True
        )

    admin_chat = await db.get_user_by_tid(admin_chat_tid)
    admin_chat_link = admin_chat['username'] if admin_chat["username"] else admin_chat_tid

    result = await db.upd_web_admin_chat_tid(web_id, None)
    if not result:
        # Вывод
        await callback.message.answer("Непредвиденная ошибка. Попробуйте позже.") 
        return await callback.answer()

    # Вывод
    await callback.answer(
        text=(
            f"Вы отняли у чата {admin_chat['full_name']} (@{admin_chat_link}) статус админского. "
             "Теперь у Вашей паутины нет админского чата."
        ),
        show_alert=True
    )
    return await callback.answer()

# Убирает наследника в паутине (если он есть)
# Мгновенно обновляет сообщение, так что у наследника
# сразу пропадёт корона возле имени

@rt.callback_query(F.data == "rm_heir")
async def rm_heir(callback: CallbackQuery):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    web_id = web['web_id']

    if web['heir_tid']:
        heir_tid = web['heir_tid']
    else:
        return await callback.answer(
            # Вывод
            text="У Вашей паутины и так нет наследника.",
            show_alert=True
        )

    heir = await db.get_user_by_tid(heir_tid)
    heir_link = heir['username'] if heir['username'] else heir_tid

    result = await db.upd_web_heir(web_id, None)
    if not result:
        # Вывод
        await callback.message.reply("Непредвиденная ошибка. Попробуйте позже.")
        return await callback.answer()

    # Вывод
    await callback.answer(
        text=(
            f"Вы отняли у пользователя {heir['full_name']} (@{heir_link}) статус наследника. "
             "Теперь у Вашей паутины нет наследника."
        ),
        show_alert=True
    )
    await admins(callback)

# Список всех админов
# Выводит список всех админов в паутине, где каждый админ - inline-кнпока.
# При нажатии на кнопку админа, показывает панель управления этим конкретным админом

@rt.callback_query(F.data == "admins")
async def admins(callback: CallbackQuery):
    await on_every_message(callback=callback)

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    # Вывод
    web_id = web['web_id']
    forename = web['forename']
    owner_tid = web['owner_tid']
    heir_tid = web['heir_tid']
    admins = await db.get_web_admins(web_id)

    # Вывод
    try:
        await callback.message.edit_text(
            text=f"🛡️ Админы паутины <b>{forename}</b>",
            reply_markup=await kb.admins(admins, owner_tid, heir_tid)
        )
        await callback.answer()
    except TelegramBadRequest:
        await callback.answer("Новых админов не появилось")

# Управление конкретным админом
# kb.admin()

@rt.callback_query(F.data.startswith("admin_"))
async def admin(callback: CallbackQuery):
    await on_every_message(callback=callback)
    user_tid = callback.from_user.id

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    admin_id = callback.data.split("_")[-1]
    admin = await db.get_admin(admin_id)

    if admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.")
        return await callback.answer()

    admin_tid = admin['admin_tid']

    if user_tid == admin_tid:
        return await callback.answer("Это Вы") # Вывод

    await admin_output(admin, admin['post'], web['heir_tid'], callback) # Вывод

# Повышение конкретного админа
# Повышать админов можно начиная с ранга хелпера.
# Он же может повышать модераторов до админов.
# Но понижать или снимать хелперов может только владелец паутины

@rt.callback_query(F.data.startswith("up_"))
async def admin_up(callback: CallbackQuery):
    sender_tid = callback.from_user.id
    target_id = callback.data.split("_")[-1]

    target_admin = await db.get_admin(target_id)
    if target_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этого админа не существует",
            show_alert=True
        )
        return await callback.message.delete()
    web = await db.get_web(target_admin['web_id'])
    if web is None:
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этой паутины не существует"
        )
        return await callback.message.delete()
    web_id = web['web_id']
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо вы не админ",
            show_alert=True
        )
        return await callback.message.delete()

    sender_post = sender_admin['post']
    sender_post_str = post_str[sender_post]
    target_tid = target_admin['admin_tid']
    target_old_post = target_admin['post']

    # Проверка прав
    ## Проверка на то, что отправитель имеет достаточный ранг
    if post_strint[sender_post] < 3:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['adminjr']})",
            show_alert=True
        )

    # Иерархические проверки
    if target_old_post == "owner":
        return await callback.answer(
            # Вывод
            text="Нельзя менять права владельцу паутины.",
            show_alert=True
        )

    elif target_old_post == "admin":
        if sender_post != "owner":
            return await callback.answer(
                # Вывод
                text=(f"Недостаточно прав ({sender_post_str}/{post_str['owner']})"),
                show_alert=True
            )
        else:
            return await callback.answer(
                # Вывод
                text=(
                    "В одной паутине может быть только один владелец.\n"
                    "Если Вы хотите передать этому человеку права на паутину, то сделайте это через админ-панель."
                ),
                show_alert=True
            )

    elif target_old_post == "adminjr" and sender_post != "owner":
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['owner']})",
            show_alert=True
        )

    elif post_strint[target_old_post] >= 2 and post_strint[sender_post] < 4:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['admin']})",
            show_alert=True
        )

    target_new_post = post_intstr[post_strint[target_old_post] + 1]
    result = await db.upd_admin_post(target_tid, web_id, target_new_post)
    if not result: return await callback.answer(
        # Вывод
        text="Непредвиденная ошибка. Попробуйте позже",
        show_alert=True
    )

    # Вывод
    await callback.answer(f"⬆️ Повышен до {post_str[target_new_post]}а")
    await admin_output(target_admin, target_new_post, web['heir_tid'], callback)

# Понижение конкретного админа
# Понижать админов можно начиная с ранга хелпера.
# Он же может понижать админов до модераторов.

@rt.callback_query(F.data.startswith("down_"))
async def admin_down(callback: CallbackQuery):
    sender_tid = callback.from_user.id
    target_id = callback.data.split("_")[-1]

    target_admin = await db.get_admin(target_id)
    if target_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этого админа не существует",
            show_alert=True
        )
        return await callback.message.delete()
    web = await db.get_web(target_admin['web_id'])
    if web is None:
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этой паутины не существует"
        )
        return await callback.message.delete()
    web_id = web['web_id']
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо вы не админ",
            show_alert=True
        )
        return await callback.message.delete()

    sender_post = sender_admin['post']
    sender_post_str = post_str[sender_post]
    target_tid = target_admin['admin_tid']
    target_old_post = target_admin['post']

    # Проверка прав
    ## Проверка на то, что отправитель имеет достаточный ранг
    if post_strint[sender_post] < 3:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав (<b>{sender_post_str}</b>/<b>{post_str['adminjr']}</b>).",
            show_alert=True
        )

    ## Нужно проверить, вдруг у цели есть чаты в этой паутине
    await db.cur.execute(
        "SELECT * FROM chats WHERE owner_tid = %s AND web_id = %s",
        (target_tid, web_id)
    )
    is_target_have_chats = await db.cur.fetchall()
    if is_target_have_chats and post_strint[target_old_post] <= 3:
        return await callback.answer(
            # Вывод
            text=(
                f"У этого пользователя есть чаты в паутине. Его нельзя снять или понизить на должность ниже {post_str['adminjr']}. "
                 "Для начала исключите его чаты из паутины."
            ),
            show_alert=True
        )

    # Иерархические проверки
    if target_old_post == "owner":
        return await callback.answer(
            # Вывод
            text="Нельзя менять права владельцу паутины.",
            show_alert=True
        )

    elif target_old_post == "admin" and sender_post != "owner":
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['owner']})",
            show_alert=True
        )

    elif target_old_post == "adminjr" and post_strint[sender_post] < 4:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['admin']})",
            show_alert=True
        )

    elif target_old_post == "helper":
        return await admin_fire(callback) # Вывод

    target_new_post = post_intstr[post_strint[target_old_post] - 1]
    result = await db.upd_admin_post(target_tid, web_id, target_new_post)
    if not result: return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    await callback.answer(f"⬇️ Понижен до {post_str[target_new_post]}а")
    await admin_output(target_admin, target_new_post, web['heir_tid'], callback) # Вывод

# Снятие конкретного админа
# Снимать админов можно начиная с ранга хелпера.
# Понижать или снимать хелперов может только владелец паутины

@rt.callback_query(F.data.startswith("fire_"))
async def admin_fire(callback: CallbackQuery):
    sender_tid = callback.from_user.id
    target_id = callback.data.split("_")[-1]

    target_admin = await db.get_admin(target_id)
    if target_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этого админа не существует",
            show_alert=True
        )
        return await callback.message.delete()
    web = await db.get_web(target_admin['web_id'])
    if web is None:
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо этой паутины не существует"
        )
        return await callback.message.delete()
    web_id = web['web_id']
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо непредвиденная ошибка, либо вы не админ",
            show_alert=True
        )
        return await callback.message.delete()

    sender_post = sender_admin['post']
    sender_post_str = post_str[sender_post]
    target_tid = target_admin['admin_tid']
    target_old_post = target_admin['post']
    heir_tid = web['heir_tid']

    # Проверка прав
    ## Проверка на то, что отправитель имеет достаточный ранг
    if post_strint[sender_post] < 3:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав (<b>{sender_post_str}</b>/<b>{post_str['adminjr']}</b>).",
            show_alert=True
        )

    ## Нужно проверить, вдруг у цели есть чаты в этой паутине
    await db.cur.execute(
        "SELECT * FROM chats WHERE owner_tid = %s AND web_id = %s",
        (target_tid, web_id)
    )
    is_target_have_chats = await db.cur.fetchall()
    if is_target_have_chats and post_strint[target_old_post] <= 3:
        return await callback.answer(
            # Вывод
            text=(
                f"У этого пользователя есть чаты в паутине. Его нельзя снять или понизить на должность ниже {post_str['adminjr']}. "
                 "Для начала исключите его чаты из паутины."
            ),
            show_alert=True
        )

    # Иерархические проверки
    if target_old_post == "owner":
        return await callback.answer(
            # Вывод
            text="Нельзя менять права владельцу паутины.",
            show_alert=True
        )

    elif target_old_post == "admin" and sender_post != "owner":
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['owner']})",
            show_alert=True
        )

    elif target_old_post == "adminjr" and post_strint[sender_post] < 4:
        return await callback.answer(
            # Вывод
            text=f"Недостаточно прав ({sender_post_str}/{post_str['admin']})",
            show_alert=True
        )

    if heir_tid == target_tid:
        # Если админ является наследником, то снять его может только владелец паутины.
        # После снятия наследника также показ предупреждения
        if sender_post != "owner":
            return await callback.answer(
                # Вывод
                text=f"Снять <b>{post_str['heir']}а</b> может только <b>{post_str['owner']}</b>.",
                show_alert=True
            )
        await db.upd_web_heir(web_id, None)
        await callback.answer(
            text=f"Предупреждение: этот админ являлся {post_str['heir']}ом. Не забудьте назначить нового.",
            show_alert=True
        )

    result = await db.rm_admin(target_tid, web_id)
    if not result: return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    await admins(callback) # Вывод
    await callback.answer(f"🔥 Снят")

# Сделать конкретного админа наследником
# Назначать наследника паутины может только её владелец

@rt.callback_query(F.data.startswith("heir_"))
async def admin_heir(callback: CallbackQuery):
    sender_tid = callback.from_user.id
    target_id = callback.data.split("_")[-1]

    target_admin = await db.get_admin(target_id)
    if target_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.",
            show_alert=True
        )
        return await callback.message.delete()
    web = await db.get_web(target_admin['web_id'])
    if web is None:
        await callback.answer(
            text="Произошла либо <b>непредвиденная ошибка</b>, либо <b>этой паутины не существует</b>."
        )
        return await callback.message.delete()
    web_id = web['web_id']
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Вывод
        await callback.answer(
            text="Произошла либо <b>непредвиденная ошибка</b>, либо <b>вы не админ</b>.",
            show_alert=True
        )
        return await callback.message.delete()

    target_tid = target_admin['admin_tid'] # TID цели

    if sender_admin['post'] != "owner":
        return await callback.answer(
            # Вывод
            text="Только владелец может назначать наследника паутины.",
            show_alert=True
        )

    if target_tid == web['heir_tid']:
        return await callback.answer(
            text="Этот человек уже и так является наследником.",
            show_alert=True
        )

    result = await db.upd_web_heir(web_id, target_tid)
    if not result: return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    await admin_output(target_admin, target_admin['post'], target_tid, callback) # Вывод

# Передать права владельния паутиной другому админу
# Передавать право владения паутиной может только её владелец

@rt.callback_query(F.data.startswith("transfer_"))
async def admin_transfer(callback: CallbackQuery):
    user_tid = callback.from_user.id
    admin_id = callback.data.split("_")[-1]

    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if callback.from_user.id != web['owner_tid']:
            return await callback.answer(f"Это действие может произвести только {post_str['owner']}")
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()
    web_id = web['web_id']
    admin = await db.get_admin(admin_id)
    user_admin = await db.get_admin_by_tid(user_tid, web_id)

    if web is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
        return await callback.answer()
    if admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этого админа не существует</b>.")
        return await callback.answer()
    if user_admin is None:
        # Вывод
        await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>вы не админ в этой сетке</b>.")
        return await callback.answer()

    owner_tid = web['owner_tid']
    admin_tid = admin['admin_tid']
    user_post = user_admin['post']

    if user_post != "owner":
        return await callback.answer(
            # Вывод
            text="Вы не владелец этой паутины.",
            show_alert=True
        )

    if admin_tid == owner_tid:
        # Технически невозможное условие
        return await callback.answer(
            text="Вы и так являетесь владельцем.",
            show_alert=True
        )

    if await db.get_web_by_owner_tid(admin_tid) is not None:
        return await callback.answer(
            text="У этого администратора уже есть своя паутина.",
            show_alert=True
        )

    result = await db.upd_web_owner(web_id, admin_tid, user_tid)

    if not result: return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    # Вывод
    await callback.message.answer("📤 Теперь эта паутина <b>не принадлежит</b> Вам!")
    await callback.message.delete()

#############################################
#   Жалобы                                  #
#   kb.report_user() и kb.report_admin()    #
#############################################

# 

@rt.callback_query(F.data.startswith("ban_"))
async def report_gban(callback: CallbackQuery):
    report_id = callback.data.split("_")[-1]
    report = await db.get_report(report_id)

    # Создание/поиск отправителя в БД
    sender_user = await db.mk_user(user=callback.from_user)

    # Поиск получателя
    target_tid = report['target_tid']
    target_user = await db.get_user_by_tid(target_tid) # Жалобы подаются только на сообщения, так что цель гарантированно есть в БД

    # Проверка на наличие всех нужных записей
    if None in (target_user, sender_user):
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    sender_tid = sender_user['tid'] # TID отправителя

    # Если человек нажимает на кнопку наказания на жалобе, отправленной на него же, то оскорбляем его жирную мамашу
    if sender_tid == target_tid:
        return await callback.answer(
            # Вывод
            text=choice([
                "Я слышал твоя мама села на айфон и он стал айпадом",
                "Твоя мамка такая жирная, что у неё есть собственный почтовый индекс",
                "Если долго смотреть на небо, то можно увидеть созвездие твоей жирной мамаши",
                "Твоя мама настолько жирная, что когда она нагибается все думают что это вход в метро",
                "Твоя мама нормальная и вовсе не жирная",
                "твоя мама настолько жирная что ей нужно искать свою задницу в справочнике"
            ]),
            show_alert=True
        )

    # Получение чата из таблиц users & chats
    chat_chat = await db.get_chat(callback.message.chat.id) # Жалобы подаются только в чатах, которые состоят в паутине, так что цель гарантированно есть в БД
    if chat_chat is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    # Получаю паутину
    web = await db.get_web(chat_chat['web_id'])
    if web is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    chat_tid = callback.message.chat.id # TID чата
    web_id = web['web_id']              # ID паутины

    # Проверка, вдруг у получателя уже есть активное наказание
    target_restr = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    for restr in target_restr:
        if restr['restr'] != "ban":
            continue

        # Если искомое наказание было найдено
        # Вывод
        # text callback.answer() должен быть не более 200 символов.
        admin_user = await db.get_user_by_tid(restr['admin_tid'])
        admin_mention = admin_user['full_name'] if len(admin_user['full_name']) <= 16 else admin_user['full_name'][:13] + "..." # 16 символов под full_name админа
        date_until = await parse_date(restr['date_until'], "HH:mm d MMMM") if restr['date_until'] else "бессрочно" # 12 символов
        if date_until:
            date_until = date_until if len(date_until) <= 12 else date_until[:9] + "..."
        reason = restr['reason'] if len(restr['reason']) <= 145 else restr['reason'][:142] + "..." # Базовый текст + admin_mention + date_until = 55 символов. На причину остаётся 145 символов
        return await callback.answer(
            text=(
                f"Уже забанен. Выдал {admin_mention} до {date_until}. \"{reason}\""
            ),
            show_alert=True
        )

    # Проверка прав
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 2:
        # Если запись в таблице admin не была найдена, это значит что пользователь не админ (логично)
        return await callback.answer("Недостаточно прав") # Вывод

    # Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Наказать модератора может админ. Наказать админа может хелпер. Хелпер и владелец не могут быть наказаны
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("helper", "owner"):
            return await callback.answer(f"Нельзя наказать {post_str['helper']}а или {post_str['owner'][:-2]}ца.") # Вывод
        if target_admin_post == "admin" and post_strint[sender_admin_post] < 3:
            return await callback.answer("Недостаточно прав")  # Вывод
        if target_admin_post == "moder" and post_strint[sender_admin_post] < 2:
            return await callback.answer("Недостаточно прав")  # Вывод

    # Устаналивание причины
    reason = f"Жалоба  #{report['report_id']}: \"{report['reason'] or "[ВЛОЖЕНИЕ]"}\""

    # Непосредственное назначение наказания
    ## Запись в БД
    restr = await db.mk_restr(web_id, target_tid, "ban", sender_tid, reason)
    if restr is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод
    if target_admin:
        result = await db.rm_admin(target_tid, web_id) # Если целевой пользователь являлся админом, то снимаем его
        if result is None:
            # Вывод
            await callback.answer(
                text="Человек успешно забанен, но по неизвестной причине с него не удалось снять админские права. Сделайте это вручную.",
                show_alert=True
            )
    await db.upd_plus_restrs_count(sender_tid, web_id, sender_admin['restrs_count'])

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.ban_chat_member(
                chat_id=chat_tid,
                user_id=target_tid
            )
        except Exception: # Если бота нет в чате или нет прав
            continue
        await sleep(2)

    # Вывод
    await callback.message.reply(
        f"⛔ {target_user['link']}, глобальный бан в паутине чатов <b>{web['forename']}</b> на <b>бессрочно</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Выдал {sender_user['link']}\n"
        f"<blockquote>{reason}</blockquote>"
    )
    await callback.answer()

@rt.callback_query(F.data.startswith("mute_"))
async def report_gmute(callback: CallbackQuery):
    report_id = callback.data.split("_")[-1]
    report = await db.get_report(report_id)

    # Создание/поиск отправителя в БД
    sender_user = await db.mk_user(user=callback.from_user)

    # Поиск получателя
    target_tid = report['target_tid']
    target_user = await db.get_user_by_tid(target_tid) # Жалобы подаются только на сообщения, так что цель гарантированно есть в БД

    # Проверка на наличие всех нужных записей
    if None in (target_user, sender_user):
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    sender_tid = sender_user['tid'] # TID отправителя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await callback.answer("Нельзя взаимодействовать с самим собой")

    # Получение чата из таблиц users & chats
    chat_chat = await db.get_chat(callback.message.chat.id) # Жалобы подаются только в чатах, которые состоят в паутине, так что цель гарантированно есть в БД
    if chat_chat is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    # Получаю паутину
    web = await db.get_web(chat_chat['web_id'])
    if web is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод

    chat_tid = callback.message.chat.id # TID чата
    web_id = web['web_id']              # ID паутины

    # Проверка, вдруг у получателя уже есть активное наказание
    target_restr = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    for restr in target_restr:
        if restr['restr'] != "mute":
            continue

        # Если искомое наказание было найдено
        # Вывод
        # text callback.answer() должен быть не более 200 символов.
        admin_user = await db.get_user_by_tid(restr['admin_tid'])
        admin_mention = admin_user['full_name'] if len(admin_user['full_name']) <= 16 else admin_user['full_name'][:13] + "..." # 16 символов под full_name админа
        date_until = await parse_date(restr['date_until'], "HH:mm d MMMM") if restr['date_until'] else "бессрочно" # 12 символов
        if date_until:
            date_until = date_until if len(date_until) <= 12 else date_until[:9] + "..."
        reason = restr['reason'] if len(restr['reason']) <= 144 else restr['reason'][:141] + "..." # Базовый текст + admin_mention + date_until = 56 символов. На причину остаётся 145 символов
        return await callback.answer(
            text=(
                f"Уже замьючен. Выдал {admin_mention} до {date_until}. \"{reason}\""
            ),
            show_alert=True
        )

    # Проверка прав
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Если запись в таблице admin не была найдена, это значит что пользователь не админ (логично)
        return await callback.answer("Недостаточно прав") # Вывод

    # Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Наказать модератора может админ. Наказать админа может хелпер. Хелпер и владелец не могут быть наказаны
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("helper", "owner"):
            return await callback.answer(f"Нельзя наказать {post_str['helper']}а или {post_str['owner'][:-2]}ца.") # Вывод
        if target_admin_post == "admin" and post_strint[sender_admin_post] < 3:
            return await callback.answer("Недостаточно прав")  # Вывод
        if target_admin_post == "moder" and post_strint[sender_admin_post] < 2:
            return await callback.answer("Недостаточно прав")  # Вывод

    # Устаналивание причины
    reason = f"Жалоба  #{report['report_id']}: \"{report['reason'] or "[ВЛОЖЕНИЕ]"}\""

    # Непосредственное назначение наказания
    ## Запись в БД
    restr = await db.mk_restr(web_id, target_tid, "mute", sender_tid, reason)
    if restr is None:
        return await callback.answer("Непредвиденная ошибка. Попробуйте позже") # Вывод
    await db.upd_plus_restrs_count(sender_tid, web_id, sender_admin['restrs_count'])

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.restrict_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_audios=False,
                    can_send_documents=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_video_notes=False,
                    can_send_voice_notes=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_edit_tag=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_manage_topics=False
                ),
                use_independent_chat_permissions=True
            )
        except Exception: # Если бота нет в чате или нет прав
            continue
        await sleep(2)

    # Вывод
    await callback.message.reply(
        f"🔇 {target_user['link']}, глобальный мут в паутине чатов <b>{web['forename']}</b> на <b>бессрочно</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Выдал {sender_user['link']}\n"
        f"<blockquote>{reason}</blockquote>"
    )
    await callback.answer()

# Отмечает жалобу проверенной

@rt.callback_query(F.data.startswith("check_"))
async def report_check(callback: CallbackQuery):
    report_id = callback.data.split("_")[-1]
    report = await db.get_report(report_id)
    if report is None:
        await callback.answer("Жалоба не найдена")
        return await callback.message.delete()
    sender_tid = report['sender_tid']
    target_tid = report['target_tid']
    sender = await db.get_user_by_tid(sender_tid)
    target = await db.get_user_by_tid(target_tid)
    admin  = await db.mk_user(callback.from_user)

    web_id = report['web_id']
    web = await db.get_web(web_id)
    web_admin_chat_tid = web['admin_chat_tid']

    if callback.message.chat.id != web_admin_chat_tid:
        admins_tid = await db.get_web_admins_tid(web_id)
        if callback.from_user.id not in admins_tid:
            return await callback.answer("У Вас недостаточно прав") # Вывод

    result = await db.rm_report(report_id)
    if not result:
        return await callback.answer(
            # Вывод
            text="Непредвиденная ошибка. Попробуйте позже.",
            show_alert=True
        )

    # Вывод
    try:
        chat_user = await db.get_user_by_tid(report['chat_tid'])

        await bot.edit_message_text(
            chat_id=web_admin_chat_tid,
            message_id=report['message_tid_bot_admin'],
            text=(
                f"✅ Жалоба на {target['link']} проверена (#{report['report_id']})\n"
                f"🆔 <code>@{target_tid}</code>\n"
                f"🗣 Отправил {sender['link']} из чата {chat_user['link']}\n"
                f"🛡️ Проверил {admin['link']}\n"
                f"<blockquote>{report['reason']}</blockquote>"
            )
        )
        await bot.edit_message_text(
            chat_id=report['chat_tid'],
            message_id=report['message_tid_bot_user'],
            text=f"✅ Жалоба проверена (#{report['report_id']})"
        )
        await callback.answer()
    except TelegramBadRequest:
        pass

# Удаляет сообщение, на которое была подана жалоба

@rt.callback_query(F.data.startswith("rmmes_"))
async def report_rmmes(callback: CallbackQuery):
    report_id = callback.data.split("_")[-1]
    report = await db.get_report(report_id)
    web_id = report['web_id']

    admins_tid = await db.get_web_admins_tid(web_id)
    if callback.from_user.id not in admins_tid:
        return await callback.answer("У Вас недостаточно прав") # Вывод

    try:
        await bot.delete_message(
            chat_id=report['chat_tid'],
            message_id=report['message_tid_user_replyto']
        )
    except Exception:
        await callback.answer("Уже и так") # Вывод
    await callback.answer("✅") # Вывод

#########################
#   Остальные коллбэки  #
#########################

# Коллбэк-альтернатива хэндлеровскому get_web()

@rt.callback_query(F.data == "get_web")
async def get_web(callback: CallbackQuery):
    await on_every_message(callback=callback)

    # Получение данных из БД
    user = await db.mk_user(user=callback.from_user)
    if callback.message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(callback.message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
    elif callback.message.chat.type == "private":
        web = await db.get_web_by_owner_tid(callback.from_user.id)
        if web is None:
            # Вывод
            await callback.message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.")
            return await callback.answer()

    # Вывод
    emoji = web['emoji'] or await rndemoji()
    owner_tid = web['owner_tid']
    owner = await db.get_user_by_tid(owner_tid)
    if web['heir_tid']:
        heir = await db.get_user_by_tid(web['heir_tid'])
        heir_link = heir['link']
    else:
        heir_link = "Отсутствует"
    descr = web['descr'] or "Описание отсутствует."
    date_reg = await parse_date(web['date_reg'])
    chats_tid_str = await mk_chats_tid_str(web['chats_tid'], web['admin_chat_tid'])

    await callback.message.edit_text(
        text=(
            f"{emoji} <b>{web['forename']}</b> (#{web['web_id']})\n"
            f"Владелец: <b>{owner['link']}</b> | Наследник: <b>{heir_link}</b>\n"
            f"Дата создания: <b>{date_reg}</b>\n"
            f"<blockquote>{descr}</blockquote>\n\n"
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

    web = await db.get_web_by_owner_tid(user_tid)
    web_id = web['web_id']
    chat = await db.mk_chat(chat_tid, web_id, chat_owner_tid)

    if chat is None:
        await callback.message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        return await callback.answer()

    await db.mk_admin(chat_owner_tid, web_id, "adminjr")

    # Вывод
    await callback.message.edit_text("✅ Это предложение было принято!")
    await callback.message.answer(f"✅ Чат <b>{chat_t.title}</b> успешно добавлен в паутину <b>{web['forename']}</b>!")
    await callback.answer()

# Чтение описания паутины

@rt.callback_query(F.data.startswith("about_"))
async def about_web_id(callback: CallbackQuery):
    await on_every_message(callback=callback)

    web_id = callback.data.split("_")[-1]
    # Получение данных из БД
    web = await db.get_web(web_id)
    if web is None:
        return await callback.answer("Произошла либо непредвиденная ошибка, либо этой паутины более не существует.") # Вывод

    descr = web['descr']
    descr = descr if descr else "Описание отсутствует."

    # Вывод
    await callback.answer(
        text=descr,
        show_alert=True
    )
