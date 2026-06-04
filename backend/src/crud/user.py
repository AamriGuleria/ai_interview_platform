from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from schemas.user_schema import UpdateProfile
from models.Users import Users
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_details(
        self,
        current_user: Users,
        user_id: int
    ):
        try:
            if current_user.id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Not Authorized"
                )
            result = await self.db.execute(
                select(Users).where(
                    Users.id == user_id
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError(
                    "User not found"
                )
            return {
                "email": user.email,
                "role": user.role,
                "phone_number": user.phone_number,
                "resume_url": user.resume_url,
                "skills": user.skills,
                "experience": user.experience
            }
        except Exception as e:
            logger.error(
                f"Failed to get profile details due to:  {e}"
            )
            raise

    async def update_profile_details(
            self,
            user_id: int,
            update_data: UpdateProfile,
            current_user: Users,
    ):
        try:
            if current_user.id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Not Authorized"
                )
            result = await self.db.execute(select(Users).where(Users.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            for key, value in update_data.model_dump(exclude_unset=True).items():
                setattr(user, key, value)
            await self.db.flush()
            return {
                "email": user.email,
                "role": user.role,
                "phone_number": user.phone_number,
                "resume_url": user.resume_url,
                "skills": user.skills,
                "experience": user.experience
            }
        except Exception as e:
            logger.error(
                f"Failed to update profile details due to: {e}"
            )
            raise