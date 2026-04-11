from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import *
from utils import *
import bot.keyboards as kb

rt = Router(name="handlers")

@rt.message(CommandStart(ignore_case=True, deep_link=False))
async def introduce(message: Message):
    if message.chat.type != "private":
        return

    await db.mk_user(user=message.from_user)

    # Вывод
    emoji = await rndemoji()

    await message.answer(
        text="🫆 <i>Установка меню</i>",
        reply_markup=await kb.main_menu()
    )

    await message.answer(
        text=(
            f"{emoji} <b>{BOT_FULL_NAME}</b>\n\n"
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

# @rt.message(F.text.casefold() == "кинг" | "пинг" | "пиу" | "бот" | "пиф")
@rt.message(F.text.casefold() == "кинг")
@rt.message(F.text.casefold() == "пинг")
@rt.message(F.text.casefold() == "пиу")
@rt.message(F.text.casefold() == "бот")
@rt.message(F.text.casefold() == "пиф")
async def ping(message: Message):
    text = message.text.lower()
    reply = ""

    match text:
        case "кинг":
            reply = "конг"
        case "пинг":
            reply = "понг"
        case "пиу":
            reply = "пау"
        case "бот":
            reply = "✅ На месте"
        case "пиф":
            reply = "паф"

    await message.reply(reply.title())

###############################################
#   Главное reply-меню                        #
#   kb.main_menu()                            #
#   Все эти команды вызываются только в ЛС.   #
###############################################

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

    await db.mk_user(user=user_t)

    # Если у пользователя уже есть паутина
    web = await db.get_web_by_owner_tid(user_tid)
    if web is not None:
        return await message.answer("У Вас уже есть паутина.") # Вывод

    # Непосредственное создание паутины
    web = await db.mk_web(user_t.full_name, user_tid)

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

# Кнока добавления бота в чат
# По сути, главная функция этой кнопки - быть наполнением,
# просто чтобы меню красиво смотрелось

@rt.message(F.text == "➕ Добавить в чат")
async def add_to_chat(message: Message):
    if message.chat.type != "private":
        return

    await db.mk_user(user=message.from_user)

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

    await db.mk_user(user=user_t)

    # Если у пользователя нет паутины
    web = await db.get_web_by_owner_tid(user_t.id)

    if web is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

    msg = await message.answer("Подождите, идёт загрузка...")

    # Формируем список чатов
    chats_tid = web['chats_tid']
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "<b>В этой паутине нет чатов.</b>"
    else:
        seq = 1
        for chat_tid in chats_tid:
            chat = await db.get_user_by_tid(chat_tid)
            if chat is None:
                chat_link = chat_tid
            else:
                chat_link = chat['link']
            chats_tid_str += f"{seq}. <b>{chat_link}</b>"
            if web['admin_chat_tid'] == chat_tid:
                chats_tid_str += " <i>(адм)</i>"
            chats_tid_str += "\n"
            seq += 1

    # Вывод
    web_id = web['web_id']
    forename = web['forename']
    emoji = web['emoji'] or await rndemoji()
    descr = web['descr'] or "Описание отсутствует."
    date_reg = await parse_date(web['date_reg'])

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

#####################################
#   Команды для групповых чатов     #
#####################################

# Добавление чата в паутину (+паутина)
# Записывает чат в БД и привязывает к паутине пользователя.
# Если команду вводит не владелец чата — отправляет предложение владельцу.

@rt.message(F.text.casefold() == "+паутина")
async def add_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    user_t = message.from_user
    chat_t = message.chat
    chat_owner_t = await get_chat_owner(chat_t.id)

    user_tid = user_t.id
    chat_tid = chat_t.id
    chat_owner_tid = chat_owner_t.id

    await db.mk_user(user=user_t)
    await db.mk_user(chat=chat_t)
    await db.mk_user(user=chat_owner_t)
    await db.upd_chat_owner(chat_tid, chat_owner_tid)

    chat = await db.get_chat(chat_tid)
    user_web = await db.get_web_by_owner_tid(user_tid)
    chat_owner_web = await db.get_web_by_owner_tid(chat_owner_tid)

    if chat:
        return await get_chat(message) # Вывод

    else:
        if user_tid != chat_owner_tid:
            if user_web is None:
                return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывод

            else:
                chat_owner_tusername = chat_owner_t.username
                chat_owner_tfull_name = chat_owner_t.full_name
                chat_owner_link = f"@{chat_owner_tusername}" if chat_owner_tusername else chat_owner_tfull_name
                return await message.reply(
                    # Вывод
                    text=f"{chat_owner_link}, этот пользователь предлагает Вам включить свой чат в <b>его</b> паутину.",
                    reply_markup=await kb.accept_invite_web(user_tid)
                )

        else:
            if chat_owner_web is None:
                return await message.reply("У Вас нет паутины. Сначала создайте её в ЛС с ботом.") # Вывод

            else:
                chat_ttitle = chat_t.title
                chat_owner_web_forename = chat_owner_web['forename']
                
                chat = await db.mk_chat(chat_tid, chat_owner_web['web_id'], chat_owner_tid)

                if chat is None:
                    return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

                return await message.reply(f"✅ Чат <b>{chat_ttitle}</b> успешно добавлен в паутину <b>{chat_owner_web_forename}</b>!") # Вывод

# Удаление чата из паутины (-паутина)
# Убирает привязку чата к текущей паутине в БД.
# Совершить действие может либо владелец самого чата, либо владелец паутины.

@rt.message(F.text.casefold() == "-паутина")
async def rm_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    user_t = message.from_user
    chat_t = message.chat
    chat_owner_t = await get_chat_owner(chat_t.id)

    user_tid = user_t.id
    chat_tid = chat_t.id
    chat_owner_tid = chat_owner_t.id

    await db.mk_user(user=user_t)
    await db.mk_user(chat=chat_t)
    await db.mk_user(user=chat_owner_t)
    await db.upd_chat_owner(chat_tid, chat_owner_tid)

    chat = await db.get_chat(chat_tid)

    if chat is None:
        return await message.reply("Этот чат и так не состоит ни в какой паутине.") # Вывод

    web_id = chat['web_id']
    web = await db.get_web(web_id)
    
    if web is None:
        return await message.reply("Непредвиденная ошибка. Паутина не найдена.") # Вывод
        
    web_owner_tid = web['owner_tid']
    web_forename = web['forename']

    # Удалить чат из сетки может либо владелец самого чата, либо владелец паутины
    if user_tid == chat_owner_tid or user_tid == web_owner_tid:
        result = await db.rm_chat(chat_tid, web_id)

        if not result:
            return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

        return await message.reply(f"🗑 Чат успешно удалён из паутины <b>{web_forename}</b>.") # Вывод
    else:
        return await message.reply("У Вас нет прав для удаления этого чата из паутины.") # Вывод

# Информация о паутине чата (паутина)
# Выводит карточку с данными паутины, к которой привязан текущий чат:
# эмодзи, название, юзернейм владельца и наследника.

@rt.message(F.text.casefold() == "паутина")
async def get_chat(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    user_t = message.from_user
    chat_t = message.chat
    chat_owner_t = await get_chat_owner(chat_t.id)

    chat_tid = chat_t.id

    await db.mk_user(user=user_t)
    await db.mk_user(chat=chat_t)
    await db.mk_user(user=chat_owner_t)
    await db.upd_chat_owner(chat_tid, chat_owner_t.id)

    chat = await db.get_chat(chat_tid)

    if chat is None:
        return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывод

    web_id = chat['web_id']
    web = await db.get_web(web_id)
    
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    web_emoji = web['emoji'] or await rndemoji()
    web_forename = web['forename']

    web_owner_tid = web['owner_tid']
    web_owner = await db.get_user_by_tid(web_owner_tid)
    web_owner_link = web_owner['link']

    if web['heir_tid']:
        web_heir_tid = web['heir_tid']
        web_heir = await db.get_user_by_tid(web_heir_tid)
        web_heir_link = web_heir['link']
    else:
        web_heir_link = "Отсутствует"
    
    return await message.reply(
        # Вывод
        text=(
            f"{web_emoji} Этот чат состоит в паутине <b>{web_forename}</b>\n"
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

    await db.mk_user(user=user_t)
    await db.mk_user(chat=chat_t)

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

#

@rt.message(F.text.startswith("жалоба"))
@rt.message(F.text.startswith(".жалоба")) # Для тех, кто привык к Ирис боту
@rt.message(F.text.startswith("репорт"))  # Для тех, кто привык к Ирис боту
@rt.message(F.text.startswith(".репорт")) # Для тех, кто привык к Ирис боту
async def report(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.reply_to_message:
        return await message.reply("Жалобу нужно подать в ответ на сообщение.") # Вывод

    sender = message.from_user
    target = message.reply_to_message.from_user

    await db.mk_user(user=sender)
    await db.mk_user(user=target)

    sender_tid = sender.id
    target_tid = target.id

    if sender_tid == target_tid:
        return

    chat = await db.get_chat(message.chat.id)

    if chat is None:
        return await message.reply("Этот чат не привязан ни к какой паутине.") # Вывод

    web_id = chat['web_id']

    web = await db.get_web(web_id)
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    if not web['admin_chat_tid']:
        return await message.reply("У сетки, в которой состоит этот чат, нет админского чата.") # Вывод

    message_user = await message.reply("Подождите, идёт загрузка...")
    message_admin = await bot.send_message(
        chat_id=web['admin_chat_tid'],
        text="Подождите, идёт загрузка..."
    )

    report = await db.mk_report(web_id, message, message_admin.message_id, message_user.message_id)
    if not report:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    report_id = report['report_id']

    await message_user.edit_text(
        text=(
            f"❗️ Жалоба на {await mklink(target.full_name, target.username)} отправлена\n"
            f"🆔 <code>{target_tid}</code>\n"
            f"🗣 Отправил {await mklink(sender.full_name, sender.username)}\n"
            f"<blockquote>{report['reason']}</blockquote>"
        ),
        reply_markup=await kb.report_user(report_id)
    )
    await message_admin.edit_text(
        text=(
            f"❗️ Жалоба на {await mklink(target.full_name, target.username)}\n"
            f"🆔 <code>{target_tid}</code>\n"
            f"🗣 Отправил {await mklink(sender.full_name, sender.username)}\n"
            f"<blockquote>{report['reason']}</blockquote>"
        ),
        reply_markup=await kb.report_admin(report_id)
    )

# 
@rt.message(F.text.startswith("чаты"))
async def chats_tid(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    await db.mk_user(user=message.from_user)
    await db.mk_user(chat=message.chat)

    chat = await db.get_chat(message.chat.id)

    if chat is None:
        return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывод

    web_id = chat['web_id']
    web = await db.get_web(web_id)
    
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    emoji = web['emoji'] or await rndemoji()
    forename = web['forename']

    msg = await message.answer("Подождите, идёт загрузка...")

    # Формируем список чатов
    chats_tid = web['chats_tid']
    chats_tid_str = ""
    if not chats_tid:
        chats_tid_str = "<b>В этой паутине нет чатов.</b>"
    else:
        seq = 1
        for chat_tid in chats_tid:
            chat = await db.get_user_by_tid(chat_tid)
            if chat is None:
                chat_link = chat_tid
            else:
                chat_link = chat['link']
            chats_tid_str += f"{seq}. <b>{chat_link}</b>"
            if web['admin_chat_tid'] == chat_tid:
                chats_tid_str += " <i>(адм)</i>"
            chats_tid_str += "\n"
            seq += 1

    await msg.edit_text(
        text=(
            f"{emoji} Чаты сетки <b>{forename}</b>\n\n"
            f"{chats_tid_str}"
        )
    )

##################################
#   Команды для личных чатов     #
##################################

@rt.message(Command("cancel", ignore_case=True))
async def cancel(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return

    current_state = await state.get_state()

    if current_state is None:
        return await message.answer("У Вас нет активных действий.")

    await state.clear()

    await message.answer("Активное действие отменено.") # Вывод
