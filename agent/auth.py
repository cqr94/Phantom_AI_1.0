
import secrets

import bcrypt
import pyotp
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = "your-secret-key"   # move to env var / settings
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    # bcrypt wants bytes; truncate to 72 bytes (bcrypt hard limit)
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def get_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)

def create_refresh_token():
    return secrets.token_urlsafe(64)

def decode_token(token: str):

    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except JWTError:
        return None