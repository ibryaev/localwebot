from psycopg import AsyncConnection
from psycopg.rows import dict_row

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

    async def web_read(self, tid_owner: int) -> dict:
        try:
            await self.cur.execute(
                "SELECT * FROM webs WHERE tid_owner = %s",
                (tid_owner,)
            )
            web = await self.cur.fetchone()
            return web

        except Exception as e:
            print(f"error: database/db_query.py: web_read(): {e}")
            return None

    async def mkweb(self, forename: str, tid_owner: int, owner_username: str) -> dict:
        '''Создаёт паутину в таблице webs, а также создателя в таблице admins'''
        try:
            await self.cur.execute(
                "INSERT INTO webs (forename, tid_owner) VALUES (%s, %s) RETURNING id_web, forename, tid_owner",
                (forename, tid_owner)
            )
            web = await self.cur.fetchone()

            await self.cur.execute(
                "INSERT INTO admins (tid_user, username, id_web, post) VALUES (%s, %s, %s, %s)",
                (tid_owner, owner_username, web['id_web'], "owner")
            )
            
            await self.conn.commit()
            return web

        except Exception as e:
            if self.conn:
                await self.conn.rollback()
            print(f"error: database/db_query.py: mkweb(): {e}")
            return None

    async def web_rename(self, id_web: int, new_forename: str) -> bool:
        '''Переименовывает паутину'''
        try:
            await self.cur.execute(
                """UPDATE webs SET forename = %s WHERE id_web = %s""",
                (new_forename, id_web)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: web_rename(): {e}")
            return False

    async def web_edit_owner(self, id_web: int, new_tid_owner: int) -> bool:
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_owner = %s WHERE id_web = %s",
                (new_tid_owner, id_web)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: web_edit_owner(): {e}")
            return False

    async def web_chats_append(self, id_web: int, tid_chat: int) -> bool:
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_chats = array_append(tid_chats, %s) WHERE id_web = %s",
                (tid_chat, id_web)
            )
            await self.conn.commit()
            return True
    
        except Exception as e:
            print(f"error: database/db_query.py: web_chats_append(): {e}")
            return False

    async def web_chats_rm(self, id_web: int, tid_chat: int) -> bool:
        try:
            await self.cur.execute(
                "UPDATE webs SET tid_chats = array_remove(tid_chats, %s) WHERE id_web = %s",
                (tid_chat, id_web)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: web_chats_rm(): {e}")
            return False

    async def rmweb(self, id_web: int) -> bool:
        try:
            await self.cur.execute("DELETE FROM webs WHERE id_web = %s", (id_web,))
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: rmweb(): {e}")
            return False

    async def mkchat(self, tid_chat: int, username: str, id_web: int, tid_owner: int) -> bool:
        try:
            await self.cur.execute(
                "INSERT INTO chats (tid_chat, username, id_web, tid_owner) VALUES (%s, %s, %s, %s)",
                (tid_chat, username, id_web, tid_owner)
            )
            await self.web_chats_append(id_web, tid_chat)
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: mkchat(): {e}")
            return False

    async def chat_update_username(self, tid_chat: int, new_username: str) -> bool:
        try:
            await self.cur.execute(
                "UPDATE chats SET username = %s WHERE tid_chat = %s",
                (new_username, tid_chat)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: chat_update_username(): {e}")
            return False

    async def chat_update_owner(self, tid_chat: int, new_tid_owner: int) -> bool:
        try:
            await self.cur.execute(
                "UPDATE chats SET tid_owner = %s WHERE tid_chat = %s",
                (new_tid_owner, tid_chat)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: chat_update_owner(): {e}")
            return False

    async def rmchat(self, tid_chat: int, id_web: int) -> bool:
        try:
            await self.cur.execute("DELETE FROM chats WHERE tid_chat = %s", (tid_chat,))
            await self.web_chats_rm(id_web, tid_chat)
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: rmchat(): {e}")
            return False

    async def res_update_until(self, id_restriction: int, new_date) -> bool:
        try:
            await self.cur.execute(
                "UPDATE restrictions SET date_until = %s WHERE id_restriction = %s",
                (new_date, id_restriction)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: res_update_until(): {e}")
            return False

    async def res_update_reason(self, id_restriction: int, new_reason: str) -> bool:
        try:
            await self.cur.execute(
                "UPDATE restrictions SET reason = %s WHERE id_restriction = %s",
                (new_reason, id_restriction)
            )
            await self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: res_update_reason(): {e}")
            return False
