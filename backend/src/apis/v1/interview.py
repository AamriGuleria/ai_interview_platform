from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile
from crud.interview import InterviewService
from database.session_manager import get_async_db
from dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/interview",tags=["Interview Management"])


@router.post("/interview_info")
async def fetch_interview_context(
    skills: List[str] = Form(...),
    experience: int = Form(...),
    target_role: str = Form(...),
    resume: UploadFile = File(...),
    app_session_id: str = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = InterviewService(db)
    result = service.register_interview(skills, experience, target_role, resume, current_user, app_session_id, db)
    return result