from typing import TypeVar, ClassVar, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from .engine import metadata as metadata_
from .base import BaseSessionHandler
from .user import UserSessionHandler
from .user_id import UserIDSessionHandler


SessionHandleT = TypeVar("SessionHandleT", bound=BaseSessionHandler)

class HandlerRegistryMeta(type):
    def __new__(cls, name, bases, attrs):
        annotations = attrs.get("__annotations__", {})
        if "__handlers_map__" not in attrs:
            attrs["__handlers_map__"] = {}
        for k, v in annotations.items():
            if k.startswith("_"):
                continue
            if issubclass(v, BaseSessionHandler):
                attrs["__handlers_map__"][k] = v
        return super().__new__(cls, name, bases, attrs)

class InitBase:
    __handlers_map__: ClassVar[dict[str, Type[SessionHandleT]]]
    def init(self, include_handlers):
        if include_handlers is None:
            include_handlers = tuple(self.__handlers_map__.values())
        
        for name, handler in (
                    (name, handler) for name, handler in self.__handlers_map__.items() 
                        if handler in include_handlers
                ):
            setattr(self, name, handler(self))

class HandlerBind(InitBase, metaclass=HandlerRegistryMeta):
    __handlers_map__: ClassVar[dict[str, Type[SessionHandleT]]]
    
    user: UserSessionHandler
    user_id: UserIDSessionHandler


class Session(AsyncSession, HandlerBind):
    def __new__(cls, *args, **kwargs):
        setattr(cls, "__handlers_map__", HandlerBind.__handlers_map__)
        return super().__new__(cls)
    
    def __init__(
        self, 
        engine: AsyncEngine, 
        include_handlers: Optional[tuple[Type[SessionHandleT]]] = None
    ):
        self._engine = engine
        super().__init__(engine)
        self.init(include_handlers)
    
    async def create_all(self, metadata = None):
        if metadata is None:
            metadata = metadata_
        async with self._engine.begin() as conn:
            conn.run_sync(metadata.create_all())
    
    async def drop_all(self, metadata = None):
        if metadata is None:
            metadata = metadata_
        async with self._engine.begin() as conn:
            conn.run_sync(metadata.drop_all())