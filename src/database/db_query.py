from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from config import *

class Database():
    def __init__(self):
        self.conn = connect(
            host="localhost",
            database="postgres",
            port="5432",
            user="postgres",
            password="nicetea"
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    async def create_web(self, forename: str, tid_owner: int) -> dict:
        owner = await bot.get_chat(tid_owner)
        
        try:
            self.cur.execute(
                query = """INSERT INTO webs (forename, tid_owner) VALUES (%s, %s);""",
                vars  = (forename, tid_owner)
            )
            web = self.cur.fetchone()
            self.cur.execute(
                query = "INSERT INTO admins (tid_user, username, post) VALUES (%s. %s, %s)",
                vars  = (tid_owner, owner.username, "owner")
            )
            self.conn.commit()
            return web

        except Exception as e:
            print(f"error: database/db_query.py: create_web(): {e}")
            return None

    async def rename_web(self, id_web: int, new_forename: str) -> dict:
        try:
            self.cur.execute(
                query = """UPDATE webs SET forename = %s WHERE id_web = %s""",
                vars  = (new_forename, id_web)
            )
            self.conn.commit()
            return True

        except Exception as e:
            print(f"error: database/db_query.py: rename_web(): {e}")
            return False
