from psycopg import AsyncConnection
from psycopg.rows import dict_row
from aiogram.types import User, Chat, Message

from emoji import is_emoji
from random import choice
from string import ascii_letters, digits

import config

class Database():
    def __init__(self):
        self.conn = None
        self.cur = None

    async def connect(self):
        self.conn = await AsyncConnection.connect(
            host        = config.DB_HOST,
            dbname      = config.DB_DBNAME,
            port        = config.DB_PORT,
            user        = config.DB_USER,
            password    = config.DB_PASSWORD,
            row_factory = dict_row
        )
        self.cur = self.conn.cursor()

    async def mkid(self, table: str = None) -> str:
        '''
        Генерирует айди в формате sdsd, с символами a-Z 0-9. Этот формат может сгенерировать 270400 уникальных айди.  
        ``table`` нужен, так как функция автоматически проверяет, что сгенерированный айди действительно уникален.
        Без него функция просто сгенерирует и вернёт айди, без всяких проверок
        '''
        if table is None:
            return choice(ascii_letters) + choice(digits) + choice(ascii_letters) + choice(digits)
        while True:
            new_id = choice(ascii_letters) + choice(digits) + choice(ascii_letters) + choice(digits)
            await self.cur.execute(f"SELECT 1 FROM {table} WHERE {table[:-1]}_id = %s", (new_id,))
            if not await self.cur.fetchone():
                return new_id

    ###################################
    #         Таблица users           #
    #                                 #
    #    mk_user()  get_username()    #
    #    rm_user()  get_tid()         #
    ###################################

    async def mk_user(self, user: User = None, chat: Chat = None) -> dict:
        '''
        Записывает данные пользователя/чата в БД. Если они уже есть - обновляет их.  
        Возвращает словарь с данными. Принимает строго либо user, либо chat.
        '''
        if bool(user) == bool(chat):
            return None

        tid = user.id if user else chat.id
        first_name_title = user.first_name if user else chat.title
        last_name = user.last_name if user else None
        full_name = user.full_name if user else first_name_title
        username = user.username if user else chat.username
        link = f"<a href='https://t.me/{username}'>{full_name}</a>" if username else full_name

        try:
            if username is not None:
                # Если в БД есть запись с такимже юзернеймом, то устаналиваем
                # её на NULL, т. к. если его юз занят кем-то другим, то значит что изначальный владелец уже изменил его
                await self.cur.execute(
                    "UPDATE users SET username = NULL WHERE username = %s AND tid != %s",
                    (username, tid)
                )

            await self.cur.execute(
                """INSERT INTO users (tid, first_name_title, last_name, full_name, username, link) VALUES (%s, %s, %s, %s, %s, %s) 
                   ON CONFLICT (tid) DO UPDATE SET 
                   username = EXCLUDED.username,
                   first_name_title = EXCLUDED.first_name_title,
                   last_name = EXCLUDED.last_name,
                   full_name = EXCLUDED.full_name,
                   link = EXCLUDED.link
                   RETURNING *""",
                (tid, first_name_title, last_name, full_name, username, link)
            )
            result = await self.cur.fetchone()
            await self.conn.commit()
            return result
        except Exception as e:
            print(f"error: database: mk_user(): {e}")
            await self.conn.rollback()
            return None

    async def get_user_by_tid(self, tid: int) -> str:
        '''Получает пользователя по TID'''
        try:
            await self.cur.execute("SELECT * FROM users WHERE tid = %s", (tid,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_username(): {e}")
            return None

    async def get_username(self, tid: int) -> str:
        '''Получает @юзернейм пользователя по TID'''
        try:
            await self.cur.execute("SELECT username FROM users WHERE tid = %s", (tid,))
            result = await self.cur.fetchone()
            if result and result['username']:
                return result['username'] if result else None
        except Exception as e:
            print(f"error: database: get_username(): {e}")
            return None

    async def get_tid(self, username: str) -> int:
        '''Получает TID пользователя по @юзернейму'''
        try:
            await self.cur.execute("SELECT tid FROM users WHERE username = %s", (username,))
            result = await self.cur.fetchone()
            return result['tid'] if result else None
        except Exception as e:
            print(f"error: database: get_tid(): {e}")
            return None

    async def rm_user(self, tid: int) -> bool:
        '''Удаляет пользователя из БД'''
        try:
            await self.cur.execute("DELETE FROM users WHERE tid = %s", (tid,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_user(): {e}")
            await self.conn.rollback()
            return False

    #################################################################################
    #                              Таблица webs                                     #
    #                                                                               #
    #    mk_web()                upd_web_name()            upd_web_heir()           #
    #    rm_web()                upd_web_descr()           upd_web_heirtoowner()    #
    #    get_web()               upd_web_owner()                                    #
    #    get_web_by_owner_tid()  upd_web_admin_chat_tid()                           #
    #################################################################################

    async def mk_web(self, forename: str, owner_tid: int) -> dict:
        '''Создает паутину и делает создателя владельцем'''
        if len(forename) > 64:
            # Если данный @юзернейм больше 64 символов - просто урезаю
            forename = forename[:64]

        try:
            web_id = await self.mkid("webs")

            await self.cur.execute(
                "INSERT INTO webs (web_id, forename, owner_tid) VALUES (%s, %s, %s) RETURNING *",
                (web_id, forename, owner_tid)
            )
            web = await self.cur.fetchone()
            await self.mk_admin(owner_tid, web_id, "owner")
            await self.conn.commit()
            return web
        except Exception as e:
            print(f"error: database: mk_web(): {e}")
            await self.conn.rollback()
            return None

    async def get_web(self, web_id) -> dict:
        '''Получает инфо о паутине по её ID'''
        try:
            await self.cur.execute("SELECT * FROM webs WHERE web_id = %s", (web_id,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_web(): {e}")
            return None

    async def get_web_by_owner_tid(self, owner_tid: int) -> dict:
        '''Получает инфо о паутине по TID её владельца (один человек может владеть одной паутиной)'''
        try:
            await self.cur.execute("SELECT * FROM webs WHERE owner_tid = %s", (owner_tid,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_web_by_owner_tid(): {e}")
            return None

    async def upd_web_name(self, web_id: str, forename: str, emoji: str) -> bool:
        '''Обновляет имя и эмодзи паутины'''
        if emoji and not is_emoji(emoji):
            # Если данный эмодзи не эмодзи
            raise ValueError("emoji should be emoji (wow)")
        if len(forename) > 64:
            # Если данный @юзернейм больше 64 символов - просто урезаю
            forename = forename[:64]

        try:
            await self.cur.execute(
                "UPDATE webs SET forename = %s, emoji = %s WHERE web_id = %s",
                (forename, emoji, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_name(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_owner(self, web_id: str, new_owner_tid: int, old_owner_tid: int = None) -> bool:
        '''
        Передает права владения паутиной другому пользователю. Старого владельца назначает хелпером и,
        если в паутине не назначен наследник, наследником.  
        ``old_owner_tid`` может быть None на случай, если Телеграм аккаунт старого владельца удалён
        '''
        try:
            web = await self.get_web(web_id)
            if not web:
                return False
                
            heir_tid = web['heir_tid']

            # Если новый владелец был наследником, забираем у него эту должность
            if heir_tid == new_owner_tid:
                await self.upd_web_heir(web_id, None)
                heir_tid = None

            if old_owner_tid is not None:
                await self.upd_admin_post(old_owner_tid, web_id, "helper")

                # Если в паутине не назначен наследник,
                # то старый владелец становится им
                if heir_tid is None:
                    await self.upd_web_heir(web_id, old_owner_tid)

            await self.cur.execute(
                "UPDATE webs SET owner_tid = %s WHERE web_id = %s",
                (new_owner_tid, web_id)
            )
            await self.upd_admin_post(new_owner_tid, web_id, "owner")
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_owner(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_heir(self, web_id: str, heir_tid: int) -> bool:
        '''Изменяет наследника в паутине'''
        try:
            await self.cur.execute(
                "UPDATE webs SET heir_tid = %s WHERE web_id = %s",
                (heir_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_heir(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_heirtoowner(self, web_id: str, heir_tid: int, owner_tid: int = None) -> bool:
        '''
        Меняет TID владельца паутины на наследника.  
        Эта функция лишь использует две другие функции: ``upd_web_owner()`` и ``upd_web_heir()``.
        Если передать ``owner_tid``, то старый владелец станет хелпером и новым наследником.
        '''
        try:
            await self.upd_web_heir(web_id, None)
            if owner_tid:
                await self.upd_web_owner(web_id, heir_tid, owner_tid)
            else:
                await self.upd_web_owner(web_id, heir_tid)
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_heirtoowner(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_admin_chat_tid(self, web_id: str, admin_chat_tid: int) -> bool:
        '''Закрепляет админский чат за паутиной'''
        try:
            await self.cur.execute(
                "UPDATE webs SET admin_chat_tid = %s WHERE web_id = %s",
                (admin_chat_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_admin_chat_tid(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_descr(self, web_id: str, descr: str) -> bool:
        '''Обновляет описание паутины'''
        if len(descr) > 200:
            # Если данное описание больше 200 символов - просто урезаю
            descr = descr[:200]

        try:
            await self.cur.execute(
                "UPDATE webs SET descr = %s WHERE web_id = %s",
                (descr, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_descr(): {e}")
            await self.conn.rollback()
            return False

    async def rm_web(self, web_id: str) -> bool:
        '''Удаляет паутину'''
        try:
            await self.cur.execute("DELETE FROM webs WHERE web_id = %s", (web_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_web(): {e}")
            await self.conn.rollback()
            return False

    #####################################
    #           chats                   #
    #                                   #
    #    mk_chat()  get_chat()          #
    #    rm_chat()  upd_chat_owner()    #
    #####################################

    async def mk_chat(self, chat_tid: int, web_id: str, owner_tid: int) -> dict:
        '''Создает чат и добавляет его в список чатов паутины'''
        try:
            await self.cur.execute(
                # Создаю запись чата в таблице chats
                "INSERT INTO chats (chat_tid, web_id, owner_tid) VALUES (%s, %s, %s) RETURNING *",
                (chat_tid, web_id, owner_tid)
            )
            chat = await self.cur.fetchone()

            await self.cur.execute(
                # Добавляю паутине в столб chats_tid данный чат
                "UPDATE webs SET chats_tid = array_append(chats_tid, %s) WHERE web_id = %s",
                (chat_tid, web_id)
            )
            await self.conn.commit()
            return chat
        except Exception as e:
            print(f"error: database: mk_chat(): {e}")
            await self.conn.rollback()
            return None

    async def get_chat(self, chat_tid: int) -> dict:
        '''Получает инфо о чате по его TID'''
        try:
            await self.cur.execute("SELECT * FROM chats WHERE chat_tid = %s", (chat_tid,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_chat(): {e}")
            return None

    async def upd_chat_owner(self, chat_tid: int, new_owner_tid: int) -> bool:
        '''Меняет данные о TID владельца данного чата'''
        try:
            await self.cur.execute(
                "UPDATE chats SET owner_tid = %s WHERE chat_tid = %s",
                (new_owner_tid, chat_tid)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_chat_owner(): {e}")
            await self.conn.rollback()
            return False

    async def rm_chat(self, chat_tid: int, web_id: str) -> bool:
        '''Удаляет чат и убирает его из списка chats_id данной паутины'''
        try:
            await self.cur.execute("DELETE FROM chats WHERE chat_tid = %s", (chat_tid,))

            await self.cur.execute(
                "UPDATE webs SET chats_tid = array_remove(chats_tid, %s) WHERE web_id = %s",
                (chat_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_chat(): {e}")
            await self.conn.rollback()
            return False

    ##########################################################
    #                       admins                           #
    #                                                        #
    #    mk_admin()  get_admin()         get_web_admins()    #
    #    rm_admin()  get_admin_by_tid()  upd_admin_post()    #
    ##########################################################

    async def mk_admin(self, admin_tid: int, web_id: str, post: str) -> dict:
        '''Назначает человека админом в конкретной паутине с конкретной ролью'''
        try:
            admin_id = await self.mkid("admins")

            if post not in ("moder", "admin", "helper", "owner"):
                # Если дана некорректная должность, то меняет её на модера
                post = "moder"
            if post == "owner":
                # Если мы создаём владельца в паутине, в которой он уже есть,
                # то меняем ему должность на хелпера
                await self.cur.execute("SELECT 1 FROM admins WHERE web_id = %s AND post = 'owner'", (web_id,))
                if await self.cur.fetchone() is not None:
                    post = "helper"

            await self.cur.execute(
                "INSERT INTO admins (admin_id, admin_tid, web_id, post) VALUES (%s, %s, %s, %s) RETURNING *",
                (admin_id, admin_tid, web_id, post)
            )
            admin = await self.cur.fetchone()
            await self.conn.commit()
            return admin
        except Exception as e:
            print(f"error: database: mk_admin(): {e}")
            await self.conn.rollback()
            return None

    async def get_admin_by_tid(self, admin_tid: int, web_id: str) -> dict:
        '''Получает данные админа в конкретной паутине по его TID'''
        try:
            await self.cur.execute(
                "SELECT * FROM admins WHERE admin_tid = %s AND web_id = %s",
                (admin_tid, web_id)
            )
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_admin_by_tid(): {e}")
            return None

    async def get_admin(self, admin_id: str) -> dict:
        '''Получает данные админа по его ID'''
        try:
            await self.cur.execute("SELECT * FROM admins WHERE admin_id = %s", (admin_id,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_admin(): {e}")
            return None

    async def get_web_admins(self, web_id: str) -> list[dict]:
        '''Получает список всех админов из данной паутины'''
        try:
            await self.cur.execute("SELECT * FROM admins WHERE web_id = %s", (web_id,))
            return await self.cur.fetchall()
        except Exception as e:
            print(f"error: database: get_web_admins(): {e}")
            return []

    async def upd_admin_post(self, admin_tid: int, web_id: str, post: str) -> bool:
        '''Обновляет должность админа в конкретной паутине'''
        try:
            if post not in ("moder", "admin", "helper", "owner"):
                # Если дана некорректная должность, то меняет её на модера
                post = "moder"
            if post == "owner":
                # Если мы создаём владельца в паутине, в которой он уже есть,
                # то меняем ему должность на хелпера
                await self.cur.execute("SELECT 1 FROM admins WHERE web_id = %s AND post = 'owner'", (web_id,))
                if await self.cur.fetchone() is not None:
                    post = "helper"

            await self.cur.execute(
                "UPDATE admins SET post = %s WHERE admin_tid = %s AND web_id = %s",
                (post, admin_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_admin_post(): {e}")
            await self.conn.rollback()
            return False

    async def rm_admin(self, admin_tid: int, web_id: str) -> bool:
        '''Снимает админа с должности в конкретной паутине'''
        try:
            # Проверка на то, что удаляемый админ является наследником паутины.
            # Если является - обнуляем наследника в этой паутине
            await self.cur.execute("SELECT heir_tid FROM webs WHERE web_id = %s", (web_id,))
            result = await self.cur.fetchone()
            if result and result['heir_tid'] == admin_tid:
                await self.upd_web_heir(web_id, None)

            # Непосредственное удаление админа
            await self.cur.execute(
                "DELETE FROM admins WHERE admin_tid = %s AND web_id = %s",
                (admin_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_admin(): {e}")
            await self.conn.rollback()
            return False

    ########################################################################################
    #                                   restrs                                             #
    #                                                                                      #
    #    mk_restr()          get_restr()               get_restrs_by_user_tid_in_web()     #
    #    rm_restr()          get_restrs_by_user_tid()  get_restrs_by_admin_tid_in_web()    #
    #    upd_restr_reason()  upd_restr_date_until()                                        #
    ########################################################################################

    async def mk_restr(self, web_id: str, user_tid: int, restr: str, admin_tid: int, reason: str = None, date_until: float = None) -> dict:
        '''Создает запись о бане/муте в конкретной паутине'''
        if restr not in ("ban", "mute"):
            return None

        try:
            restr_id = await self.mkid("restrs")

            await self.cur.execute(
                "INSERT INTO restrs (restr_id, web_id, user_tid, restr, admin_tid, reason, date_until) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
                (restr_id, web_id, user_tid, restr, admin_tid, reason, date_until)
            )
            restr = await self.cur.fetchone()
            await self.conn.commit()
            return restr
        except Exception as e:
            print(f"error: database: mk_restr(): {e}")
            await self.conn.rollback()
            return None

    async def get_restr(self, restr_id: str) -> dict:
        '''Получает наказание по его ID'''
        try:
            await self.cur.execute("SELECT * FROM restrs WHERE restr_id = %s", (restr_id),)
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_restr(): {e}")
            return False

    async def get_restrs_by_user_tid(self, user_tid: int) -> dict:
        '''Получает все наказания данного человека'''
        try:
            await self.cur.execute("SELECT * FROM restrs WHERE user_tid = %s", (user_tid,))
            return await self.cur.fetchall()
        except Exception as e:
            print(f"error: database: get_restrs_by_user_tid(): {e}")
            return False

    async def get_restrs_by_user_tid_in_web(self, user_tid: int, web_id: str) -> dict:
        '''Получает все наказания данного человека в конкретной паутине'''
        try:
            await self.cur.execute(
                "SELECT * FROM restrs WHERE user_tid = %s AND web_id = %s",
                (user_tid, web_id)
            )
            return await self.cur.fetchall()
        except Exception as e:
            print(f"error: database: get_restrs_by_user_tid_in_web(): {e}")
            return False

    async def get_restrs_by_admin_tid_in_web(self, admin_tid: int, web_id: str) -> dict:
        '''Получает все наказания данного человека в конкретной паутине'''
        try:
            await self.cur.execute(
                "SELECT * FROM restrs WHERE admin_tid = %s AND web_id = %s",
                (admin_tid, web_id)
            )
            return await self.cur.fetchall()
        except Exception as e:
            print(f"error: database: get_restrs_by_admin_tid_in_web(): {e}")
            return False

    async def upd_restr_reason(self, restr_id: str, reason: str) -> bool:
        '''Изменяет причину наказания'''
        try:
            await self.cur.execute(
                "UPDATE restrs SET reason = %s WHERE restr_id = %s",
                (reason, restr_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_restr_reason(): {e}")
            await self.conn.rollback()
            return False

    async def upd_restr_date_until(self, restr_id: str, date_until: float) -> bool:
        '''Изменяет время истечения наказания'''
        try:
            await self.cur.execute(
                "UPDATE restrs SET date_until = %s WHERE restr_id = %s",
                (date_until, restr_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_restr_date_until(): {e}")
            await self.conn.rollback()
            return False

    async def rm_restr(self, restr_id: str) -> bool:
        '''Удаляет наказание'''
        try:
            await self.cur.execute("DELETE FROM restrs WHERE restr_id = %s", (restr_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_restr(): {e}")
            await self.conn.rollback()
            return False

    ################################################
    #              Таблица reports                 #
    #                                              #
    #    mk_report()  get_report()  rm_report()    #
    ################################################

    async def mk_report(self, web_id: str, message_user: Message, message_tid_bot_admin: int, message_tid_bot_user: int) -> dict:
        '''Создает запись жалобы'''
        report_id = await self.mkid("reports")
        chat_tid = message_user.chat.id
        message_tid_user = message_user.message_id
        message_tid_user_replyto = message_user.reply_to_message.message_id
        sender_tid = message_user.from_user.id
        target_tid = message_user.reply_to_message.from_user.id
        reason = message_user.text.split(" ", 1)
        if len(reason) == 2:
            reason = reason[-1]
        else:
            reason = "Причина не указана."

        try:
            await self.cur.execute(
                "INSERT INTO reports (report_id, web_id, chat_tid, message_tid_user, message_tid_user_replyto, message_tid_bot_admin, message_tid_bot_user, sender_tid, target_tid, reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
                (report_id, web_id, chat_tid, message_tid_user, message_tid_user_replyto, message_tid_bot_admin, message_tid_bot_user, sender_tid, target_tid, reason)
            )
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: mk_report(): {e}")
            await self.conn.rollback()
            return False

    async def get_report(self, report_id: str) -> dict:
        try:
            await self.cur.execute("SELECT * FROM reports WHERE report_id = %s", (report_id,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_report(): {e}")
            return False

    async def rm_report(self, report_id: str) -> bool:
        '''Удаляет жалобу'''
        try:
            await self.cur.execute("DELETE FROM reports WHERE report_id = %s", (report_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_report(): {e}")
            await self.conn.rollback()
            return False
