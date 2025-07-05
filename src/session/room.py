from json import dumps
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Union
from fastapi import WebSocket, APIRouter, Response, HTTPException
from uuid import uuid4
from src.user import User, get_user_by_name
from src.jwt import JWTError, verify_token
from src.log import logger

router = APIRouter(prefix="/room")

def get_system_time():
    # Confirmed that UTC time is used
    return datetime.now().timestamp()

class Unset:
    def __str__(self):
        return "Unset"
    
    def __bool__(self):
        return False
    
    def __json__(self):
        return "Unset"
    
    def __repr__(self):
        return "Unset"
    
    def __copy__(self):
        return self
    
    def __deepcopy__(self, memo):
        return self

_Unset = Unset()

def or_none(val):
    if val is _Unset:
        return None
    return val

class _MessageTypes:
    if TYPE_CHECKING:
        command: Literal[
            "state", "action", "desc",
            "req",
        ]
        name: Literal[
            "stop",
            "enabled",
            "pause", "paused-for-cache", "volume", "ao-mute", "mute", "speed", "sub-delay", "audio-delay",
            "seek",
            "pos",
            "master",
            "slave"
        ]
        value: Union[str, int, float, bool]
        extra: "MessageWrap"

        filename: str
        filesize: int
        duration: int
        pos: float
        
        timestamp: float

class MessageWrap(_MessageTypes):
    def __init__(self, message: dict):
        self._message = message
    
    def to_dict(self):
        return self._message
    
    def __getattr__(self, name):
        try:
            val = self._message[name]
            if isinstance(val, dict):
                return MessageWrap(val)
            else:
                return val
        except KeyError:
            return _Unset

class Description:
    filename: str = _Unset
    filesize: int = _Unset
    duration: int = _Unset
    start_pos: float = _Unset

    def to_dict(self):
        return {
            "filename": {"value": or_none(self.filename) , "timestamp_server": get_system_time(), "req": True},
            "filesize": {"value": or_none(self.filesize) , "timestamp_server": get_system_time(), "req": True},
            "duration": {"value": or_none(self.duration) , "timestamp_server": get_system_time(), "req": True},
            "pos":      {"value": or_none(self.start_pos), "timestamp_server": get_system_time(), "req": True}
        }
    
    def update(self, message: MessageWrap) -> None:
        self.filename = message.extra.filename
        self.filesize = message.extra.filesize
        self.duration = message.extra.duration
        self.start_pos = message.extra.pos

class State:
    paused: bool = _Unset
    position: float = _Unset
    volume: int = _Unset
    ao_mute: bool = _Unset
    mute: bool = _Unset
    speed: int = _Unset

    sub_delay: int = _Unset
    audio_delay: int = _Unset

    _paused_timestamp: float = _Unset
    _position_timestamp: float = _Unset
    _volume_timestamp: float = _Unset
    _ao_mute_timestamp: float = _Unset
    _mute_timestamp: float = _Unset
    _speed_timestamp: float = _Unset
    _sub_delay_timestamp: float = _Unset
    _audio_delay_timestamp: float = _Unset

    def to_dict(self):
        return {
            "pause":        {"value": or_none(self.paused),      "timestamp_server": get_system_time(), "timestamp": or_none(self._paused_timestamp),        "req": True},
            "pos":          {"value": or_none(self.position),    "timestamp_server": get_system_time(), "timestamp": or_none(self._position_timestamp),      "req": True},
            "volume":       {"value": or_none(self.volume),      "timestamp_server": get_system_time(), "timestamp": or_none(self._volume_timestamp),        "req": True},
            "ao_mute":      {"value": or_none(self.ao_mute),     "timestamp_server": get_system_time(), "timestamp": or_none(self._ao_mute_timestamp),       "req": True},
            "mute":         {"value": or_none(self.mute),        "timestamp_server": get_system_time(), "timestamp": or_none(self._mute_timestamp),          "req": True},
            "speed":        {"value": or_none(self.speed),       "timestamp_server": get_system_time(), "timestamp": or_none(self._speed_timestamp),         "req": True},
            "sub_delay":    {"value": or_none(self.sub_delay),   "timestamp_server": get_system_time(), "timestamp": or_none(self._sub_delay_timestamp),     "req": True},
            "audio_delay":  {"value": or_none(self.audio_delay), "timestamp_server": get_system_time(), "timestamp": or_none(self._audio_delay_timestamp),   "req": True}
        }

    def update(self, message: MessageWrap) -> None:
        def type_check(val, tp):
            if not isinstance(val, tp):
                try:
                    if tp in [int, float]:
                        # string to int or float
                        val = tp(val)
                        return val
                except Exception:
                    pass
                raise TypeError(f"Expected {tp}, got {type(val)}")
            return val
        try:
            if message.name == _Unset:
                logger.warning(f"Invalid received message: {message}")
                return False
            if message.command == "state":
                if message.name in ["pause", "paused-for-cache"]:
                    val = type_check(message.value, bool)
                    self._paused_timestamp = message.timestamp
                    if self.paused == val:
                        return True
                    self.paused = val
                elif message.name == "volume":
                    val = type_check(message.value, int)
                    self._volume_timestamp = message.timestamp
                    if self.volume == val:
                        return False
                    self.volume = val
                elif message.name == "mute":
                    val = type_check(message.value, bool)
                    self._mute_timestamp = message.timestamp
                    if self.mute == val:
                        return False
                    self.mute = val
                elif message.name == "ao-mute":
                    val = type_check(message.value, bool)
                    self._ao_mute_timestamp = message.timestamp
                    if self.ao_mute == val:
                        return False
                    self.ao_mute = val
                elif message.name == "speed":
                    val = type_check(message.value, int)
                    self._speed_timestamp = message.timestamp
                    if self.speed == val:
                        return False
                    self.speed = val
                elif message.name == "sub-delay":
                    val = type_check(message.value, int)
                    self._sub_delay_timestamp = message.timestamp
                    if self.sub_delay == val:
                        return False
                    self.sub_delay = val
                elif message.name == "audio-delay":
                    val = type_check(message.value, int)
                    self._audio_delay_timestamp = message.timestamp
                    if self.audio_delay == val:
                        return False
                    self.audio_delay = val
                elif message.name == "pos":
                    val = type_check(message.value, float)
                    self._position_timestamp = message.timestamp
                    if self.position == val:
                        return True
                    self.position = val
            elif message.command == "action":
                if message.name == "seek":
                    val = type_check(message.value, float)
                    self._seek_timestamp = message.timestamp
                    if self.position == val:
                        return True
                    self.position = val
            return True
        except TypeError as e:
            logger.warning(f"Invalid received message: {e}")
            return False

class Room:
    _room_state: str
    uuid: str
    name: str
    master: User
    members: list
    state: State
    description: Description

    def __init__(self, master: User, name: str = "New Room") -> None:
        self.uuid = uuid4()
        self.name = name
        self.master = master
        self.members = [master]
        self.connected_users: dict[int, WebSocket] = {}
        self.state = State()
        self.description = Description()

    def add_member(self, member: User) -> None:
        self.members.append(member)
    
    def remove_member(self, member: User) -> None:
        if member.id == self.master.id:
            raise ValueError("Cannot remove master from room")
        self.members.remove(member)
    
    def add_connected_socket(self, user_id, connect: WebSocket):
        self.connected_users[user_id] = connect
    
    def remove_connected_socket(self, user_id):
        self.connected_users.pop(user_id, None)

    async def close(self):
        ...

    async def recv_master(self, message: dict):
        message_w = MessageWrap(message)
        if message_w.command == "desc":
            self.description.update(message_w)
        else:
            if self.state.update(message_w):
                await self.notify_all_users(message_w)
    
    async def recv_member(self, user_id: int, message: dict):
        message_w = MessageWrap(message)
        if message_w.command == "req":
            if message_w.name == "desc":
                extra = self.description.to_dict()
            elif message_w.name == "state":
                extra = self.state.to_dict()
            else:
                logger.warning(f"Invalid received message with unknown req name: {message_w.name} from {user_id}")
                return
            await self.send_to(user_id, {"command": "req", "extra": extra})
        elif message_w.command == "state":
            pass
        else:
            logger.warning(f"Invalid received message with unknown command: {message_w.command} from {user_id}")

    @staticmethod
    def pack_message(message: MessageWrap):
        return dumps({
            "command": message.command,
            "name": message.name.replace("-", "_"),
            "value": message.value,
            "extra": message.extra.to_dict()
        })

    async def send_to(self, user_id: int, message: Union[dict, MessageWrap]) -> None:
        socket = self.connected_users.get(user_id)
        if socket is not None:
            if isinstance(message, MessageWrap):
                await socket.send_text(self.pack_message(message))
            else:
                await socket.send_json(message)
    
    async def notify_all_users(self, message: MessageWrap) -> None:
        for socket in self.connected_users.values():
            # logger.info(f"Sending message to {socket.client.host}")
            await socket.send_text(self.pack_message(message))

class RoomManager:
    def __init__(self) -> None:
        self.rooms = {}

    def create_room(self, master: User, name: str = "New Room") -> Room:
        room = Room(master, name)
        self.rooms[room.uuid] = room
        return room

    def get_room(self, uuid: str) -> Room:
        return self.rooms[uuid]

    def delete_room(self, uuid: str) -> None:
        del self.rooms[uuid]

_g_group_manager = RoomManager()

def get_room_manager() -> RoomManager:
    return _g_group_manager

@router.post("/create")
async def create_room(response: Response):
    try:
        decode = verify_token(response.headers.get("Authorization"))
    except JWTError:
        return HTTPException(code=401, reason="Unauthorized token expired")
    if decode is None:
        return HTTPException(code=401, reason="Unauthorized")
    
    user = await get_user_by_name(decode["sub"])
    
    _g_group_manager.create_room(user)
