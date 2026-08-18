from datetime import datetime, timezone, timedelta
from authlib.jose import jwt, JoseError
from passlib.context import CryptContext
from app.shared.core.config import JWT_SECRET, JWT_ACCESS_TOKEN_EXPIRE, JWT_REFRESH_TOKEN_EXPIRE, ALGORITHM

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain:str, hashed:str)->bool:
    return pwd_context.verify(plain, hashed)

def create_token(sub:str, expires_delta:timedelta, token_type:str)->str:
    now = datetime.now(timezone.utc)
    header = {"alg": ALGORITHM}
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(header, payload, JWT_SECRET).decode("utf-8")

def create_access_token(user_id:str)->str:
    return create_token(user_id, timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE), "access")

def create_refresh_token(user_id:str)->str:
    return create_token(user_id, timedelta(hours=JWT_REFRESH_TOKEN_EXPIRE), "refresh")

def decode_token(token:str)->dict:
    try:
        claims = jwt.decode(token, JWT_SECRET)
        claims.validate()
        return claims
    except JoseError:
        raise ValueError("Invalid or expired token")
