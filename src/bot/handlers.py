from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatPermissions
from aiogram.fsm.context import FSMContext
from datetime import datetime
from random import randint

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

# # # # # # # # # # # # # # # # #
#   Управление паутиной чата    #
# # # # # # # # # # # # # # # # #

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
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

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
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

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

# # # # # # # # # # # # # # # # #
#   Управление админами         #
#   через текстовые команды     #
# # # # # # # # # # # # # # # # #

# Повышение админа через текстовую команду
# Если человек не был админом - назначает модератором.

@rt.message(F.text.casefold() == "повысить")
async def up(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.reply_to_message:
        return await message.reply("Повышение нужно писать в ответ на сообщение.") # Вывод

    sender_t = message.from_user
    target_t = message.reply_to_message.from_user

    await db.mk_user(user=sender_t)
    await db.mk_user(user=target_t)
    await db.mk_user(chat=message.chat)

    sender_tid = sender_t.id
    target_tid = target_t.id

    if sender_tid == target_tid:
        return

    # Получаю паутину этого чата
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод
    
    web_id = chat['web_id']

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав
    if not sender_admin or post_strint[sender_admin['post']] < 3:
        # Только хелперы и владелец могут повышать
        post_name = post_str[sender_admin['post']] if sender_admin else "Пользователь"
        return await message.reply(f"Недостаточно прав (<b>{post_name}</b>/<b>{post_str['helper']}</b>)") # Вывод

    sender_post = sender_admin['post']

    # Если target не админ, то делаю его модером
    if not target_admin:
        result = await db.mk_admin(target_tid, web_id, "moder")
        if not result:
            return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        
        target = await db.get_user_by_tid(target_tid)
        return await message.reply(f"🛡 {target['link']} назначен <b>{post_str['moder'].lower()}ом</b> паутины!") # Вывод

    # Повышаю ранг
    target_post = target_admin['post']
    
    if target_post == "owner":
        return await message.reply("Нельзя менять права владельцу паутины.") # Вывод

    elif target_post == "helper":
        if sender_post != "owner":
            return await message.reply("Вы не можете менять права админу, который выше или равен Вам.") # Вывод
        else:
            return await message.reply(
                text=(
                    # Вывод
                    "В одной паутине может быть только один владелец.\n"
                    "Если Вы хотите передать этому человеку права на паутину, то сделайте это через админ-панель."
                )
            )

    elif target_post == "admin":
        if sender_post != "owner":
            return await message.reply("Назначать новых хелперов может только владелец паутины.") # Вывод

    new_post = post_intstr[post_strint[target_post] + 1]
    result = await db.upd_admin_post(target_tid, web_id, new_post)
    if not result:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    target = await db.get_user_by_tid(target_tid)
    return await message.reply(f"⬆️ {target['link']} повышен до <b>{post_str[new_post].lower()}а</b>!") # Вывод

# Понижание админа через текстовую команду
# Если должность модер - полностью снимает.

@rt.message(F.text.casefold() == "понизить")
async def down(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.reply_to_message:
        return await message.reply("Понижение нужно писать в ответ на сообщение.") # Вывод

    sender_t = message.from_user
    target_t = message.reply_to_message.from_user

    await db.mk_user(user=sender_t)
    await db.mk_user(user=target_t)
    await db.mk_user(chat=message.chat)

    sender_tid = sender_t.id
    target_tid = target_t.id

    if sender_tid == target_tid:
        return

    # Получаю паутину этого чата
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод
    
    web_id = chat['web_id']

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав
    if not sender_admin or post_strint[sender_admin['post']] < 3:
        # Только хелперы и владелец могут повышать
        post_name = post_str[sender_admin['post']] if sender_admin else "Пользователь"
        return await message.reply(f"Недостаточно прав (<b>{post_name}</b>/<b>{post_str['helper']}</b>)") # Вывод

    sender_post = sender_admin['post']

    # Если target не админ, то делаю его модером
    if not target_admin:
        return await message.reply(f"Этот пользователь и так не является админом.") # Вывод

    # Повышаю ранг
    target_post = target_admin['post']
    
    if target_post == "owner":
        return await message.reply("Нельзя менять права владельцу паутины.") # Вывод

    elif target_post == "helper":
        if sender_post != "owner":
            return await message.reply("Понижать хелперов может только владелец паутины.") # Вывод
        else:
            return await message.reply(
                text=(
                    # Вывод
                    "В одной паутине может быть только один владелец.\n"
                    "Если Вы хотите передать этому человеку права на паутину, то сделайте это через админ-панель."
                )
            )

    elif target_post == "moder":
        result = await db.rm_admin(target_tid, web_id)
        if not result:
            return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

        # Вывод
        target = await db.get_user_by_tid(target_tid)
        return await message.reply(f"🔥 {target['link']} снят с должности!")

    new_post = post_intstr[post_strint[target_post] - 1]
    result = await db.upd_admin_post(target_tid, web_id, new_post)
    if not result:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    target = await db.get_user_by_tid(target_tid)
    return await message.reply(f"⬇️ {target['link']} понижен до <b>{post_str[new_post].lower()}а</b>!") # Вывод

# Полное снятие админа с должности через текстовую команду
# Прописать может только хелпер или владелец.

@rt.message(F.text.casefold() == "снять")
async def fire(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.reply_to_message:
        return await message.reply("Снятие нужно писать в ответ на сообщение.") # Вывод

    sender_t = message.from_user
    target_t = message.reply_to_message.from_user

    await db.mk_user(user=sender_t)
    await db.mk_user(user=target_t)
    await db.mk_user(chat=message.chat)

    sender_tid = sender_t.id
    target_tid = target_t.id

    if sender_tid == target_tid:
        return

    # Получаю паутину этого чата
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод
    
    web_id = chat['web_id']
    web = await db.get_web(web_id)

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав отправителя
    if not sender_admin or post_strint[sender_admin['post']] < 3:
        # Снимать могут только хелперы и владелец
        post_name = post_str[sender_admin['post']] if sender_admin else "Пользователь"
        return await message.reply(f"Недостаточно прав (<b>{post_name}</b>/<b>{post_str['helper']}</b>)") # Вывод

    sender_post = sender_admin['post']

    # Проверка цели
    if not target_admin:
        return await message.reply(f"Этот пользователь и так не является админом.") # Вывод

    target_post = target_admin['post']
    heir_tid = web['heir_tid']

    # Иерархические проверки
    if target_post == "owner":
        return await message.reply("У паутины обязан быть владелец.") # Вывод

    if target_post == "helper" and sender_post != "owner":
        return await message.reply("Снимать хелперов может только владелец паутины.") # Вывод

    # Логика снятия наследника
    heir_warning = ""
    if heir_tid == target_tid:
        if sender_post != "owner":
            return await message.reply("Снять наследника может только владелец паутины.") # Вывод
        
        # Если снимаем наследника, обнуляем поле в webs
        await db.upd_web_heir(web_id, None)
        heir_warning = "\n⚠️ <i>Этот админ являлся наследником. Не забудьте назначить нового.</i>"

    # Непосредственное удаление из таблицы admins
    result = await db.rm_admin(target_tid, web_id)
    if not result:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    target = await db.get_user_by_tid(target_tid)
    return await message.reply(f"🔥 {target['link']} снят с должности!{heir_warning}")

# # # # # # # # # # # # #
#   Админские команды   #
#   Гмут, гбан, гкик    #
# # # # # # # # # # # # #

# Гмут - Команда для глобального мута человека

@rt.message(F.text.casefold().startswith("гмут"))
@rt.message(F.text.casefold().startswith("гломут")) # Для тех, кто привык к Ирис боту
async def gmute(message: Message):
    # 4/14/26: Я с нуля переписал команду глобального мута.
    # Я пересмотрел свой взгялд на то, как стоит писать код:
    # Раньше я писал код с "поэтапной" логикой. Теперь же я считаю,
    # что лучше пожертвовать "пару байтами", взаимен на структурированность кода.
    # Раньше я писал комментарии только в тех местах, которые как мне казалось, наиболее замудрённые.
    # Теперь же я в целом пишу больше комментариев: даже в простейших местах.
    # Ктобы мог подумать, что так намного легче передвигаться по коду? Глазу есть за что цепляться.
    # TODO Пересмотреть весь код в файлах handers.py и callbacks.py

    if message.chat.type not in ("group", "supergroup"): return

    # Создание/поиск отправителя в БД
    sender_user = await db.mk_user(user=message.from_user)
    if sender_user is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Поиск получателя
    target_user = {}
    if message.reply_to_message is None:
        # Если сообщение - не ответ
        target_username = await grep_username(message.text.split("\n")[0]) # Попытка найти в тексте @юзернейм (grep_username())
        if target_username is None:
            # @юз не найден
            return await message.reply("Нужно либо ответить на сообщение, либо дать @юзернейм.")  # Вывод
        elif target_username.isdigit():
            # Если найденный @юз является TID
            target_user = await db.get_user_by_tid(int(target_username))
        else:
            # @юз найден
            target_tid = await db.get_tid(target_username)
            if target_tid is None:
                return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод
            target_user = await db.get_user_by_tid(target_tid) # Получатель найден
    else:
        # Иначе тупо создаю пользователя в БД
        target_user = await db.mk_user(user=message.reply_to_message.from_user)
    if target_user is None: # LOL      hoiv yv8ty gvgb0ujnu 9hb97yb         --- Серафим даун
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid:
        easteregg_chance = randint(1, 100) # Пасхалка
        if easteregg_chance <= 10:
            return await message.reply("ты мазохист?")
        else:
            return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата из таблиц users & chats
    chat_user = await db.mk_user(chat=message.chat)
    chat_chat = await db.get_chat(message.chat.id)
    if chat_user is None or chat_chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    # Получаю паутину
    web = await db.get_web(chat_chat['web_id'])
    if web is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    chat_tid = message.chat.id # TID чата
    web_id = web['web_id']     # ID паутины

    # Проверка, вдруг у получателя уже есть активное наказание
    target_restr = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    for restr in target_restr:
        if restr['restr'] != "mute":
            continue

        # Если искомое наказание было найдено
        # Вывод
        admin_user = await db.get_user_by_tid(restr['admin_tid'])
        date_reg = await parse_date(restr['date_reg'], "HH:mm d MMMM")
        date_until = await parse_date(restr['date_until'], "HH:mm d MMMM")
        return await message.reply(
            text=(
                 "Этот человек уже замьючен.\n\n"
                f"🔇 {target_user['link']}, глобальный мут в паутине чатов <b>{web['forename']}</b> до <b>{date_until}</b>\n"
                f"🆔 <code>@{target_tid}</code>\n"
                f"⏳ Выдано <b>{date_reg}</b>\n"
                f"🛡️ Выдал {admin_user['link']}\n"
                f"<blockquote>{restr['reason']}</blockquote>"
            )
        )

    # Проверка прав
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Если запись в таблице admin не была найдена, это значит что пользователь не админ (логично)
        return await message.reply(f"Недостаточно прав (<b>{post_str['user']}</b>/<b>{post_str['moder']}</b>)") # Вывод

    # Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Наказать модератора может админ. Наказать админа может хелпер. Хелпер и владелец не могут быть наказаны
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("helper", "owner"):
            return await message.reply(f"Нельзя наказать {post_str['helper']}а или {post_str['owner'][:-2]}ца.")                # Вывод
        if target_admin_post == "admin" and post_strint[sender_admin_post] < 3:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['helper']}</b>)") # Вывод
        if target_admin_post == "moder" and post_strint[sender_admin_post] < 2:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)")  # Вывод

    # Парсинг сообщения: причина и время наказания
    try:
        text = message.text.replace(f"@{target_username}", "").replace("  ", " ").strip() # Перед парсингом убираем из сообщения @юз получателя
    except Exception:
        # Если @юза и так нет
        text = message.text
    date_until = datetime.now().timestamp() + 604_800.0 # Если не указано время - по стандарту одна неделя
    date_until_str = "1 неделю"
    target_quote = f"| \"{message.reply_to_message.text or "[ВЛОЖЕНИЕ]"}\"" if message.reply_to_message else ""
    reason = f"Причина не указана.{target_quote}" # Если не указана причина - так и пишу

    ## Причина
    text_rows = text.split("\n")
    if len(text_rows) == 1:
        # Причина не указана
        pass
    elif len(text_rows) == 2:
        # Причина - весь второй абзац
        reason = f"{text_rows[1]}{target_quote}"
    else:
        # Неккоректное колво абзацей
        return await message.reply("Неккоректный ввод команды.\n<pre>гмут {число} {время}\n{Причина (опционально)}</pre>") # Вывод

    ## Время наказания
    time_str = text_rows[0].split(" ", 1)
    if len(time_str) == 1:
        # "гмут"
        pass
    else:
        date_until_pack = await parse_time(time_str[1])
        if date_until_pack is None:
            return await message.reply("Неккоректный ввод команды.\n<pre>гмут {число} {время}\n{Причина (опционально)}</pre>") # Вывод
        date_until, date_until_str = date_until_pack

    # Непосредственное назначение наказания
    ## Запись в БД
    restr = await db.mk_restr(web_id, target_tid, "mute", sender_tid, reason, date_until)
    if restr is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.restrict_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                permissions=ChatPermissions(
                    can_send_message=False,
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
                use_independent_chat_permissions=True,
                until_date=datetime.fromtimestamp(date_until)
            )
        except Exception: # Если бота нет в чате или нет прав
            continue

    # Вывод
    await message.reply(
        f"🔇 {target_user['link']}, глобальный мут в паутине чатов <b>{web['forename']}</b> на <b>{date_until_str}</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Выдал {sender_user['link']}\n"
        f"<blockquote>{reason}</blockquote>"
    )

# Гразмут - Команда для снятия глобального мута

@rt.message(F.text.casefold().startswith("гразмут"))
@rt.message(F.text.casefold().startswith("глоразмут")) # Для тех, кто привык к Ирис боту
async def gunmute(message: Message):
    if message.chat.type not in ("group", "supergroup"): return

    # Создание/поиск отправителя в БД
    sender_user = await db.mk_user(user=message.from_user)
    if sender_user is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Поиск получателя
    target_user = {}
    if message.reply_to_message is None:
        # Если сообщение - не ответ
        target_username = await grep_username(message.text.split("\n")[0]) # Попытка найти в тексте @юзернейм (grep_username())
        if target_username is None:
            # @юз не найден
            return await message.reply("Нужно либо ответить на сообщение, либо дать @юзернейм.")  # Вывод
        elif target_username.isdigit():
            # Если найденный @юз является TID
            target_user = await db.get_user_by_tid(int(target_username))
        else:
            # @юз найден
            target_tid = await db.get_tid(target_username)
            if target_tid is None:
                return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>пользователь не найден</b>.") # Вывод
            target_user = await db.get_user_by_tid(target_tid) # Получатель найден
    else:
        # Иначе тупо создаю пользователя в БД
        target_user = await db.mk_user(user=message.reply_to_message.from_user)
    if target_user is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if sender_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")
    
    # Получение чата из таблиц users & chats
    chat_user = await db.mk_user(chat=message.chat)
    chat_chat = await db.get_chat(message.chat.id)
    if chat_user is None or chat_chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    # Получаю паутину
    web = await db.get_web(chat_chat['web_id'])
    if web is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    chat_tid = message.chat.id # TID чата
    web_id = web['web_id']     # ID паутины

    # Проверка, есть ли вообще у получателя активное наказание
    target_restrs = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    target_restr = {}
    for tr in target_restrs:
        if tr['restr'] == "mute":
            target_restr = tr
            break

    if not target_restr:
        # Если искомое наказание не было найдено
        return await message.reply("У этого пользователя нет активного глобального мута в этой паутине.")

    # Проверка прав
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        return await message.reply(f"Недостаточно прав (<b>{post_str['user']}</b>/<b>{post_str['moder']}</b>)") # Вывод

    # Проверка прав
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Если запись в таблице admin не была найдена, это значит что пользователь не админ (логично)
        return await message.reply(f"Недостаточно прав (<b>{post_str['user']}</b>/<b>{post_str['moder']}</b>)") # Вывод

    # Проверка, если получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Убрать наказание модератору может админ. Убрать наказание админу может хелпер. Хелпер и владелец не могут быть наказаны
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("helper", "owner"):
            return await message.reply(f"{post_str['helper']} или {post_str['owner']} и так чисто технически не могут быть наказаны.")                # Вывод
        if target_admin_post == "admin" and post_strint[sender_admin_post] < 3:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['helper']}</b>)") # Вывод
        if target_admin_post == "moder" and post_strint[sender_admin_post] < 2:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)")  # Вывод

    # Непосредственное удаление наказания
    ## Удаление записи из БД
    result = await db.rm_restr(target_restr['restr_id'])
    if result is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.restrict_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                permissions=ChatPermissions(
                    can_send_message=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_edit_tag=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True
                ),
                use_independent_chat_permissions=True
            )
        except Exception: # Если бота нет в чате или нет прав
            continue

    # Вывод
    await message.reply(
        f"🔊 {target_user['link']}, глобальный мут в паутине <b>{web['forename']}</b> снят\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Снял {sender_user['link']}"
    )

# # # # # # # # #
#   Остальное   #
# # # # # # # # #

#

@rt.message(F.text.casefold().startswith("жалоба"))
@rt.message(F.text.casefold().startswith(".жалоба")) # Для тех, кто привык к Ирис боту
@rt.message(F.text.casefold().startswith("репорт"))  # Для тех, кто привык к Ирис боту
@rt.message(F.text.casefold().startswith(".репорт")) # Для тех, кто привык к Ирис боту
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
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

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

@rt.message(F.text.casefold().startswith("чаты"))
async def chats_tid(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    await db.mk_user(user=message.from_user)
    await db.mk_user(chat=message.chat)

    chat = await db.get_chat(message.chat.id)

    if chat is None:
        return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

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
