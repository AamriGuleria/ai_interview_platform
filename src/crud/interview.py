from datetime import datetime
from typing import List
from uuid import uuid4
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from models.Interview import Interview, InterviewQuestion
from core.config import config
from services.minio_client import MinioClient
from models.Users import Users
from fastapi import BackgroundTasks, HTTPException, UploadFile
from background_tasks.resume_text_extraction import extract_resume_context
from services.embeddings import retrieve_questions_from_embedding
from services.llm_service import GeminiService
from background_tasks.prepare_interview import prepare_interview
from background_tasks.evaluate_answers import evaluate_answer

logger = logging.getLogger(__name__)

class InterviewService:
    PERSONALIZATION_BATCH_SIZE = 5
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
            logger.error(f"Failed to register interview due to: {e}")
            raise

    async def get_interview_questions(
        self,
        interview_id: int,
        current_user: Users,
        background_tasks: BackgroundTasks
    ):
        try:
            interview = (
                await self.db.execute(
                    select(Interview).where(
                        Interview.id == interview_id,
                        Interview.user_id == current_user.id
                    )
                )
            ).scalars().one_or_none()

            if not interview:
                raise HTTPException(status_code=404, detail="Interview not found")
            if interview.status != "ready":
                raise HTTPException(status_code=400, detail=f"Interview not ready. Current status: {interview.status}")
            if interview.resume_embedding is None:
                raise HTTPException(status_code=400, detail="Resume embedding not available")

            background_tasks.add_task(prepare_interview, interview_id)
            return {"message": "Interview preparation started", "status": "preparing"}
        
        except Exception as e:
            logger.error(f"Error fetching interview questions: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    

    async def get_next_interview_question(
        self,
        interview_id: int,
        current_user: Users
    ):
        from database.session_manager import db_manager
        interview = (
            await self.db.execute(
                select(Interview).where(
                    Interview.id == interview_id,
                    Interview.user_id == current_user.id
                )
            )
        ).scalars().one_or_none()

        if not interview:
            raise HTTPException(
                status_code=404,
                detail="Interview not found"
            )

        if interview.status != "ready":
            raise HTTPException(
                status_code=400,
                detail=f"Interview is not ready yet. Current status: {interview.status}"
            )

        with db_manager.sync_session_scope() as sync_db:
            interview_question = (
                sync_db.execute(
                    select(InterviewQuestion)
                    .where(
                        InterviewQuestion.interview_id == interview_id,
                        InterviewQuestion.user_answer.is_(None)
                    )
                    .order_by(InterviewQuestion.id)
                )
            ).scalars().first()
            if not interview_question:
                return {
                    "message": "Interview completed"
                }
            return {
                "interview_question_id": interview_question.id,
                "question_id": interview_question.question_id,
                "question_text":
                    interview_question.personalized_question
                    or interview_question.original_question,
                "assigned_at":
                    interview_question.assigned_at
            }

    async def submit_answer(
        self,
        interview_id: int,
        answer: str,
        current_user: Users,
        interview_question_id: int,
        background_tasks: BackgroundTasks
    ):
        try:
            interview_question = self.db.execute(
                select(InterviewQuestion).where(
                    InterviewQuestion.id == interview_question_id,
                    InterviewQuestion.interview_id == interview_id
                )
            )
            interview_question = interview_question.scalars().one_or_none()
            if not interview_question:
                raise HTTPException(
                    status_code=404,
                    detail="Interview question not found"
                )
            
            interview_question.user_answer = answer
            self.db.add(interview_question)
            await self.db.commit()
            await self.db.refresh(interview_question)
            background_tasks.add_task(evaluate_answer, interview_question_id)
            return {"message": "Answer submitted successfully",
                "interview_question_id": interview_question.id}
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")