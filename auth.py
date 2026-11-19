"""Password + token security utilities (bcrypt + JWT w/ HTTP-only cookie)."""
from __future__ import annotations

import os
import sys
import secrets
import uuid
from pathlib import Path

from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext

# Ensure the project root is importable whether run as a package or standalone
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from settings import BASE_DIR, DATABASE_URL, UPLOAD_DIR, MEDIA_URL

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

# Stable admin access secret: persisted in a file so login tokens survive restarts.
# Falls back to a per-process random secret if the file is missing.
_ACCESS_SECRET_FILE = Path(
    os.environ.get("ACCESS_SECRET_FILE", "/home/bongani/.car-dealership/access_secret.txt")
)
ACCESS_SECRET = (
    os.environ.get("ACCESS_SECRET")
    or (_ACCESS_SECRET_FILE.read_text().strip() if _ACCESS_SECRET_FILE.exists() else None)
    or secrets.token_urlsafe(64)
)
ACCESS_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, email: str, full_name: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "full_name": full_name,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, ACCESS_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, ACCESS_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


def generate_verification_token(email: str) -> str:
    """One-time token used for password reset / email verification."""
    return secrets.token_urlsafe(32)
