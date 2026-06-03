from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.src.core import config
from backend.src.database.session_manager import get_async_db
import logging
from backend.src.models import Users
from backend.src.utils import jwt

security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_user(
    credentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            config.jwt_secret_key,
            algorithms=[config.algorithm]
        )
        user_id = int(payload["sub"])
        result = await db.execute(
            select(Users).where(
                Users.id == user_id
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

def decode_token(token: str):
    return jwt.decode(
        token,
        config.jwt_secret_key,
        algorithms=[config.algorithm]
    )