from sqlmodel import SQLModel, Field
from .base import BaseSessionHandler
from .engine import metadata as _metadata

class UserIDModel(SQLModel, table=True):
    metadata = _metadata
    id: int = Field(primary_key=True)
    latest_id: int = Field(default=0)

class UserIDSessionHandler(BaseSessionHandler[UserIDModel]):
    __model_class__ = UserIDModel