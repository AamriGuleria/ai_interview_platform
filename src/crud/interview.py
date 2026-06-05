from datetime import datetime
from typing import List
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from models.Interview import Interview
from core.config import config
from services.minio_client import MinioClient
from schemas.user_schema import UpdateProfile
from models.Users import Users
from fastapi import BackgroundTasks, File, Form, HTTPException, UploadFile
from background_tasks.resume_text_extraction import extract_resume_context

logger = logging.getLogger(__name__)

class InterviewService:

    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_interview(
        self,
        skills: List[str],
        experience: int,
        target_role: str,
        resume: UploadFile,
        current_user: Users,
        app_session_id: int,
        background_tasks: BackgroundTasks
    ):
        try:
            # Upload the file to minio
            now = datetime.utcnow()
            file_location = (
                f"resumes/{current_user.id}/"
                f"{uuid4()}_{resume.filename}"
            )
            minio_client = MinioClient()
            minio_client.initialize_bucket(config.bucket_name)
            minio_client.upload_file(
                config.bucket_name,
                file_location,
                resume.file
            )
            # Generate interview context using LLM
            # Make entry for the Interview model

            interview = Interview(
                user_id=current_user.id,
                target_role=target_role,
                app_session_id=app_session_id,
                experience=experience,
                skills=skills,
                resume_url=file_location,
                started_at=now,
                status="pending"
            )
            self.db.add(interview)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(interview)
            background_tasks.add_task(
                extract_resume_context,
                interview.id
            )
            return interview
        except Exception as e:
            logger.error(
                f"Failed to register interview due to:  {e}"
            )
            raise