import logging
from sqlalchemy import select
from models.Interview import Interview, InterviewStatus
from services.embeddings import create_resume_embeddings
from services.minio_client import MinioClient
from services.llm_service import LLMService
from core.config import config
from database.session_manager import db_manager
import tempfile
import fitz
import os
import re
from core.constants import RESUME_ANALYSIS_USER_PROMPT, RESUME_ANALYSIS_SYSTEM_PROMPT 

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text.strip()

def extract_text(file_path: str) -> str:
    pdf = fitz.open(file_path)
    pages = [page.get_text() for page in pdf]
    pdf.close()
    return "\n".join(pages)

def extract_resume_context(interview_id: int):
    file_name = None
    response_summary = None
    try:
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()
            if not interview:
                raise Exception("Interview not found")

            # Step 1: Download and extract resume text
            file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            file_name = file.name
            file.close()
            minio_service = MinioClient()
            minio_service.download_file(config.bucket_name, interview.resume_url, file_name)
            cleaned_text = clean_text(extract_text(file_name))
            interview.resume_text = cleaned_text
            logger.info(f"Resume text extracted for interview {interview_id}")

            gemini_service = LLMService()
            RESUME_ANALYSIS_USER_PROMPT.format(
                    target_role=interview.target_role,
                    experience=interview.experience,
                    skills=interview.skills,
                    cleaned_text=cleaned_text
                   )
            RESUME_ANALYSIS_SYSTEM_PROMPT.format(target_role=interview.target_role)
            response = gemini_service.generate_resume_context(RESUME_ANALYSIS_USER_PROMPT, RESUME_ANALYSIS_SYSTEM_PROMPT)
            logger.info(f"LLM context generated for interview {interview_id}")

            interview.interview_context = {
                "candidate_name": response.candidate_name,
                "years_of_experience": response.years_of_experience,
                "skills": response.skills,
                "projects": [p.model_dump() for p in response.projects],
                "work_experience": [w.model_dump() for w in response.work_experience],
                "education": response.education,
                "strength_areas": response.strength_areas,
                "recommended_topics": response.recommended_topics,
                "difficulty_level": response.difficulty_level,
                "target_role": response.target_role
            }
            interview.resume_summary = response.resume_summary
            interview.retrieval_summary = response.retrieval_summary
            reponse_summary = response.resume_summary
            retrieval_summary = response.retrieval_summary
            resume_embedding, retrieval_embedding = create_resume_embeddings(retrieval_summary, reponse_summary)
            interview.resume_embedding = resume_embedding
            interview.retrieval_embedding = retrieval_embedding
            interview.status = InterviewStatus.RESUME_READY.value
            db.add(interview)

            # Remove Resume file from minio
            minio_service.delete_file(config.bucket_name, interview.resume_url)
    except Exception as e:
        logger.error(f"Failed to extract resume context due to: {e}")
        raise
    finally:
        if file_name is not None and os.path.exists(file_name):
            os.remove(file_name)