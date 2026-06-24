import logging
from sqlalchemy import select
from models.Interview import Interview, InterviewStatus
from services.embeddings import create_resume_embeddings
from services.minio_client import MinioClient
from services.llm_service import GeminiService
from core.config import config
from database.session_manager import db_manager
import tempfile
import fitz
import os
import re

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

            # Step 2: Call LLM
            prompt = f"""
            You are an expert technical recruiter. Analyze the candidate and return ONLY valid JSON.
            
            Target Role: {interview.target_role}
            Experience: {interview.experience}
            Declared Skills: {interview.skills}
            Resume: {cleaned_text}
            
            Return JSON in this exact format:
            {{
                "candidate_name": "John Doe",
                "years_of_experience": 5,
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "projects": [
                    {{
                        "name": "Project Name",
                        "description": "Project description",
                        "technologies": ["Python", "FastAPI"]
                    }}
                ],
                "work_experience": [
                    {{
                        "company": "Company Name",
                        "role": "Software Engineer",
                        "duration": "2 years",
                        "responsibilities": ["Developed APIs", "Optimized queries"]
                    }}
                ],
                "education": ["Bachelor's in Computer Science"],
                "strength_areas": ["Backend Development", "Database Optimization"],
                "recommended_topics": ["System Design", "API Architecture"],
                "difficulty_level": "Medium",
                "resume_summary": "Candidate summary for recruiter"
            }}
            
            Rules:
            - Extract candidate name from resume
            - Calculate years of experience from work history
            - List all technical skills found
            - Extract 2-3 key projects with descriptions
            - Include work experience with responsibilities
            - Add education information
            - Identify 3-4 strength areas
            - Suggest 5-6 interview topics
            - Set difficulty: Beginner/Medium/Advanced
            - Write recruiter summary (2-3 sentences)
            
            Return JSON only.
            """
            gemini_service = GeminiService()
            response = gemini_service.generate_resume_context(prompt)
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
                "difficulty_level": response.difficulty_level
            }
            interview.resume_summary = response.resume_summary
            reponse_summary = response.resume_summary
            resume_embedding = create_resume_embeddings(reponse_summary)
            interview.resume_embedding = resume_embedding
            interview.status = InterviewStatus.RESUME_READY.value
            db.add(interview)
    except Exception as e:
        logger.error(f"Failed to extract resume context due to: {e}")
        raise
    finally:
        if file_name is not None and os.path.exists(file_name):
            os.remove(file_name)