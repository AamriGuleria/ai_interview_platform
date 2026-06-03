from fastapi import APIRouter, Depends
from crud.auth import AuthService
from database.session_manager import get_async_db, get_db
from models import Users
from utils.security import hash_password
from schemas.auth_schema import RegiserUser
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