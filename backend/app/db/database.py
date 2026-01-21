from databases import Database
from ..config import DATABASE_URL

database = Database(DATABASE_URL) if DATABASE_URL else None


async def connect_db():
    if database:
        await database.connect()


async def disconnect_db():
    if database and database.is_connected:
        await database.disconnect()
