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

# Команды, для проверки скорости ответа бота

async def ping(message: Message):
    reply = ""
    match message.text.casefold():
        case "бот":
            reply = "✅" # 4/19/26 - Yqw O предложил заменить "✅ На месте" на просто "✅". Принято
        case "кинг":
            reply = "КОНГ"
        case "пинг":
            reply = "ПОНГ"
        case "пиу":
            reply = "ПАУ"
        case "пиф":
            reply = "ПАФ"
        case "пук":
            reply = "Срёньк"

    await message.reply(reply) # Вывод

###############################################
#   Главное reply-меню                        #
#   keyboards.py: main_menu()                 #
#   Все эти команды вызываются только в ЛС    #
###############################################

# Настройка паутины
# Выводит список чатов, который входят в паутину, 
# и inline-клавиатуру, с кнопками для настройки своей паутины

async def get_web(message: Message):
    # Получение данных из БД
    user = await db.mk_user(user=message.from_user)
    if user is None: return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    if message.chat.type in ("group", "supergroup"):
        # Получение чата и паутины
        chat_and_web = await get_chat_and_web(message)
        if chat_and_web is None:
            return
        chat, web = chat_and_web
        if message.chat.id != web['admin_chat_tid']:
            return
    elif message.chat.type == "private":
        web = await db.get_web_by_owner_tid(message.from_user.id)
        if web is None: return await message.answer("Произошла либо <b>непредвиденная ошибка</b>, либо <b>у Вас нет паутины</b>.") # Вывод

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

    await message.answer(
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

# Создание паутины
# В качестве первончального названия паутины
# выступает full_name создателя

async def mk_web(message: Message):
    # Получение данных из БД
    user = await db.mk_user(user=message.from_user)
    if user is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    web = await db.get_web_by_owner_tid(message.from_user.id)

    ## Проверка на наличие всех нужных записей в БД
    if web is not None:
        return await message.answer("У Вас уже есть паутина.") # Вывод

    # Непосредственно создание паутины в БД
    web = await db.mk_web(user['full_name'], user['tid'])
    if web is None:
        return await message.answer("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    await message.reply(
        text=(
            f"✅ Паутина <b>{web['forename']} (#{web['web_id']})</b> успешно создана!\n\n"
             "Можете заняться её первоначальной настройкой, нажав на кнопку <code>🗂️ Мои паутины</code> "
             "или сразу добавить в неё первые чаты 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

# Кнока добавления бота в чат
# По сути, главная функция этой кнопки - быть наполнением,
# просто чтобы меню красиво смотрелось

async def add_to_chat(message: Message):
    # Вывод
    await message.answer(
        text="➕ Добавляй бота в нужные чаты и пиши там команду <code>+паутина</code>",
        reply_markup=await kb.add_to_chat()
    )

@rt.message(F.text == "📚 Команды")
async def commands_list(message: Message):
    # 4/19/26 - Возможно стоит сделать страницу в teletype.in?
    await message.answer(
        "Визуальная панель управления паутиной <b>пока-что</b> доступна " #
        "только в ЛС с ботом и только для владельца.\n\n" #

        "<code>+паутина</code>, <code>-паутина</code> — Добавляет, удаляет чат из паутины. Прописать можешь только владелец чата или паутины.\n"
        "<code>паутина</code> — Просмотр информации о паутине, в которой состоит этот чат.\n"
        "<code>сделать админским</code> — Делает чат, в котором была прописана команда, админским в этой паутине. " #
        "Наличие админского чата активирует возможно подавать жалобы. Жалобы со всех чатов паутины будут приходить в админский чат.\n\n" #

        "<b>*</b> <code>повысить</code>, <code>понизить</code>, <code>снять</code> — Повышает или создаёт, понижает, сразу снимает админа в паутине.\n\n"

        "<b>***</b> <code>[г/гл/гло][бан/мут/кик]</code> — Банить/мутит/кикает человека во всех чатах паутины.\n"
        "<b>***</b> <code>[г/гл/гло]раз[бан/мут]</code> — Разбанивает/размьючивает человека во всех чатах паутины.\n\n"

        "<b>**</b> <code>жалоба</code>/<code>.жалоба</code>/<code>репорт</code>/<code>.репорт</code> — Подаёт жалобу на человека.\n"
        "<code>чаты</code> — Выводит список чатов, состоящих в паутине.\n"
        "<code>админы</code>/<code>гладмины</code>/<code>глоадмины</code>/" #
        "<code>кто админ</code>/<code>кто гладмин</code>/<code>кто глоадмин</code> — Выводит список глобальной администрации.\n" #
        "<code>жалобы</code> — Выводит список нерешённых жалоб. Можно вводить только в админском чате.\n"
        "<b>*</b> <code>причина</code>/<code>наказания</code> — Выводит список всех наказаний пользователя.\n\n"

        "<b>*</b> — Можно передать @юзернейм или @телеграмайди человека, или ответить на его сообщение.\n"
        "<b>**</b> — Можно дать причину (вводить нужно с новой строки).\n"
        "<b>***</b> — Плюсом к одинарной звездочке прибавляется возможность ввести причину (вводить нужно с новой строки)."
    )

#####################################
#   Команды для групповых чатов     #
#                                   #
#   паутина  +паутина  -паутина     #
#   сделать админским               #
#####################################

# # # # # # # # # # # # # # # # #
#   Управление паутиной чата    #
# # # # # # # # # # # # # # # # #

# Информация о паутине чата (паутина)
# Выводит карточку с данными паутины, к которой привязан текущий чат:
# эмодзи, название, юзернейм владельца и наследника.

async def get_chat(message: Message):
    # Получение данных из БД
    ## Получение инфы о чате, где была введена команда, чтобы получить web_id
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        return await message.reply("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    ## Непосредственное получение инфы о паутине
    web = await db.get_web(chat['web_id'])
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    emoji = web['emoji'] or await rndemoji()
    owner = await db.get_user_by_tid(web['owner_tid'])
    if web['heir_tid']:
        heir = await db.get_user_by_tid(web['heir_tid'])
        heir_link = heir['link']
    else:
        heir_link = "Отсутствует"
    
    return await message.reply(
        text=(
            f"{emoji} Этот чат состоит в паутине <b>{web['forename']}</b>\n"
            f"Владелец: <b>{owner['link']}</b> | Наследник: <b>{heir_link}</b>"
        ),
        reply_markup=await kb.about(web['web_id'])
    )

# Добавление чата в паутину (+паутина)
# Записывает чат в БД и привязывает к паутине пользователя.
# Если команду вводит не владелец чата — отправляет предложение владельцу.

async def mk_chat(message: Message):
    # Получение данных из БД
    user = await db.mk_user(user=message.from_user)
    chat_owner = await db.mk_user(user=await get_chat_owner(message.chat.id))
    ## Проверка на наличие запрошенных данных в БД
    if None in (user, chat_owner):
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    await db.upd_chat_owner(message.chat.id, chat_owner['tid'])
    chat_chat = await db.get_chat(message.chat.id)
    web_chat_owner = await db.get_web_by_owner_tid(chat_owner['tid'])

    user_tid = user['tid']             # TID прописавшего команду
    chat_owner_tid = chat_owner['tid'] # TID владельца чата

    # Непосредственная логика всей команды
    if chat_chat:
        # Если чат уже состоит в паутине
        return await get_chat(message) # Вывод

    else:
        if user_tid != chat_owner_tid:
            # Если команду прописал не владелец чата
            if await db.get_web_by_owner_tid(user_tid) is None:
                # Если у невладельцачата нет своей паутины, то просто вывод
                return await message.reply("Этот чат не состоит ни в какой паутине.") # Вывод

            else:
                # Иначе - предложение вступить в его паутину
                return await message.reply(
                    # Вывод
                    text=f"{chat_owner['link']}, этот пользователь предлагает включить Ваш чат в его паутину чатов.",
                    reply_markup=await kb.accept_invite_web(user_tid)
                )

        else:
            if web_chat_owner is None:
                # Если у владельца чата нет паутины
                return await message.reply("У Вас нет паутины. Сначала создайте её в ЛС с ботом.") # Вывод

            else:
                chat_chat = await db.mk_chat(message.chat.id, web_chat_owner['web_id'], chat_owner['tid'])
                if chat_chat is None:
                    return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
                return await message.reply(f"✅ Чат <b>{message.chat.title}</b> успешно добавлен в паутину <b>{web_chat_owner['forename']}</b>!") # Вывод

# Удаление чата из паутины (-паутина)
# Убирает привязку чата к текущей паутине в БД.
# Совершить действие может либо владелец самого чата, либо владелец паутины.

async def rm_chat(message: Message):
    # Получение данных из БД
    user = await db.mk_user(user=message.from_user)
    chat_owner = await db.mk_user(user=await get_chat_owner(message.chat.id))
    ## Проверка на наличие запрошенных данных в БД
    if None in (user, chat_owner):
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    await db.upd_chat_owner(message.chat.id, chat_owner['tid'])
    chat_chat = await db.get_chat(message.chat.id)
    
    # Непосредственная логика всей команды
    if chat_chat is None:
        # Если чат и так не в паутине
        return await message.reply("Этот чат и так не состоит ни в какой паутине.") # Вывод

    ## Если чат в паутине, получаем данные о ней
    web_id = chat_chat['web_id']
    web = await db.get_web(web_id)
    
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    user_tid = user['tid'] # TID прописавшего команду

    # Проверка прав доступа
    # Удалить чат может либо хозяин чата, либо хозяин всей паутины
    if user_tid == chat_owner['tid'] or user_tid == web['owner_tid']:
        ## Непосредственное удаление из БД
        result = await db.rm_chat(message.chat.id, web_id)
        if not result: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        return await message.reply(f"🗑 Чат <b>{message.chat.title}</b> успешно удалён из паутины <b>{web['forename']}</b>!") # Вывод (успех)

    else:
        return await message.reply("Исключить чат из паутины может только владелец этого чата, либо владелец самой паутины.") # Вывод (неуспех: недостаточно прав)

# Назначение админского чата в паутине (сделать админским)
# В этот чат будут приходить уведомления о жалобах (репортах) из всех чатов паутины.
# Назначить админский чат может только владелец паутины.

async def mk_admin_chat(message: Message):
    # Получение данных из БД
    chat = await db.get_chat(message.chat.id)
    if chat is None:
        return await message.reply("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    ## Получаю паутину
    web = await db.get_web(chat['web_id'])
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    chat_tid      = message.chat.id  # TID чата, где была введена команда
    web_owner_tid = web['owner_tid'] # TID владельца паутины

    # Непосредственная логика всей команды
    if chat_tid == web['admin_chat_tid']:
        # Если чат уже и так админский
        return await message.reply("Этот чат уже и так является админским.") # Вывод

    if message.from_user.id != web_owner_tid:
        # Если команду прописал не владелец паутины
        web_owner = await db.get_user_by_tid(web_owner_tid)
        return await message.reply(f"Только владелец паутины ({web_owner['link']}) может назначать админский чат.") # Вывод

    result = await db.upd_web_admin_chat_tid(web['web_id'], chat_tid)
    if not result: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    await message.reply("🛡️ Теперь в этот чат будут приходить глобальные репорты.") # Вывод

# # # # # # # # # # # # # # # # #
#   Управление админами         #
#   через текстовые команды     #
# # # # # # # # # # # # # # # # #

# Повышение админа через текстовую команду (повысить)
# Если человек не был админом - назначает модератором.

async def admin_up(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав
    ## Проверка на то, что отправитель является админом
    if sender_admin is None or post_strint[sender_admin['post']] < 4:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['admin']}</b>).") # Вывод

    target_restrs = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    if target_restrs:
        for restr in target_restrs:
            if restr['restr'] == "ban": return await message.reply("Этот пользователь забанен.") # Вывод

    # Если target не админ, то выдача минимального ранга
    if target_admin is None:
        result = await db.mk_admin(target_tid, web_id, post_intstr[1])
        if result is None: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
        return await message.reply(f"🛡 {target_user['link']} назначен <b>{post_str[post_intstr[1]]}ом</b> паутины!") # Вывод

    ## Получатель является админом
    sender_post = sender_admin['post'] # Должность отправителя
    target_post = target_admin['post'] # Должность получателя

    if target_post == "owner":
        return await message.reply("Нельзя менять права владельцу паутины.") # Вывод

    elif target_post == "admin":
        if sender_post != "owner":
            return await message.reply("Вы не можете менять права админу, который выше или равен Вам по должности.") # Вывод
        else:
            return await message.reply(
                text=(
                    # Вывод
                    "В одной паутине может быть только один владелец.\n"
                    "Если Вы хотите передать этому человеку права на паутину, то сделайте это через админ-панель."
                )
            )

    elif target_post == "adminjr" and sender_post != "owner":
        return await message.reply(f"Назначить нового <b>{post_str['admin']}а</b> может только <b>{post_str['owner']}</b>.") # Вывод

    ## Повышаем ранг, уже непосредственно в БД
    new_post = post_intstr[post_strint[target_post] + 1]
    result = await db.upd_admin_post(target_tid, web_id, new_post)
    if not result: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    return await message.reply(f"⬆️ {target_user['link']} повышен до <b>{post_str[new_post]}а</b>!") # Вывод

# Понижание админа через текстовую команду (понизить)
# Если должность модер - полностью снимает.

async def admin_down(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав
    ## Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 4:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['admin']}</b>).") # Вывод

    # Если target не админ, то с него "нечего брать"
    if target_admin is None:
        return await message.reply(f"Этот {post_str['user'].lower()} и так не админ.") # Вывод

    # Нужно проверить, вдруг у цели есть чаты в этой паутине.
    # Делаю прямой запрос в БД (без отдельной функции, т. к. это излишне)
    # 4/19/26 - В целом планирую сократить кол-во функций в db_query.py, если это возможно.
    # Проведу там код ревью (потом) TODO
    await db.cur.execute(
        "SELECT * FROM chats WHERE owner_tid = %s AND web_id = %s",
        (target_tid, web_id)
    )
    is_target_have_chats = await db.cur.fetchall()
    if is_target_have_chats:
        return await message.reply("У этого пользователя есть чаты в паутине, его нельзя снять или понизить.") # Вывод

    # Непосредственно логика повышения ранга
    sender_post = sender_admin['post'] # Должность отправителя
    target_post = target_admin['post'] # Должность получателя
    
    if target_post == "owner":
        return await message.reply("Нельзя менять права владельцу паутины.") # Вывод

    elif target_post == "admin" and sender_post != "owner":
        return await message.reply(f"Понизить <b>{post_str['admin']}а</b> может только <b>{post_str['owner']}</b>.") # Вывод

    elif target_post == "helper":
        return await admin_fire(message)

    ## Понижаем ранг, уже непосредственно в БД
    new_post = post_intstr[post_strint[target_post] - 1]
    result = await db.upd_admin_post(target_tid, web_id, new_post)
    if not result: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    return await message.reply(f"⬇️ {target_user['link']} понижен до <b>{post_str[new_post]}а</b>!") # Вывод

# Полное снятие админа с должности через текстовую команду (снять)
# Прописать может только хелпер или владелец.

async def admin_fire(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Получаю данные админов (отправителя и цели)
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    target_admin = await db.get_admin_by_tid(target_tid, web_id)

    # Проверка прав
    ## Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 4:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['admin']}</b>).") # Вывод

    # Если target не админ, то с него "нечего брать"
    if target_admin is None:
        return await message.reply(f"Этот {post_str['user'].lower()} и так не админ.") # Вывод

    # Нужно проверить, вдруг у цели есть чаты в этой паутине.
    await db.cur.execute(
        "SELECT * FROM chats WHERE owner_tid = %s AND web_id = %s",
        (target_tid, web_id)
    )
    is_target_have_chats = await db.cur.fetchall()
    if is_target_have_chats:
        return await message.reply("У этого пользователя есть чаты в паутине, его нельзя снять или понизить.") # Вывод

    # Непосредственно логика повышения ранга
    sender_post = sender_admin['post'] # Должность отправителя
    target_post = target_admin['post'] # Должность получателя
    heir_tid = web['heir_tid']         # TID наследника паутины

    # Иерархические проверки
    if target_post == "owner":
        return await message.reply("У паутины обязан быть владелец.") # Вывод

    if target_post == "admin" and sender_post != "owner":
        return await message.reply( ) # Вывод

    # Непосредственно логика снятие админа
    ## Логика снятия наследника
    heir_warning_text = ""
    if heir_tid == target_tid:
        if sender_post != "owner":
            return await message.reply(f"Снять <b>{post_str['heir']}а</b> может только <b>{post_str['owner']}</b>.") # Вывод

        # Если снимаем наследника, обнуляем поле в webs
        await db.upd_web_heir(web_id, None)
        heir_warning_text = f"\nЭтот админ являлся <b>{post_str['heir']}ом</b>. Не забудьте назначить нового."

    ## Непосредственно удаление из таблицы admins
    result = await db.rm_admin(target_tid, web_id)
    if not result: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    return await message.reply(f"🔥 {target_user['link']} снят с должности!{heir_warning_text}")

# # # # # # # # # # # # #
#   Админские команды   #
#   Гмут, гбан, гкик    #
# # # # # # # # # # # # #

# Глобальный бан ("гбан", "глбан", "глобан")
# Админ может загбанить модера, хелпер админа.

async def gban(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Проверка, вдруг у получателя уже есть активное наказание
    target_restr = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    for restr in target_restr:
        if restr['restr'] != "ban":
            continue

        # Если искомое наказание было найдено
        # Вывод
        admin_user = await db.get_user_by_tid(restr['admin_tid'])
        date_reg = await parse_date(restr['date_reg'], "HH:mm d MMMM")
        date_until = await parse_date(restr['date_until'], "HH:mm d MMMM")

        return await message.reply(
            text=(
                 "Этот пользователь уже забанен.\n\n"
                f"⛔ {target_user['link']}, глобальный бан в паутине чатов <b>{web['forename']}</b> до <b>{date_until}</b>\n"
                f"🆔 <code>@{target_tid}</code>\n"
                f"⏳ Выдано <b>{date_reg}</b>\n"
                f"🛡️ Выдал {admin_user['link']}\n"
                f"<blockquote>{restr['reason']}</blockquote>"
            )
        )

    # Проверка прав
    ## Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 2:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['moder']}</b>).") # Вывод

    ## Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("owner", "admin"):
            return await message.reply(f"Нельзя наказать {post_str['admin']}а или {post_str['owner'][:-2]}ца.") # Вывод
        elif target_admin_post == "adminjr" and post_strint[sender_admin_post] < 4:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)") # Вывод
        elif target_admin_post in ("moder", "helper") and post_strint[sender_admin_post] < 3:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['adminjr']}</b>)") # Вывод

    # Парсинг сообщения: причина и время наказания
    text_rows = message.text.split("\n", 1)
    date_until = datetime.now().timestamp() + (31_536_000.0 + 86_401.0) # Если не указано время, то бессрочно
    date_until_str = "бессрочно"
    target_quote = f" | \"{message.reply_to_message.text or "[ВЛОЖЕНИЕ]"}\"" if message.reply_to_message else ""
    reason = f"Причина не указана.{target_quote}" # Если не указана причина - так и пишу

    ## Причина
    if len(text_rows) == 1:
        # Причина не указана
        pass
    elif len(text_rows) == 2:
        reason = f"{text_rows[1].strip()}{target_quote}"

    ## Время наказания
    text_row_0 = text_rows[0].replace(await grep_username(text_rows[0], True), "").replace("  ", " ").strip()
    time_str = text_row_0.split(" ", 1)
    
    if len(time_str) == 1:
        pass
    elif len(time_str) == 2:
        if time_str[1] in ("навсегда", "бессрочно"):
            pass
        else:
            time_str = time_str[1].split(" ")
            if len(time_str) > 1:
                return await message.reply("Время наказания введено неккоректно.")
            date_until_pack = await parse_time(time_str[1])
            if date_until_pack is None:
                return await message.reply("Время наказания введено неккоректно.")
            date_until, date_until_str = date_until_pack

    # Непосредственное назначение наказания
    ## Запись в БД
    restr = await db.mk_restr(web_id, target_tid, "ban", sender_tid, reason, date_until)
    if restr is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
    if target_admin:
        result = await db.rm_admin(target_tid, web_id) # Если целевой пользователь являлся админом, то снимаем его
        if result is None: await message.reply("Человек успешно забанен, но по неизвестной причине с него не удалось снять админские права. Сделайте это вручную.") # Вывод
    await db.upd_plus_restrs_count(sender_tid, web_id, sender_admin['restrs_count'])

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.ban_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                until_date=date_until
            )
        except Exception: # Если бота нет в чате или нет прав
            continue

    # Вывод
    await message.reply(
        f"⛔ {target_user['link']}, глобальный бан в паутине чатов <b>{web['forename']}</b> на <b>{date_until_str}</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Выдал {sender_user['link']}\n"
        f"<blockquote>{reason}</blockquote>"
    )

# Глобальный разбан ("гразбан", "глразмут", "глоразбан")

async def gunban(message: Message):
    # Получение отправителя и получателя
    sender_user, target_user = await get_sender_and_target(message)
    if not target_user or not sender_user:
        return

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение сектки
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Проверка, есть ли вообще у получателя активное наказание
    target_restrs = await db.get_restrs_by_user_tid_in_web(target_tid, web_id)
    target_restr = {}
    for tr in target_restrs:
        if tr['restr'] == "ban":
            target_restr = tr
            break
    if not target_restr:
        # Если искомое наказание не было найдено
        return await message.reply("У этого пользователя нет активного глобального бана в этой паутине.")

    # Проверка прав
    ## Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 2:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['moder']}</b>).") # Вывод

    ## Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("owner", "admin"):
            return await message.reply(f"Нельзя наказать {post_str['admin']}а или {post_str['owner'][:-2]}ца.") # Вывод
        elif target_admin_post == "adminjr" and post_strint[sender_admin_post] < 4:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)") # Вывод
        elif target_admin_post in ("moder", "helper") and post_strint[sender_admin_post] < 3:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['adminjr']}</b>)") # Вывод

    # Непосредственное удаление наказания
    ## Удаление записи из БД
    result = await db.rm_restr(target_restr['restr_id'])
    if result is None: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.unban_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                only_if_banned=True
            )
        except Exception: # Если бота нет в чате или нет прав
            continue

    # Вывод
    await message.reply(
        f"✅ {target_user['link']}, глобальный разбан в паутине <b>{web['forename']}</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Снял {sender_user['link']}"
    )

# Глобальный мут ("гмут", "глмут", "гломут")
# Запрещает все права пользователю во всех чатах паутины, ВКЛЮЧАЯ СОЗДАНИЕ ОПРОСОВ.
# Админ может загмутить модера, хелпер админа.

async def gmute(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

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
        return await message.reply(f"Недостаточно прав (<b>{post_str['user']}</b>/<b>{post_str['helper']}</b>)") # Вывод

    # Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Наказать модератора может админ. Наказать админа может хелпер. Хелпер и владелец не могут быть наказаны
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("helper", "owner"):
            return await message.reply(f"Нельзя наказать {post_str['helper']}а или {post_str['owner'][:-2]}ца.")                # Вывод
        elif target_admin_post == "admin" and post_strint[sender_admin_post] < 3:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['helper']}</b>)") # Вывод
        elif target_admin_post == "moder" and post_strint[sender_admin_post] < 2:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)")  # Вывод

    # Парсинг сообщения: причина и время наказания
    text_rows = message.text.split("\n", 1)
    date_until = datetime.now().timestamp() + (31_536_000.0 + 86_401.0) # Если не указано время, то бессрочно
    date_until_str = "бессрочно"
    target_quote = f" | \"{message.reply_to_message.text or "[ВЛОЖЕНИЕ]"}\"" if message.reply_to_message else ""
    reason = f"Причина не указана.{target_quote}" # Если не указана причина - так и пишу

    ## Причина
    if len(text_rows) == 1:
        # Причина не указана
        pass
    elif len(text_rows) == 2:
        reason = f"{text_rows[1].strip()}{target_quote}"

    ## Время наказания
    text_row_0 = text_rows[0].strip().replace(await grep_username(text_rows[0], True), "").replace("  ", " ").strip()
    time_str = text_row_0.split(" ", 1)
    
    if len(time_str) == 1:
        pass
    elif len(time_str) == 2:
        if time_str[1] in ("навсегда", "бессрочно"):
            pass
        else:
            time_str = time_str[1].split(" ")
            if len(time_str) > 1:
                return await message.reply("Время наказания введено неккоректно.")
            date_until_pack = await parse_time(time_str[1])
            if date_until_pack is None:
                return await message.reply("Время наказания введено неккоректно.")
            date_until, date_until_str = date_until_pack

    # Непосредственное назначение наказания
    ## Запись в БД
    restr = await db.mk_restr(web_id, target_tid, "mute", sender_tid, reason, date_until)
    if restr is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод
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

# Глобальный размут ("гразмут", "глразмут", "глоразмут")

async def gunmute(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

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
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None:
        # Если запись в таблице admin не была найдена, это значит что пользователь не админ (логично)
        return await message.reply(f"Недостаточно прав (<b>{post_str['user']}</b>/<b>{post_str['helper']}</b>)") # Вывод

    ## Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        sender_admin_post = sender_admin['post']
        target_admin_post = target_admin['post']

        if target_admin_post in ("owner", "admin"):
            return await message.reply(f"Нельзя наказать {post_str['admin']}а или {post_str['owner'][:-2]}ца.") # Вывод
        elif target_admin_post == "adminjr" and post_strint[sender_admin_post] < 4:
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['admin']}</b>)") # Вывод
        elif target_admin_post in ("moder", "helper") and post_strint[sender_admin_post] < 3:   
            return await message.reply(f"Недостаточно прав (<b>{post_str[sender_admin_post]}</b>/<b>{post_str['adminjr']}</b>)") # Вывод

    # Непосредственное удаление наказания
    ## Удаление записи из БД
    result = await db.rm_restr(target_restr['restr_id'])
    if result is None: return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    ## Назначение в Телеграме
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.restrict_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                permissions=ChatPermissions(
                    can_send_messages=True,
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
        f"🔊 {target_user['link']}, глобальный размут в паутине <b>{web['forename']}</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Снял {sender_user['link']}"
    )

# Глобальный кик ("гкик", "глкик", "глокик")
# Логика проста - глобанит и мгновенное глоразбанивает пользователя,
# что создаёт иллюзию кика. В Telegram Bot API нет встроенной функции кика.
# Администрацию кикать нельзя.

async def gkick(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    web_id = web['web_id'] # ID паутины

    # Проверка прав
    # Проверка на то, что отправитель является админом
    sender_admin = await db.get_admin_by_tid(sender_tid, web_id)
    if sender_admin is None or post_strint[sender_admin['post']] < 2:
        sender_admin_poststr = post_str[sender_admin['post']] if sender_admin else post_str["user"]
        return await message.reply(f"Недостаточно прав (<b>{sender_admin_poststr}</b>/<b>{post_str['moder']}</b>).") # Вывод

    # Проверка на то, что получатель является админом
    target_admin = await db.get_admin_by_tid(target_tid, web_id)
    if target_admin:
        # Если да - нельзя наказать
        return await message.reply("Нельзя глобально кикнуть админа.")

    # Парсинг сообщения: причина и время наказания
    text_rows = message.text.split("\n", 1)
    target_quote = f" | \"{message.reply_to_message.text or "[ВЛОЖЕНИЕ]"}\"" if message.reply_to_message else ""
    reason = f"Причина не указана.{target_quote}" # Если не указана причина - так и пишу

    ## Причина
    if len(text_rows) == 1:
        # Причина не указана
        pass
    elif len(text_rows) == 2:
        reason = f"{text_rows[1].strip()}{target_quote}"

    # Непосредственное назначение наказания
    ## Запись в БД
    await db.upd_plus_restrs_count(sender_tid, web_id, sender_admin['restrs_count'])

    ## Бан и мгновенный разбан во всех чатах паутины
    chats_tid = web['chats_tid']
    for chat_tid in chats_tid:
        try:
            await bot.ban_chat_member(
                chat_id=chat_tid,
                user_id=target_tid
            )
            await bot.unban_chat_member(
                chat_id=chat_tid,
                user_id=target_tid,
                only_if_banned=True
            )
        except Exception: # Если бота нет в чате или нет прав
            continue

    # Вывод
    await message.reply(
        f"👟 {target_user['link']}, глобальный кик в паутине чатов <b>{web['forename']}</b>\n"
        f"🆔 <code>@{target_tid}</code>\n"
        f"🛡️ Выдал {sender_user['link']}\n"
        f"<blockquote>{reason}</blockquote>"
    )

# # # # # # # # #
#   Остальное   #
# # # # # # # # #

# Отправляет жалобу на пользователя ("жалоба", ".жалоба", "репорт", ".репорт")
# Если чат состоит в паутине, и у этой паутины 
# назначен админский чат, то жалоба отправится в адм. чат.
# Работает только в ответ на сообщение, не принимая @юзернейм.

async def report(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender, target = sender_and_target

    sender_tid = sender['tid'] # TID отправителя
    target_tid = target['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web
    if not web['admin_chat_tid']:
        return await message.reply("У паутины, в которой состоит этот чат, нет админского чата.") # Вывод

    web_id = web['web_id'] # ID паутины
    chat_user = await db.get_user_by_tid(message.chat.id)

    # Непосредственно логика команды
    message_user = await message.reply("Подождите, идёт загрузка...") # Вывод (загрузка)
    message_admin = await bot.send_message(
         # Вывод (загрузка)
        chat_id=web['admin_chat_tid'],
        text=(
            f"Идёт загрузка жалобы из чата {chat_user['link']}..."
        )
    )

    # Непосредственно создание жалобы в БД
    report = await db.mk_report(web_id, message, message_admin.message_id, message_user.message_id)
    if not report:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    report_id = report['report_id']

    await message_user.edit_text(
        text=(
            f"❗️ Жалоба на {target['link']} отправлена (#{report['report_id']})\n"
            f"🆔 <code>@{target_tid}</code>\n"
            f"🗣 Отправил {sender['link']}\n"
            f"<blockquote>{report['reason']}</blockquote>"
        ),
        reply_markup=await kb.report_user(report_id)
    )
    await message_admin.edit_text(
        text=(
            f"❗️ Жалоба на {target['link']} (#{report['report_id']})\n"
            f"🆔 <code>@{target_tid}</code>\n"
            f"🗣 Отправил {sender['link']} из чата {chat_user['link']}\n"
            f"<blockquote>{report['reason']}</blockquote>"
        ),
        reply_markup=await kb.report_admin(report_id)
    )

# Список чатов паутины (чаты)
# Выводит список чатов, состоящих в паутине,
# в порядке времени добавления.

async def chats_tid(message: Message):
    # Получение данных из БД
    ## Получение инфы о чате, где была введена команда, чтобы получить web_id, а после саму паутину
    
    chat_chat = await db.get_chat(message.chat.id)
    if chat_chat is None:
        return await message.reply("Произошла либо <b>непредвиденная ошибка</b>, либо <b>этот чат не состоит ни в какой паутине</b>.") # Вывод

    web_id = chat_chat['web_id'] # ID паутины, где производится действие

    ## Получаю паутину
    web = await db.get_web(web_id)
    if web is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    msg = await message.reply("Подождите, идёт загрузка...") # Пока формируется список чатов паутины
    emoji = web['emoji'] or await rndemoji()
    chats_tid_str = await mk_chats_tid_str(web['chats_tid'], web['admin_chat_tid'])

    await msg.edit_text(
        text=(
            f"{emoji} Чаты паутины <b>{web['forename']}</b>\n\n"
            f"{chats_tid_str}"
        )
    )

# Список админов паутины ("админы", "гладмины", "глоадмины", "кто админ", "кто гладмин", "кто глоадмин")
# Выводит список админов в порядке иерархии:
# Владелец и наследник, хелперы, админы и в конце модеры.

async def admins(message: Message):
    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    ## Получаю админов паутину
    admins = await db.get_web_admins(web['web_id'])
    if admins is None:
        return await message.reply("Непредвиденная ошибка. Попробуйте позже.") # Вывод

    # Вывод
    msg = await message.reply("Подождите, идёт загрузка...") # Пока формируется список админов паутины

    ## Формирование списка админов
    owner_and_heir_str = f"🤴 <b>{post_str['owner']} и {post_str['heir']}</b>"
    admins_str = f"4️⃣ <b>{post_str['admin']}ы</b>"
    adminsjr_str = f"3️⃣ <b>{post_str['adminjr']}ы</b>"
    moders_str = f"2️⃣ <b>{post_str['moder']}ы</b>"
    helpers_str = f"1️⃣ <b>{post_str['helper']}и</b>"
    for admin in admins:
        admin_tid = admin['admin_tid']
        admin_post = admin['post']
        admin_user = await db.get_user_by_tid(admin_tid); admin_link = admin_user['link']

        if admin_tid == web['owner_tid']:
            owner_and_heir_str += f"\n{admin_link} ({post_str[admin_post]})"
            if admin_tid == chat['owner_tid']:
                owner_and_heir_str += " (Владелец этого чата)"
        elif admin_tid == web['heir_tid']:
            owner_and_heir_str += f"\n{admin_link} (Наследник) ({post_str[admin_post]})"
            if admin_tid == chat['owner_tid']:
                owner_and_heir_str += " (Владелец этого чата)"

        elif admin_post == "admin":
            admins_str += "\n" + admin_link
            if admin_tid == chat['owner_tid']:
                admins_str += " (Владелец этого чата)"
        elif admin_post == "adminjr":
            adminsjr_str += "\n" + admin_link
            if admin_tid == chat['owner_tid']:
                adminsjr_str += " (Владелец этого чата)"
        elif admin_post == "moder":
            moders_str += "\n" + admin_link
        elif admin_post == "helper":
            helpers_str += "\n" + admin_link
        # Проверка на "(Владелец этого чата)" есть только у владельца паутины, админа и младшего админа, 
        # потому что владельцы чатов не могут иметь должности ниже.

    ## Итоговый вывод
    owner_and_heir_str += "\n\n"
    admins_str += "\n\n"
    adminsjr_str += "\n\n"
    moders_str += "\n\n"
    helpers_str += "\n\n"

    if admins_str == f"4️⃣ <b>{post_str['admin']}ы</b>\n\n":
        admins_str = ""
    if adminsjr_str == f"3️⃣ <b>{post_str['adminjr']}ы</b>\n\n":
        adminsjr_str = ""
    if moders_str == f"2️⃣ <b>{post_str['moder']}ы</b>\n\n":
        moders_str = ""
    if helpers_str == f"1️⃣ <b>{post_str['helper']}и</b>\n\n":
        helpers_str = ""

    await msg.edit_text(
        text=(
            owner_and_heir_str +
            admins_str +
            adminsjr_str +
            moders_str +
            helpers_str
        )
    )

# Список всех незакрытых жалоб (жалобы, репорты)
# Вводится только в админ чате.

async def reports(message: Message):
    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    # Проверка на то, что команда введена в админ чате
    if message.chat.id != web['admin_chat_tid']: return

    # Получаю список всех репортов в этой паутине
    await db.cur.execute("SELECT * FROM reports WHERE web_id = %s", (web['web_id'],))
    reports = await db.cur.fetchall()
    if not reports:
        return await message.reply("В вашей паутине нет активных жалоб. Так держать!") # Вывод

    # Вывод
    for report in reports:
        report_id = report['report_id']
        sender_tid = report['sender_tid']
        target_tid = report['target_tid']
        sender = await db.get_user_by_tid(sender_tid)
        target = await db.get_user_by_tid(target_tid)
        chat = await db.get_user_by_tid(report['chat_tid'])

        await message.answer(
            f"❗️ Жалоба на {target['link']} (#{report_id})\n"
            f"🆔 <code>@{target_tid}</code>\n"
            f"🗣 Отправил {sender['link']} из чата {chat['link']}\n"
            f"<blockquote>{report['reason']}</blockquote>\n\n"
            f"🔗 <b>https://t.me/c/{str(web['admin_chat_tid']).removeprefix("-100")}/{report['message_tid_bot_admin']}</b>"
        )

# Информация о наказаниях пользователя (причина, наказания)
# Показывает инфу о наложенных наказаниях на данного пользователя
# в данной паутине.

async def restr_reason(message: Message):
    # Получение отправителя и получателя
    sender_and_target = await get_sender_and_target(message)
    if sender_and_target is None:
        return
    sender_user, target_user = sender_and_target

    sender_tid = sender_user['tid'] # TID отправителя
    target_tid = target_user['tid'] # TID получателя

    # Проверка корректности отправителя и получателя
    if sender_tid == target_tid: return await message.reply("Нельзя взаимодействовать с самим собой.")
    if target_tid == BOT_TID:    return await message.reply("Нельзя взаимодействовать с ботом.")

    # Получение чата и паутины
    chat_and_web = await get_chat_and_web(message)
    if chat_and_web is None:
        return
    chat, web = chat_and_web

    target_restrs = await db.get_restrs_by_user_tid_in_web(target_tid, web['web_id'])
    if not target_restrs:
        return await message.reply(f"У этого пользователя нет наказаний в паутине <b>{web['forename']}</b>.") # ВЫывод

    else:
        for restr in target_restrs:
            admin_user = await db.get_user_by_tid(restr['admin_tid'])
            date_reg = await parse_date(restr['date_reg'], "HH:mm d MMMM")
            date_until = await parse_date(restr['date_until'], "HH:mm d MMMM")

            if restr['restr'] == "ban":
                return await message.reply(
                    # Вывод
                    text=(
                        f"⛔ {target_user['link']}, глобальный бан в паутине чатов <b>{web['forename']}</b> до <b>{date_until}</b>\n"
                        f"🆔 <code>@{target_tid}</code>\n"
                        f"⏳ Выдано <b>{date_reg}</b>\n"
                        f"🛡️ Выдал {admin_user['link']}\n"
                        f"<blockquote>{restr['reason']}</blockquote>"
                    )
                )
            if restr['restr'] == "mute":
                return await message.reply(
                    # Вывод
                    text=(
                        f"🔇 {target_user['link']}, глобальный мут в паутине чатов <b>{web['forename']}</b> до <b>{date_until}</b>\n"
                        f"🆔 <code>@{target_tid}</code>\n"
                        f"⏳ Выдано <b>{date_reg}</b>\n"
                        f"🛡️ Выдал {admin_user['link']}\n"
                        f"<blockquote>{restr['reason']}</blockquote>"
                    )
                )

##################################
#   Команды для личных чатов     #
##################################

# Приветственное сообщение (/start)

@rt.message(CommandStart(ignore_case=True, deep_link=False))
async def introduce(message: Message):
    if message.chat.type != "private": return
    await on_every_message(message=message)

    # Вывод
    emoji = await rndemoji()

    await message.answer(
        text="🫆 <i>Установка меню</i>",
        reply_markup=await kb.main_menu()
    )
    await message.answer(
        text=(
            f"{emoji} <b><a href='https://t.me/{BOT_USERNAME}'>{BOT_FULL_NAME}</a></b>\n\n"
             "Этот бот позволяет объединить несколько чатов в одну паутину, "
             "позволяя централизировать несколько проектов и объединяться с другими чатами.\n\n"
             "🔨 <b>Глобальный бан:</b> Если забаненный в одном чате человек, "
             "войдёт в другой чат, но из той же паутины, то бот автоматически забанит его и там.\n"
             "🔇 <b>Глобальный мут:</b> Замученный в одном чате человек, не сможет писать сообщения в другой чате, из той же паутины.\n"
             "👟 <b>Глобальный кик:</b> Кик человека из одного чата, кикнет его из всех чатов этой паутины.\n"
             "🛡️ <b>Глобальная модерация:</b> Админ из одного чата, будет админом во всех чатах паутины.\n\n"
             "<b>Один</b> человек может иметь <b>одну</b> паутину,\n"
             "<b>один</b> чат может состоять в <b>одной</b> паутине!\n\n"
             "Создай паутину используя меню, добавляй бота в нужные чаты и пиши там команду <code>+паутина</code> 👇"
        ),
        reply_markup=await kb.add_to_chat()
    )

#####################################################################
#   ГЛАВНЫЙ ОБРАБОТЧИК                                              #
#   Перед тем, как обработать команду, он добавлят человека,        #
#   человека которому ответили и чат в БД (on_every_message()).     #
#   А даже если введена не команда, БД всё равно пополнится.        #
#   (ну и плюс есть другой больший потенциал)                       #
#####################################################################

@rt.message()
async def main(message: Message):
    await on_every_message(message=message)

    if message.text is None:
        return

    msgtext = message.text.strip()
    msgtextcf = msgtext.casefold().strip()

    if msgtextcf in ("бот", "кинг", "пинг", "пиу", "пиф", "пук"):
        return await ping(message)
    if msgtext in ("🗂️ Мои паутины", "админ панель"):
            return await get_web(message)

    elif message.chat.type == "private":
        if msgtext[2:] == "Создать паутину" or message.text[3:] == "Создать паутину":
            return await mk_web(message)
        elif msgtext == "➕ Добавить в чат":
            return await add_to_chat(message)
        elif msgtext == "📚 Команды":
            return await commands_list(message)

    elif message.chat.type in ("group", "supergroup"):
        if msgtextcf == "паутина":
            return await get_chat(message) 
        elif msgtextcf == "+паутина":
            return await mk_chat(message)
        elif msgtextcf == "-паутина":
            return await rm_chat(message)
        elif msgtextcf == "сделать админским":
            return await mk_admin_chat(message)

        elif msgtextcf.startswith("повысить"):
            return await admin_up(message)
        elif msgtextcf.startswith("понизить"):
            return await admin_down(message)
        elif msgtextcf.startswith("снять"):
            return await admin_fire(message)

        elif msgtextcf.startswith(("гбан", "глбан", "глобан")):
            return await gban(message)
        elif msgtextcf.startswith(("гразбан", "глразмут", "глоразбан")):
            return await gunban(message)
        elif msgtextcf.startswith(("гмут", "глмут", "гломут")):
            return await gmute(message)
        elif msgtextcf.startswith(("гразмут", "глразмут", "глоразмут")):
            return await gunmute(message)
        elif msgtextcf.startswith(("гкик", "глкик", "глокик")):
            return await gkick(message)

        elif msgtextcf.startswith(("жалоба", ".жалоба", "репорт", ".репорт")):
            return await report(message)
        elif msgtextcf == "чаты":
            return await chats_tid(message)
        elif msgtextcf in ("админы", "гладмины", "глоадмины", "кто админ", "кто гладмин", "кто глоадмин"):
            return await admins(message)
        elif msgtextcf in ("жалобы", "репорты"):
            return await reports(message)
        elif msgtextcf.startswith(("причина", "наказания")):
            return await restr_reason(message)
