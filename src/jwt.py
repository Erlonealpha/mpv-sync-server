from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional


def generate_key():
    import secrets
    return secrets.token_urlsafe(32)

SECRET_KEY = generate_key()
pwd_algorithm = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=1440)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=pwd_algorithm)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, float]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[pwd_algorithm])
        username = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

def verify_token(token: str):
    token_data = decode_token(token)
    if token_data is None:
        return None
    expires: float = token_data.get("exp")
    if datetime.now() >= datetime.fromtimestamp(expires):
        raise JWTError("Token expired")
    return token_data

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)