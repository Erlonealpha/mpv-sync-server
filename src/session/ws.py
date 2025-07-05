from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketState
from src.jwt import JWTError, verify_token
from src.user import User, get_user_by_name
from src.log import logger

from .room import get_room_manager

router = APIRouter(prefix="/ws")

connected_clients = set()

g_room_manager = get_room_manager()


@router.websocket("/master/{room_id}")
async def websocket_endpoint_master(websocket: WebSocket, room_id: str):
    accepted = False
    try:
        decode = verify_token(websocket.headers.get("Authorization"))
    except JWTError:
        await websocket.close(code=4001, reason="Unauthorized token expired")
        return
    if decode is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    user = await get_user_by_name(decode.get("sub"))
    try:
        await websocket.accept()
        accepted = True
        connected_clients.add(websocket)
        if (room := g_room_manager.get_room(room_id)) is None:
            await websocket.close(code=4004, reason="Room not found")
            return
        room.add_member(user)
        
        while True:
            data = await websocket.receive_json()
            room.recv_master(data)
    except Exception as e:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1002, reason=f"Closed by server with err: {e}")
    finally:
        if accepted:
            connected_clients.remove(websocket)
            room.remove_member(user)
            await room.close()

@router.websocket("/member/{room_id}")
async def websocket_endpoint_member(websocket: WebSocket, room_id: str):
    accepted = False
    try:
        decode = verify_token(websocket.headers.get("Authorization"))
    except JWTError:
        await websocket.close(code=4001, reason="Unauthorized token expired")
        return
    if decode is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    user = await get_user_by_name(decode.get("sub"))
    try:
        await websocket.accept()
        accepted = True
        connected_clients.add(websocket)
        if (room := g_room_manager.get_room(room_id)) is None:
            await websocket.close(code=4004, reason="Room not found")
            return
        room.add_member(user)
        room.add_connected_socket(user.id, websocket)
        while True:
            data = await websocket.receive_json()
            await room.recv_member(data)
    except Exception as e:
        logger.error(f"Error in websocket_endpoint_member: {e}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1002, reason=f"Closed by server with err: {e}")
    finally:
        if accepted:
            connected_clients.remove(websocket)
            room.remove_member(user)
            room.remove_connected_socket(user.id)

test_mas_user = User(1001, "TEST_MASTER", "xxx")
mas_connected = False
test_room = g_room_manager.create_room(test_mas_user, "TEST_ROOM")
test_mem_id_start = 1002

# Test endpoints
# Future: Make this to /ws/master/public
@router.websocket("/test_master")
async def websocket_endpoint_test_master(websocket: WebSocket):
    global mas_connected
    accepted = False
    if mas_connected:
        await websocket.close(code=4009, reason="Master already connected")
        return
    await websocket.accept()
    accepted = True
    mas_connected = True
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await test_room.recv_master(data)
            # logger.info(f"Received data from {test_mas_user.name}: {data}")
    except Exception as e:
        logger.error(f"Error in websocket_endpoint_test_master: {e}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1002, reason=f"Closed by server with err: {e}")
    finally:
        if accepted:
            mas_connected = False
            connected_clients.remove(websocket)

@router.websocket("/test_member")
async def websocket_endpoint_test_member(websocket: WebSocket):
    global test_mem_id_start
    accepted = False
    await websocket.accept()
    _id = test_mem_id_start
    test_mem_id_start += 1
    accepted = True
    test_mem_user = User(_id, f"TEST_MEMBER_{_id}", "xxx")
    connected_clients.add(websocket)
    test_room.add_member(test_mem_user)
    test_room.add_connected_socket(test_mem_user.id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # logger.info(f"Received data from {test_mem_user.name}: {data}")
            await test_room.recv_member(test_mem_user.id, data)
    except Exception as e:
        logger.exception(f"Error in websocket_endpoint_test_member: {e}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1002, reason=f"Closed by server with err: {e}")
    finally:
        if accepted:
            logger.info(f"Remove {test_mem_user.name} from room {test_room.uuid}")
            connected_clients.remove(websocket)
            test_room.remove_member(test_mem_user)
            test_room.remove_connected_socket(test_mem_user.id)
