from datetime import timedelta
from fastapi import APIRouter, HTTPException, Cookie, status
from fastapi.responses import Response, JSONResponse
from src.user import create_user, UserAlreadyExists
from .prog import program
from .jwt import verify_token, create_access_token, verify_password

router = APIRouter(prefix="/api")

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized",
)

def get_current_user(token: str = Cookie(None)):
    if not token:
        raise UNAUTHORIZED
    payload = verify_token(token)
    if not payload:
        raise UNAUTHORIZED
    username = payload.get("sub")
    if not username:
        raise UNAUTHORIZED
    return username

async def auth_user(username: str, password: str):
    async with program.session_context() as session:
        user = await session.user.get_by(username=username)
        if user is None:
            return {"status": False, "status_code": 401, "message": "User not found"}
        if not verify_password(user.password_hash, password):
            return {"status": False, "status_code": 401, "message": "Invalid password"}
        return {"status": True, "status_code": 200, "message": "Login successful"}

@router.post("/login", response_model=dict)
async def login(response: JSONResponse):
    j = response.render()
    username = j.get("username")
    password = j.get("password")
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format")
    resp = await auth_user(username, password)
    if resp["status"]:
        token = create_access_token({"sub": username}, expires_delta=timedelta(days=7))
        response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
        return {"access_token": token, "token_type": "bearer"}
    return JSONResponse(
        status_code=resp["status_code"],
        content=resp["message"]
    )

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}

@router.post("/register", response_model=dict)
async def register(response: JSONResponse):
    j = response.render()
    username = j.get("username")
    password = j.get("password")
    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format")
    try:
        user = await create_user(username, password)
    except UserAlreadyExists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User name has already been used")
    return {"status": True, "status_code": 200, "message": "Registration successful"}
