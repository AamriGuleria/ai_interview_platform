from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional
import logging
from dependencies.auth import decode_token
from core import config
from models.Users import AppSession, Users
from schemas.auth_schema import LoginUser, RegiserUser, UserRole
from utils.jwt import create_access_token, create_refresh_token
from utils.security import hash_password, verify_password
from fastapi import HTTPException
from jose import ExpiredSignatureError, JWTError, jwt

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
                password_hash=hash_password(
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
                    "sub": str(registered_user.id),
                    "email": registered_user.email,
                    "role": registered_user.role.value
                }
            )
            refresh_token, exp = create_refresh_token(
                {
                    "sub": str(registered_user.id)
                }
            )
            refresh_hash = hash_password(
                refresh_token
            )
            session = AppSession(
                user_id=registered_user.id,
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

    async def refresh_access_token(self, refresh_token: str)-> Dict[str, Any]:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            user_id = int(
                payload["sub"]
            )
            result = await self.db.execute(
                select(Users)
                .where(
                    Users.id == user_id,
                    Users.is_active == True
                )
            )
            valid_user = result.scalar_one_or_none()

            if not valid_user:
                raise HTTPException(
                    status_code=401,
                    detail="User Not Found"
                )
            # Find Valid Session to exist
            session_result = await self.db.execute(
                select(AppSession)
                .where(
                    AppSession.user_id == user_id,
                    AppSession.is_revoked.is_(False)
                )
            )

            sessions = session_result.scalars().all()
            valid_session = None

            for session in sessions:
                if verify_password(
                    refresh_token,
                    session.refresh_token_hash
                ):
                    valid_session = session
                    break
            if not valid_session:
                raise HTTPException(
                    status_code=401,
                    detail="Session not found"
                )
            if valid_session.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=401,
                    detail="Refresh token expired"
                )
            access_token = create_access_token(
                {
                    "sub": str(valid_user.id),
                    "email": valid_user.email,
                    "role": valid_user.role.value
                })
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Refresh token expired"
            )

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        except Exception as e:
            logger.exception("Unexpected error")
            raise

    async def logout_session(
        self, refresh_token: str, current_user: Users
    ):
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            user_id = int(payload["sub"])
            if user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Token does not belong to current user"
                )
            result = await self.db.execute(
                select(AppSession)
                .where(
                    AppSession.user_id == user_id,
                    # AppSession.refresh_token_hash == hash_password(refresh_token),
                    AppSession.is_revoked.is_(False)
                )
            )
            sessions = result.scalars().all()
            session_to_revoke = None
            for session in sessions:
                if verify_password(
                    refresh_token,
                    session.refresh_token_hash
                ):
                    session_to_revoke = session
                    break
            if not session_to_revoke:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found"
                )

            session_to_revoke.is_revoked = True
            return {
                "message": "Successfully logged out"
            }

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise
