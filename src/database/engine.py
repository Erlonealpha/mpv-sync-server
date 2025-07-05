from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import MetaData
from src.config import settings

a_engine_g = None
metadata = MetaData()

def get_async_engine():
    global a_engine_g
    if a_engine_g is None:
        a_engine_g = create_async_engine(f"sqlite+aiosqlite:///{settings.database_url}", echo=settings.debug)
    return a_engine_g