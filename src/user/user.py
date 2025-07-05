from dataclasses import dataclass
from typing import Optional
from src.database import UserModel, UserIDModel, Session
from src.prog import program
from src.jwt import get_password_hash

class UserException(Exception):
    '''Base class for user exceptions'''

class UserAlreadyExists(UserException):
    '''Raised when a user with the same name already exists'''

@dataclass
class User:
    id: int
    name: str
    password_hash: str
    hash_algorithm: str = "sha256"

    @classmethod
    def from_model(cls, model: UserModel):
        return cls(
            id=model.user_id,
            name=model.username,
            password_hash=model.password_hash,
            hash_algorithm=model.hash_algorithm
        )

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

USER_ID_BASE = 1000_000_000

async def generate_user_id(session: Session):
    user_id_e = await session.user_id.get_by(unique=True, id=0)
    if user_id_e is None:
        user_id_m = UserIDModel(
            id=0,
            latest_id=0
        )
    else:
        user_id_m = user_id_e.sqlmodel_update(latest_id=user_id_e.latest_id + 1)
    
    session.add(user_id_m)
    await session.commit()
    user_id_raw = user_id_m.latest_id
    if user_id_raw < USER_ID_BASE:
        user_id = user_id_raw + USER_ID_BASE
    else:
        user_id = user_id_raw
    return user_id


async def create_user(name: str, password: str):
    async with program.session_context() as session:
        user = session.user.get_by(name=name)
        if user is not None:
            raise UserAlreadyExists(f"User {name} already exists")
        user_id = await generate_user_id(session)
        user = UserModel(
            name=name, 
            password_hash=get_password_hash(password),
            user_id=user_id
        )
        session.add(user)
        await session.commit()
        return User.from_model(user)

async def get_user_by_name(name: str) -> Optional[User]:
    async with program.session_context() as session:
        user = session.user.get_by(name=name)
        if user is None:
            return None
        return User.from_model(user)

async def get_user_by_id(user_id: int) -> Optional[User]:
    async with program.session_context() as session:
        user = session.user.get_by(user_id=user_id)
        if user is None:
            return None
        return User.from_model(user)

