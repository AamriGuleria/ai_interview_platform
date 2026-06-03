from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from models.Users import AppSession, Users
from schemas.auth_schema import LoginUser, RegiserUser, UserRole
from utils.jwt import create_access_token, create_refresh_token
from utils.security import hash_password, verify_password
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        user_data: RegiserUser
    ):
        try:

            existing_user = await self.db.execute(
                select(Users).where(
                    Users.email == user_data.email
                )
            )

            if existing_user.scalar_one_or_none():
                raise ValueError(
                    "User already exists"
                )

            user = Users(
                email=user_data.email,
                password=hash_password(
                    user_data.password
                ),
                role=user_data.role
                    or UserRole.CANDIDATE
            )
            self.db.add(user)
            await self.db.flush()
            return user.id

        except Exception as e:
            logger.exception(
                f"Registration failed: {e}"
            )
            raise

    async def login_user(
        self,
        user: LoginUser
    ):
        try:
            result = await self.db.execute(
                select(Users).where(Users.email == user.email)
            )

            registered_user = result.scalar_one_or_none()
            if not registered_user:
                raise HTTPException(status_code=404, detail="User Not Registered")
            if not verify_password(user.password, registered_user.password_hash):
                raise HTTPException(status_code=401, detail="Wrong Password")
            # Access Token and Refresh Token generation
            access_token = create_access_token(
                {
                    "sub": str(user.id),
                    "email": user.email,
                    "role": user.role.value
                }
            )
            refresh_token, exp = create_refresh_token(
                {
                    "sub": str(user.id)
                }
            )
            refresh_hash = hash_password(
                refresh_token
            )
            session = AppSession(
                user_id=user.id,
                ip_address=user.ip_address,
                device=user.device,
                refresh_token_hash=refresh_hash,
                expires_at=exp
            )

            self.db.add(session)

            await self.db.flush()
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"Error occured due to {e}")
            raise