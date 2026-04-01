from psycopg import AsyncConnection
from psycopg.rows import dict_row
from emoji import is_emoji

class Database():
    def __init__(self):
        self.conn_params = {
            "host":     "localhost",
            "fullname": "postgres",
            "port":     "5432",
            "user":     "postgres",
            "password": "nicetea"
        }
        self.conn = None
        self.cur = None

    async def connect(self):
        self.conn = await AsyncConnection.connect(
            host        = self.conn_params["host"],
            dbname      = self.conn_params["fullname"],
            port        = self.conn_params["port"],
            user        = self.conn_params["user"],
            password    = self.conn_params["password"],
            row_factory = dict_row
        )
        self.cur = self.conn.cursor()

    async def mkweb(self, forename: str, tid_owner: int) -> dict:
        '''Создаёт паутину в таблице webs, а также её создателя в таблице admins'''
        try:
            await self.cur.execute(
                "INSERT INTO webs (forename, tid_owner) VALUES (%s, %s) RETURNING *",
                (forename, tid_owner)
            )

            web = await self.cur.fetchone()

            await self.cur.execute(
                "INSERT INTO admins (tid_admin, id_web, post) VALUES (%s, %s, %s)",
                (tid_owner, web['id_web'], "owner")
            )
            
            await self.conn.commit()
            return web

        except Exception as e:
            print(f"error: database: mkweb(): {e}")
            await self.conn.rollback()
            return None

    async def web_get(self, tid_owner: int) -> dict:
        '''Возвращает полную информацию о паутине, по Telegram ID её владельца'''
        try:
            await self.cur.execute(
                "SELECT * FROM webs WHERE tid_owner = %s",
                (tid_owner,)
            )
            web = await self.cur.fetchone()
            return web

        except Exception as e:
            print(f"error: database: web_read(): {e}")
            return None

    async def web_get_id(self, tid_owner: int) -> int:
        '''Возвращает ID паутины, по Telegram ID её владельца'''
        try:
            await self.cur.execute(
                "SELECT id_web FROM webs WHERE tid_owner = %s",
                (tid_owner,)
            )
            web = await self.cur.fetchone()
            return web['id_web'] if web else None

        except Exception as e:
            print(f"error: database: web_get_id(): {e}")
            return None

    async def web_rename(self, id_web: int, new_forename: str, new_emoji: str) -> bool:
        '''Переименовывает и меняет иконку паутине'''
        if not is_emoji(new_emoji):
            raise ValueError("new_emoji should be an emoji (unexpected?)")

        try:
            await self.cur.execute(
                "UPDATE webs SET forename = %s, emoji = %s WHERE id_web = %s",
                (new_forename, new_emoji, id_web)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: web_rename(): {e}")
            await self.conn.rollback()
            return False

    async def web_transfer_ownership(self, id_web: int, tid_owner: int, new_tid_owner: int) -> bool:
        '''Меняет владельца паутины'''
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_owner = %s WHERE id_web = %s",
                (new_tid_owner, id_web)
            )
            await self.admin_edit_post(tid_owner, id_web, "helper")
            await self.admin_edit_post(new_tid_owner, id_web, "owner")
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: web_edit_owner(): {e}")
            await self.conn.rollback()
            return False

    async def web_tid_chats_append(self, id_web: int, tid_chat: int) -> bool:
        '''Добавляет Telegram ID чата в список привязанных к паутине чатов'''
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_chats = array_append(tid_chats, %s) WHERE id_web = %s",
                (tid_chat, id_web)
            )
            await self.conn.commit()
            return True
    
        except Exception as e:
            print(f"error: database: web_chats_append(): {e}")
            await self.conn.rollback()
            return False

    async def web_tid_chats_rm(self, id_web: int, tid_chat: int) -> bool:
        '''Убирает Telegram ID чата из списка привязанных к паутине чатов'''
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_chats = array_remove(tid_chats, %s) WHERE id_web = %s",
                (tid_chat, id_web)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: web_chats_rm(): {e}")
            await self.conn.rollback()
            return False

    async def rmweb(self, id_web: int) -> bool:
        '''Удаляет паутину'''
        try:
            await self.cur.execute(
                "DELETE FROM webs WHERE id_web = %s",
                (id_web,)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: rmweb(): {e}")
            await self.conn.rollback()
            return False


    async def mkusername(self, tid: int, username: str = None) -> bool:
        '''Записывает в таблицу usernames @юзернейм пользователя. Если запись уже есть - обновляет'''
        try:
            await self.cur.execute(
                "INSERT INTO usernames (tid, username) VALUES (%s, %s) ON CONFLICT (tid) DO UPDATE SET username = EXCLUDED.username",
                (tid, username)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: mkusername(): {e}")
            await self.conn.rollback()
            return False

    async def get_tid(self, username: str) -> int:
        '''Возвращает Telegram- ID по @юзернейм'''
        try:
            await self.cur.execute(
                "SELECT tid FROM usernames WHERE username = %s",
                (username,)
            )
            user = await self.cur.fetchone()
            return user['tid'] if user else None

        except Exception as e:
            print(f"error: database: get_tid(): {e}")
            return None

    async def get_username(self, tid: int) -> str:
        '''Возвращает Telegram- @юзернейм по ID'''
        try:
            await self.cur.execute(
                "SELECT username FROM usernames WHERE tid = %s",
                (tid,)
            )
            user = await self.cur.fetchone()
            return user['username'] if user else None

        except Exception as e:
            print(f"error: database: get_username(): {e}")
            return None


    async def mkchat(self, tid_chat: int, id_web: int, tid_owner: int, username: str = None) -> bool:
        try:
            await self.cur.execute(
                "INSERT INTO chats (tid_chat, id_web, tid_owner) VALUES (%s, %s, %s) RETURNING *",
                (tid_chat, id_web, tid_owner)
            )
            chat = await self.cur.fetchone()

            await self.web_tid_chats_append(id_web, tid_chat)
            await self.mkusername(tid_chat, username)
            await self.conn.commit()
            return chat

        except Exception as e:
            print(f"error: database: mkchat(): {e}")
            await self.conn.rollback()
            return None

    async def chat_edit_tid_owner(self, tid_chat: int, new_tid_owner: int) -> bool:
        try:
            await self.cur.execute(
                "UPDATE chats SET tid_owner = %s WHERE tid_chat = %s",
                (new_tid_owner, tid_chat)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: chat_edit_tid_owner(): {e}")
            await self.conn.rollback()
            return False

    async def rmchat(self, tid_chat: int, id_web: int) -> bool:
        try:
            await self.cur.execute(
                "DELETE FROM chats WHERE tid_chat = %s",
                (tid_chat,)
            )
            await self.web_tid_chats_rm(id_web, tid_chat)
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: databasey: rmchat(): {e}")
            await self.conn.rollback()
            return False


    async def mkadmin(self, tid_admin: int, id_web: int, post: str, username: str = None) -> dict:
        '''Создаёт администратора в таблице admins'''
        try:
            await self.cur(
                "INSERT INTO admins (VALUES tid_admin, id_web, post) VALUES (%s, %s, %s) RETURNING *",
                (tid_admin, id_web, post)
            )
            admin = await self.cur.fetchone()

            await self.mkusername(tid_admin, username)
            await self.conn.commit()
            return admin

        except Exception as e:
            print(f"error: database: mkadmin(): {e}")
            await self.conn.rollback()
            return None

    async def admin_get(self, id_web: int, tid_admin: int) -> str:
        '''Возвращает полную информацию об админе из конкретной сетки, по  его Telegram ID'''
        try:
            await self.cur.execute(
                "SELECT * FROM admins WHERE id_web = %s AND tid_admin = %s",
                (id_web, tid_admin)
            )
            admin = await self.cur.fetchone()
            return admin

        except Exception as e:
            print(f"error: database: admin_get(): {e}")
            return None

    async def admin_edit_post(self, tid_admin: int, id_web: int, new_post: str) -> bool:
        if new_post not in ('owner', 'helper', 'admin', 'moder'):
            raise ValueError("Unknows post type")

        try:
            await self.cur.execute(
                "UPDATE admins SET post = %s WHERE id_web = %s AND tid_admin = %s",
                (new_post, id_web, tid_admin)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database: admin_edit_post(): {e}")
            await self.conn.rollback()
            return False

    async def rmadmin(self, tid_admin: int, id_web: int) -> bool:
        try:
            await self.cur.execute(
                "DELETE FROM admins WHERE id_web = %s AND tid_admin = %s",
                (id_web, tid_admin)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: databasey: rmadmin(): {e}")
            await self.conn.rollback()
            return False
