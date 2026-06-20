from logging import getLogger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.Interview import InterviewQuestion
from services.llm_service import GeminiService
from database.session_manager import db_manager

logger = getLogger(__name__)

def evaluate_answer(interview_question_id: int):
    try:
        with db_manager.sync_session_scope() as db:
            interview_question = db.execute(
                select(InterviewQuestion)
                .options(selectinload(InterviewQuestion.interview))
                .where(InterviewQuestion.id == interview_question_id)
            ).scalars().one_or_none()

            if not interview_question:
                logger.error(f"Interview question {interview_question_id} not found")
                return

            interview = interview_question.interview
            resume_context = interview.interview_context or {}
            question = interview_question.personalized_question or interview_question.original_question
            user_answer = interview_question.user_answer

            if not user_answer:
                logger.error(f"No user answer for interview question {interview_question_id}")
                return

            llm_service = GeminiService()
            result = llm_service.get_question_evaluation(
                interview_question_id=interview_question_id,
                interview_context=resume_context,
                question=question,
                user_answer=user_answer
            )

            interview_question.score = result.score
            interview_question.feedback = result.feedback
            interview_question.strengths = result.strengths
            interview_question.gaps = result.gaps
            db.add(interview_question)
            logger.info(f"Evaluation saved for interview question {interview_question_id}: score={result.score}")

    except Exception as e:
        logger.error(f"Error evaluating answer for interview question {interview_question_id}: {e}")
        raise
