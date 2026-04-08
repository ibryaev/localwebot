from psycopg import AsyncConnection
from psycopg.rows import dict_row

from emoji import is_emoji
from datetime import datetime
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

    async def mkid(self, table: str) -> str:
        '''Генерирует айди в формате "%%s%%%d%%%s%%d". Этот формат может сгенерировать 270400 уникальных айди'''
        while True:
            new_id = choice(ascii_letters) + choice(digits) + choice(ascii_letters) + choice(digits)
            await self.cur.execute(f"SELECT 1 FROM {table} WHERE {table[:-1]}_id = %s", (new_id,))
            if not await self.cur.fetchone():
                return new_id

    # users

    async def mk_user(self, tid: int, username: str) -> bool:
        '''Записывает пользователя в базу. Если он уже есть - обновляет username'''
        try:
            await self.cur.execute(
                "INSERT INTO users (tid, username) VALUES (%s, %s) ON CONFLICT (tid) DO UPDATE SET username = EXCLUDED.username",
                (tid, username)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: mk_user(): {e}")
            await self.conn.rollback()
            return False

    async def get_username(self, tid: int) -> dict:
        '''Получает @юзернейм пользователя по TID'''
        try:
            await self.cur.execute("SELECT * FROM users WHERE tid = %s", (tid,))
            user = await self.cur.fetchone()

            if user and user['username']:
                return user['username']
            elif user and user['username'] is None:
                return "<code>" + user['tid'] + "</code>"
        except Exception as e:
            print(f"error: database: get_user(): {e}")
            return None

    async def get_tid(self, username: str) -> int:
        '''Получает TID пользователя по @юзернейму'''
        try:
            await self.cur.execute("SELECT tid FROM users WHERE username = %s", (username,))
            user = await self.cur.fetchone()
            return user['tid'] if user else None
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

    # webs

    async def mk_web(self, forename: str, owner_tid: int) -> dict:
        '''Генерирует уникальный web_id, создает паутину и делает создателя владельцем'''
        if len(forename) > 32:
            forename = forename[:32]

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

    async def get_web(self, web_id: str) -> dict:
        '''Получает инфо о паутине по её ID'''
        try:
            await self.cur.execute("SELECT * FROM webs WHERE web_id = %s", (web_id,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_web(): {e}")
            return None

    async def get_web_tid(self, owner_tid: int) -> dict:
        '''Получает инфо о паутине по TID её владельца'''
        try:
            await self.cur.execute("SELECT * FROM webs WHERE owner_tid = %s", (owner_tid,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_web_tid(): {e}")
            return None

    # async def get_web_owner(self, owner_tid: int) -> dict:
    #     '''Ищет паутину, где данный пользователь является владельцем'''
    #     try:
    #         await self.cur.execute("SELECT * FROM webs WHERE owner_tid = %s", (owner_tid,))
    #         return await self.cur.fetchone()
    #     except Exception as e:
    #         print(f"error: database: get_web_owner(): {e}")
    #         return None

    async def upd_web_name(self, web_id: str, forename: str, emoji: str) -> bool:
        '''Обновляет имя и эмодзи паутины'''
        if emoji and not is_emoji(emoji):
            raise ValueError("emoji should be emoji (wow)")
        if len(forename) > 32:
            raise ValueError("forename cannot be longer than 32 symbols")
        
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

    async def upd_web_owner(self, web_id: str, old_owner_tid: int, new_owner_tid: int) -> bool:
        '''Передает права владения паутиной другому админу'''
        try:
            await self.cur.execute(
                "UPDATE webs SET owner_tid = %s WHERE web_id = %s",
                (new_owner_tid, web_id)
            )
            await self.upd_admin_post(old_owner_tid, web_id, "helper")
            await self.upd_admin_post(new_owner_tid, web_id, "owner")
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_owner(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_heir(self, web_id: str, heir_tid: int) -> bool:
        '''Назначает наследника на сетку'''
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

    async def upd_web_heirtoowner(self, web_id: str, owner_tid: int, heir_tid: int) -> bool:
        '''Меняет TID владельца сетки на наследника'''
        try:
            await self.upd_web_owner(web_id, owner_tid, heir_tid)
            await self.upd_web_heir(web_id, None)
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_web_heirtoowner(): {e}")
            await self.conn.rollback()
            return False

    async def upd_web_admin_chat_tid(self, web_id: str, admin_chat_tid: int) -> bool:
        '''Назначает админский чат на сетку'''
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
            raise ValueError("Web description cannot be larger than 200 symbols")

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
        '''Удаляет паутину. Связанные чаты и админы удалятся по CASCADE'''
        try:
            await self.cur.execute("DELETE FROM webs WHERE web_id = %s", (web_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_web(): {e}")
            await self.conn.rollback()
            return False

    # chats

    async def mk_chat(self, chat_tid: int, web_id: str, owner_tid: int) -> dict:
        '''Создает чат и добавляет его в список чатов паутины'''
        try:
            await self.cur.execute(
                "INSERT INTO chats (chat_tid, web_id, owner_tid) VALUES (%s, %s, %s) RETURNING *",
                (chat_tid, web_id, owner_tid)
            )
            chat = await self.cur.fetchone()

            await self.cur.execute(
                "UPDATE webs SET chats_tid = array_append(chats_tid, %s) WHERE web_id = %s",
                (chat_tid, web_id)
            )
            await self.conn.commit()
            return chat
        except Exception as e:
            print(f"error: database: mk_chat(): {e}")
            await self.conn.rollback()
            return None

    async def get_chat(self, chat_tid: str) -> dict:
        '''Получает инфо о чате по её TID'''
        try:
            await self.cur.execute("SELECT * FROM chats WHERE chat_tid = %s", (chat_tid,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_chat(): {e}")
            return None

    async def upd_chat_owner(self, chat_tid: int, new_owner_tid: int) -> bool:
        '''Меняет владельца конкретного чата'''
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
        '''Удаляет чат и убирает его из массива в webs'''
        try:
            await self.cur.execute("DELETE FROM chats WHERE chat_tid = %s", (chat_tid,))
            
            # Вычищаем из массива webs.chats_tid
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

    # admins

    async def mk_admin(self, admin_tid: int, web_id: str, post: str) -> dict:
        '''Назначает человека админом в конкретной сетке с конкретной ролью'''
        admin_id = None

        try:
            admin_id = await self.mkid("admins")

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

    async def get_admin(self, admin_tid: int, web_id: str) -> dict:
        '''Получает данные админа в конкретной паутине по его TID'''
        try:
            await self.cur.execute(
                "SELECT * FROM admins WHERE admin_tid = %s AND web_id = %s",
                (admin_tid, web_id)
            )
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_admin(): {e}")
            return None

    async def get_admin_id(self, admin_id: str) -> dict:
        '''Получает данные админа, находя его по уникальному ID'''
        try:
            await self.cur.execute("SELECT * FROM admins WHERE admin_id = %s", (admin_id,))
            return await self.cur.fetchone()
        except Exception as e:
            print(f"error: database: get_admin_id(): {e}")
            return None

    # async def get_admin_webs(self, admin_tid: int) -> list:
    #     '''Получает список всех сеток, где пользователь является админом'''
    #     try:
    #         await self.cur.execute("SELECT * FROM admins WHERE admin_tid = %s", (admin_tid,))
    #         return await self.cur.fetchall()
    #     except Exception as e:
    #         print(f"error: database: get_admin_webs(): {e}")
    #         return []

    async def get_web_admins(self, web_id: str) -> list[dict]:
        '''Получает список всех админов из данной сетки'''
        try:
            await self.cur.execute("SELECT * FROM admins WHERE web_id = %s", (web_id,))
            return await self.cur.fetchall()
        except Exception as e:
            print(f"error: database: get_web_admins(): {e}")
            return []

    async def upd_admin_post(self, admin_tid: int, web_id: str, new_post: str) -> bool:
        '''Обновляет должность админа в конкретной сетке'''
        try:
            await self.cur.execute(
                "UPDATE admins SET post = %s WHERE admin_tid = %s AND web_id = %s",
                (new_post, admin_tid, web_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_admin_post(): {e}")
            await self.conn.rollback()
            return False

    async def rm_admin(self, admin_tid: int, web_id: str) -> bool:
        '''Снимает админа с должности в конкретной сетке'''
        try:
            await self.cur.execute(
                "DELETE FROM admins WHERE admin_tid = %s AND web_id = %s",
                (admin_tid, web_id)
            )
            await self.upd_web_heir(web_id, None)
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_admin(): {e}")
            await self.conn.rollback()
            return False

    # restrs

    async def mk_restr(self, web_id: str, user_tid: int, restr_type: str, admin_tid: int, reason: str = None, until: datetime = None) -> dict:
        '''Создает запись о бане/муте в конкретной сетке'''
        if restr_type not in ('ban', 'mute'):
            raise ValueError("restrs_type must be in ('ban', 'mute')")

        try:
            restr_id = await self.mkid("restrs")

            await self.cur.execute(
                "INSERT INTO restrs (restr_id, web_id, user_tid, restr, admin_tid, reason, date_until) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                (restr_id, web_id, user_tid, restr_type, admin_tid, reason, until)
            )
            restr = await self.cur.fetchone()
            await self.conn.commit()
            return restr
        except Exception as e:
            print(f"error: database: mk_restr(): {e}")
            await self.conn.rollback()
            return None

    async def upd_restr_until(self, restr_id: int, new_until: datetime) -> bool:
        '''Изменяет время истечения наказания'''
        try:
            await self.cur.execute(
                "UPDATE restrs SET date_until = %s WHERE restr_id = %s",
                (new_until, restr_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: upd_restr_until(): {e}")
            await self.conn.rollback()
            return False

    async def rm_restr(self, restr_id: int) -> bool:
        '''Удаляет наказание'''
        try:
            await self.cur.execute("DELETE FROM restrs WHERE restr_id = %s", (restr_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"error: database: rm_restr(): {e}")
            await self.conn.rollback()
            return False
