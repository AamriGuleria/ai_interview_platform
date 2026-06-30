from logging import getLogger
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from models.Interview import InterviewQuestion
from services.llm_service import GeminiService
from database.session_manager import db_manager
from core.config import config

logger = getLogger(__name__)


def generate_follow_up_question(interview_question_id: int):
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

            if interview_question.is_follow_up:
                logger.info(
                    f"Skipping follow-up generation for follow-up question {interview_question_id}"
                )
                return

            user_answer = interview_question.user_answer
            if not user_answer:
                logger.error(f"No user answer for interview question {interview_question_id}")
                return

            interview = interview_question.interview
            resume_context = interview.interview_context or {}
            current_follow_up_count = db.execute(
                select(func.count(InterviewQuestion.id)).where(
                    InterviewQuestion.interview_id == interview.id,
                    InterviewQuestion.is_follow_up.is_(True),
                )
            ).scalar_one()

            if current_follow_up_count >= int(getattr(config, "max_follow_ups_per_interview", 3)):
                logger.info(
                    f"Maximum follow-up count reached for interview {interview.id}: {current_follow_up_count}"
                )
                return

            llm_service = GeminiService()
            follow_up_payload = llm_service.get_follow_up_question(
                interview_context=resume_context,
                original_question=interview_question.personalized_question or interview_question.original_question,
                user_answer=user_answer,
                expected_answer=interview_question.original_expected_answer,
            )
            follow_up_question_text = follow_up_payload.get("follow_up_question") or follow_up_payload.get("question")

            if not follow_up_question_text:
                logger.info(
                    f"No follow-up question suggested for interview question {interview_question_id}"
                )
                return

            follow_up_question = InterviewQuestion(
                interview_id=interview.id,
                original_question=follow_up_question_text,
                original_expected_answer="",
                is_follow_up=True,
                parent_question_id=interview_question.id,
                display_order=interview_question.display_order + 0.5,
            )
            interview_question.follow_up_requested = True
            db.add(interview_question)
            db.add(follow_up_question)
            db.commit()

            logger.info(
                f"Follow-up question created for interview question {interview_question_id}: {follow_up_question_text}"
            )

    except Exception as e:
        logger.error(f"Error generating follow-up question for interview question {interview_question_id}: {e}")
        raise


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
            is_personalized = True if interview_question.personalized_question else False
            question = interview_question.personalized_question or interview_question.original_question
            original_expected_answer = interview_question.original_expected_answer
            user_answer = interview_question.user_answer

            if not user_answer:
                logger.error(f"No user answer for interview question {interview_question_id}")
                return

            llm_service = GeminiService()
            result = llm_service.get_question_evaluation(
                interview_question_id=interview_question_id,
                interview_context=resume_context,
                question=question,
                user_answer=user_answer,
                is_personalized = is_personalized,
                expected_answer=original_expected_answer
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
