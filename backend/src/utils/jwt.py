from jose import jwt
import logging
from datetime import datetime, timedelta
from core.config import config

logger = logging.getLogger(__name__)

SECRET_KEY = config.jwt_secret_key
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_IN_MINUTES = 15
REFRESH_TOKEN_EXPIRE_IN_DAYS = 30

def create_access_token(data: dict):
    try:
        payload = data.copy()
        payload["exp"] = (
            datetime.utcnow()
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_IN_MINUTES)
        )
        payload["type"] = "access"
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
    except Exception as e:
        logger.error(f"Failed to create access token due to {e}")
        raise

def create_refresh_token(data: dict):

    payload = data.copy()
    expiry = (
        datetime.utcnow()
        + timedelta(days=REFRESH_TOKEN_EXPIRE_IN_DAYS)
    )
    payload["type"] = "refresh"
    payload["exp"] = expiry

    return (
        jwt.encode(
            payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        ),
        expiry
    )

def decode_token(token: str):
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )