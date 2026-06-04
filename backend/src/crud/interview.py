from datetime import datetime
from typing import List
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from core.config import config
from services.minio_client import MinioClient
from schemas.user_schema import UpdateProfile
from models.Users import Users
from fastapi import File, Form, HTTPException, UploadFile

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
        db: AsyncSession
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
            pass
        except Exception as e:
            logger.error(
                f"Failed to register interview due to:  {e}"
            )
            raise