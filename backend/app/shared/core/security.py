from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
from authlib.jose import jwt, JoseError
from app.shared.core.config import JWT_SECRET, JWT_ACCESS_TOKEN_EXPIRE, JWT_REFRESH_TOKEN_EXPIRE, ALGORITHM


# In-memory token blocklist (replace with Redis in production)
_token_blocklist: set[str] = set()


def block_token(jti: str) -> None:
    """Add a token's JTI to the blocklist."""
    _token_blocklist.add(jti)


def is_token_blocked(jti: str) -> bool:
    """Check if a token's JTI is in the blocklist."""
    return jti in _token_blocklist


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_token(sub:str, expires_delta:timedelta, token_type:str)->str:
    now = datetime.now(timezone.utc)
    header = {"alg": ALGORITHM}
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # unique token ID for revocation
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
