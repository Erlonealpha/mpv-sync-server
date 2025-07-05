from typing import Optional, Union, TypeVar, Generic, Type, TYPE_CHECKING
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar

T = TypeVar("T")

if TYPE_CHECKING:
    from .session import Session

class BaseSessionHandler(Generic[T]):
    __model_class__: Type[T] = None
    if TYPE_CHECKING:
        session: Session

    def __new__(cls):
        if not cls.__model_class__:
            raise NotImplementedError("Model class not defined for this handler")

    def __init__(self, session):
        self.session = session
    
    async def get_by(self, fetch_all: bool = False, unique: bool = False, **filters) -> Optional[Union[T, list[T]]]:
        if unique and not fetch_all:
            raise ValueError("Fetch all must be True when unique is True")
        statement = select(self.__model_class__).filter_by(**filters)
        return await self._fetch_all(statement, unique) if fetch_all else await self._fetch_one(statement)

    async def _fetch_one(self, statement: SelectOfScalar[T]) -> Optional[T]:
        results = await self.session.execute(statement)
        return results.first()
    
    async def _fetch_all(self, statement: SelectOfScalar[T], unique = False) -> list[T]:
        results = await self.session.execute(statement)
        if unique:
            results = results.unique()
        return results.all()