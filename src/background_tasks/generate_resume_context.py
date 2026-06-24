from sqlalchemy import select
from sqlalchemy.orm import Session
from models.Interview import Interview, InterviewStatus
from services.llm_service import GeminiService
from database.session_manager import db_manager

def generate_context(interview_id: int):
    with db_manager.sync_session_scope() as db:
        interview = db.execute(
            select(Interview).where(Interview.id == interview_id)
        ).scalars().one_or_none()
        if not interview:
            raise Exception("Interview not found")
        prompt = f"""
        You are an expert technical recruiter.

        Analyze the following candidate.

        Target Role:
        {interview.target_role}

        Experience:
        {interview.experience}

        Declared Skills:
        {interview.skills}

        Resume:
        {interview.resume_text}

        Instructions:

        1. Extract technical skills.
        2. Identify projects.
        3. Identify strongest areas.
        4. Suggest interview topics.
        5. Decide interview difficulty.
        6. Create a recruiter-style summary.

        Return only structured data.
        """
        gemini_service = GeminiService()
        response = gemini_service.generate_resume_context(prompt)
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
        interview.status = InterviewStatus.RESUME_READY.value
        db.add(interview)