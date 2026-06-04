from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.Users import Users
from dependencies.auth import get_current_user
from schemas.user_schema import UpdateProfile
from crud.user import UserService
from database.session_manager import get_async_db

router = APIRouter(prefix="/user",tags=["User Management"])

@router.get("/profile")
async def get_user_profile(
    user_id: int,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
    ):
    service = UserService(db)
    return await service.get_profile_details(current_user, user_id)

@router.put("/profile")
async def update_user_profile(
    user_id: int,
    updated_data: UpdateProfile,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
    ):
    service = UserService(db)
    return await service.update_profile_details(user_id, updated_data, current_user)