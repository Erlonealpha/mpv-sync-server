from sqlmodel import SQLModel, Field
from .base import BaseSessionHandler
from .engine import metadata as _metadata

class UserModel(SQLModel, table=True):
    metadata = _metadata
    id: int = Field(primary_key=True)
    user_id: int
    username: str
    password_hash: str
    hash_algorithm: str
    salt: str

class UserSessionHandler(BaseSessionHandler[UserModel]):
    __model_class__ = UserModel
