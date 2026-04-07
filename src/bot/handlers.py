from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION#, LEAVE_TRANSITION
from aiogram.fsm.context import FSMContext
from asyncio import sleep

from config import *
from utils import *
import bot.keyboards as kb

rt = Router(name="handlers")

@rt.message(CommandStart(ignore_case=True, deep_link=False))
async def introduce(message: Message):
    if message.chat.type != "private":
        return

    user_t = message.from_user
    await db.mk_user(user_t.id, user_t.username)

    # Вывод
    emoji = await rndemoji()

    botme = await bot.get_me()
    bot_full_name = botme.full_name

    await message.answer(
        text="🫆 <i>Установка меню</i>",
        reply_markup=await kb.main_menu()
    )

    await message.answer(
        text=(
            f"{emoji} <b>{bot_full_name}</b>\n\n"
             "Этот бот позволяет объединить несколько чатов в одну паутину, "
             "позволяя централизировать несколько проектов и объединяться с другими чатами.\n\n"
             "🔨 <b>Глобальный бан:</b> Если забаненный в одном чате человек, "
             "войдёт в другой чат, но из той же паутины, то бот автоматически забанит его и там.\n"
             "🔇 <b>Глобальный мут:</b> Замученный в одном чате человек, не сможет писать сообщения в другой чате, из той же паутины.\n"
             "👟 <b>Глобальный кик:</b> Кик человека из одного чата, кикнет его из всех чатов этой паутины.\n"
             "🛡️ <b>Глобальная модерация:</b> Админ из одного чата, будет админом во всех чатах паутины.\n\n"
             "<b>Один</b> человек может иметь <b>одну</b> паутину,\n"
             "<b>один</b> чат может состоять в <b>одной</b> паутине!\n\n"
             "Создай паутину используя меню, добавляй бота в нужные чаты и пиши там команду <code>паутина</code> 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

#########################
#   Главное reply-меню  #
#   kb.main_menu()      #
#########################

# Создание паутины
# В качестве первончального названия паутины
# выступает full_name создателя

@rt.message(F.text[2:] == "Создать паутину")
@rt.message(F.text[3:] == "Создать паутину")
async def mk_web(message: Message):
    if message.chat.type != "private":
        return

    user_t = message.from_user
    user_tid = user_t.id
    await db.mk_user(user_tid, user_t.username)

    web = await db.get_web_tid(user_tid)

    if web is not None:
        return await message.answer("У Вас уже есть паутина.") # Вывод

    web = await db.mk_web(
        forename=user_t.full_name[:32],
        owner_tid=user_tid
    )

    if web is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    forename = web['forename']
    web_id = web['web_id']

    await message.reply(
        text=(
            f"✅ Паутина <b>{forename} (#{web_id})</b> успешно создана!\n\n"
             "Можете заняться её первоначальной настройкой, нажав на кнопку <code>🗂️ Мои паутины</code> "
             "или сразу добавить в неё первые чаты 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

# Добавление бота в чат
# По сути, главная функция этой кнопки - быть наполнением,
# просто чтобы меню красиво смотрелось

@rt.message(F.text == "➕ Добавить в чат")
async def add_to_chat(message: Message):
    if message.chat.type != "private":
        return

    user_t = message.from_user
    await db.mk_user(user_t.id, user_t.username)

    # Вывод
    await message.answer(
        text="📥 Добавляй бота в нужные чаты и пиши там команду <code>паутина</code>",
        reply_markup=await kb.add_to_chat()
    )

# Настройка паутины
# Выводит список чатов, который входят в паутину, 
# и inline-клавиатуру, с кнопками для настройки своей паутины

@rt.message(F.text == "🗂️ Мои паутины")
async def get_web(message: Message):
    if message.chat.type != "private":
        return

    user_t = message.from_user
    user_tid = user_t.id
    await db.mk_user(user_tid, user_t.username)

    web = await db.get_web_tid(user_tid)

    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    msg = await message.answer("Подождите, идёт загрузка...")

    chats_tid = web['chats_tid']
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "<b>В этой паутине нет чатов.</b>"
    else:
        seq = 1
        for chat_tid in chats_tid:
            #chat = await db.get_chat(chat_tid)
            chat_t = await bot.get_chat(chat_tid)
            chat_tusername = chat_t.username
            chat_ttitle = chat_t.title
            chat_tlink = f"<a href='https://t.me/{chat_tusername}'>{chat_ttitle}</a>" if chat_tusername else chat_ttitle
            chats_tid_str += f"{seq}. <b>{chat_tlink}</b>"
            if web['admin_chat_tid'] == chat_tid:
                chats_tid_str += " <i>(адм)</i>"
            chats_tid_str += "\n"
            seq += 1
            await sleep(2.0) # Чтобы Телеграм не жаловался на большое количество обращений. TODO Хранить в БД имя чата

    # Вывод
    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    date_reg = await date_c(web['date_reg'])
    web_id = web['web_id']
    descr = web['descr']
    descr = descr if descr else "Описание отсутствует."

    await msg.edit_text(
        text=(
            f"{emoji} <b>{forename}</b>\n"
            f"Дата создания: <b>{date_reg}</b> | ID: <b>#{web_id}</b>\n"
            f"<blockquote>{descr}</blockquote>\n\n"
             "Чаты:\n"
            f"{chats_tid_str}"
        ),
        reply_markup=await kb.web_settings() 
    )

#################
#   Триггеры    #
#################

@rt.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join_transition(event: ChatMemberUpdated) -> None:
    user_t = event.from_user
    chat_t = event.chat
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)

    await db.mk_user(user_t.id, user_t.username)
    await db.mk_user(chat_tid, chat_t.username)
    await db.upd_chat_owner(chat_tid, chat_owner_t.id)

@rt.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_my_join_transition(event: ChatMemberUpdated):
    chat_t = event.chat
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)

    await db.mk_user(chat_tid, chat_t.username)
    await db.upd_chat_owner(chat_tid, chat_owner_t.id)

    chat = await db.get_chat(chat_tid)

    if chat is not None:
        return await event.answer("&gt;_&lt;") # Вывод (">_<". Особенности HTML)

    # Вывод
    emoji = await rndemoji()

    await event.answer(
        text=(
            f"{emoji} <b>Этот чат не состоит ни в какой паутине</b>\n"
             "Кто-нибудь, у кого она есть, должен написать команду <code>паутина</code>."
        )
    )

#####################################
#   Команды для групповых чатов     #
#####################################

# Выводит информацию о паутине, в которой состоит этот чат
# Но если чат не состоит ни в какой паутине, то:
# 1. Если у человека, который прописывает эту команду, 
#    тоже нет паутины - ответ что чат свободен;
# 2. !1. - к ответу добавляет клавиатура (с одной кнопкой),
#    нажать на которую может только владелец этого чата.
#    Эта кнопка включит этот чат в паутину этого человека;
# 3. Если команду прописал сам владелец чата и у него есть своя паутина -
#    мгновенно включает его чат в его паутину.

@rt.message(F.text.casefold() == "+паутина")
async def mk_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    user_t = message.from_user
    chat_t = message.chat
    user_tid = user_t.id
    user_tusername = user_t.username
    chat_tid = chat_t.id
    chat_owner_t = await get_chat_owner(chat_tid)
    chat_owner_tid = chat_owner_t.id
    chat_owner_tusername = chat_owner_t.username
    chat_owner_tfull_name = chat_owner_t.full_name

    await db.mk_user(user_tid, user_tusername)
    await db.mk_user(chat_tid, chat_t.username)
    await db.mk_user(chat_owner_tid, chat_owner_tusername)
    await db.upd_chat_owner(chat_tid, chat_owner_tid)

    chat = await db.get_chat(chat_tid)

    if chat is None:
        web = await db.get_web_tid(user_tid)
        owner_web = await db.get_web_tid(chat_owner_tid)

        if web is None and owner_web is None:
            return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывыд

        elif web is not None and owner_web is None and user_tid != chat_owner_tid:
            owner_link = f"@{chat_owner_tusername}" if chat_owner_tusername else chat_owner_tfull_name
            return await message.reply(
                # Вывод
                text=f"{owner_link}, этот пользователь предлагает Вам включить свой чат в <b>его</b> паутину.",
                reply_markup=await kb.accept_invite_web(user_tid)
            )

        chat = await db.mk_chat(chat_tid, web['web_id'], chat_owner_tid)

        if chat is None:
            return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

        return await message.reply(f"✅ Чат <b>{chat_t.title}</b> успешно добавлен в паутину <b>{web['forename']}</b>!") # Вывод

    # Вывод
    web_id = chat['web_id']
    web = await db.get_web(web_id)

    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']
    web_owner_tid = web['owner_tid']
    web_owner = await bot.get_chat(web_owner_tid)
    web_owner_username = web_owner.username
    web_owner_full_name = web_owner.full_name
    web_owner_link = f"<a href='https://t.me/{web_owner_username}'>{web_owner_full_name}</a>" if web_owner_username else web_owner_full_name
    if web['heir_tid']:
        web_heir_tid = web['heir_tid']
        web_heir = await bot.get_chat(web_heir_tid)
        web_heir_username = web_heir.username
        web_heir_full_name = web_heir.full_name
        web_heir_link = f"<a href='https://t.me/{web_heir_username}'>{web_heir_full_name}</a>" if web_heir_username else web_heir_full_name
    else:
        web_heir_link = "Отсутствует"
    
    return await message.reply(
        text=(
            f"{emoji} Этот чат состоит в паутине <b>{forename}</b>\n"
            f"Владелец: <b>{web_owner_link}</b> | Наследник: <b>{web_heir_link}</b>"
        ),
        reply_markup=await kb.about(web_id)
    )

# Делает чат, в котором была введена эта команда, админским в этой паутине

@rt.message(F.text.casefold() == "сделать админским")
async def mk_admin_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    user_t = message.from_user
    chat_t = message.chat
    user_tid = user_t.id
    chat_tid = chat_t.id
    await db.mk_user(user_tid, user_t.username)
    await db.mk_user(chat_tid, chat_t.username)

    chat = await db.get_chat(chat_tid)

    if chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    if user_tid != chat['owner_tid']:
        return await message.answer("Только владелец паутины может назначать админский чат.") # Вывод

    web_id = chat['web_id']
    web = await db.get_web(web_id)

    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    if web['admin_chat_tid'] == chat_tid:
        return await message.reply("Этот чат уже и так является админским.") # Вывод

    result = await db.upd_web_admin_chat_tid(web_id, chat_tid)

    if not result:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await message.reply("🛡️ Теперь в этот чат будут приходить глобальные репорты.") # Вывод

##################################
#   Команды для личных чатов     #
##################################

@rt.message(Command("cancel", ignore_case=True))
async def cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state is None:
        return

    await state.clear()

    await message.answer("Активное действие отменено.") # Вывод
