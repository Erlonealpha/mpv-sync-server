from contextlib import asynccontextmanager
from src.database import Session, get_async_engine


class Program:
    def __init__(self, engine = get_async_engine()):
        self._engine = engine
    
    @asynccontextmanager
    async def session_context(self):
        async with Session(self._engine) as session:
            yield session

program = None

def init_program():
    global program
    if program is None:
        program = Program()