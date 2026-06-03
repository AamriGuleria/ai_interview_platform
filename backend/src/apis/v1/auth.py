from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user
from crud.auth import AuthService
from database.session_manager import get_async_db, get_db
from models import Users
from utils.security import hash_password
from schemas.auth_schema import LoginUser, RegiserUser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    # dependencies=Depends(get_db)
    )

@router.post("/register")
async def register_user(
    user: RegiserUser,
    db: AsyncSession = Depends(get_async_db)
    ):
    service = AuthService(db)
    return await service.register_user(user)

@router.post("/login")
async def login_user(
    user: LoginUser,
    # current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
    ):
    service = AuthService(db)
    return await service.login_user(user)


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str,
    # current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
    ):
    service = AuthService(db)
    return await service.refresh_access_token(refresh_token)

@router.post("/logout")
async def logout_session(
    refresh_token: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
    ):
    service = AuthService(db)
    return await service.logout_session(refresh_token, current_user)