from logging import getLogger
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from models.Interview import InterviewQuestion
from services.llm_service import LLMService
from database.session_manager import db_manager
from core.config import config
from services.celery_app import celery_app

logger = getLogger(__name__)


def should_generate_follow_up(score: float, evaluation_recommends_follow_up: bool) -> bool:
    return (
        evaluation_recommends_follow_up
        and score < config.follow_up_score_threshold
    )


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_follow_up_question(evaluation: dict):
    try:
        interview_question_id = evaluation["interview_question_id"]
        if not evaluation["should_follow_up"]:
            logger.info(
                "Skipping follow-up for interview question %s: evaluation criteria not met",
                interview_question_id,
            )
            return

        with db_manager.sync_session_scope() as db:
            interview_question = db.execute(
                select(InterviewQuestion)
                .options(selectinload(InterviewQuestion.interview))
                .where(InterviewQuestion.id == interview_question_id)
            ).scalars().one_or_none()

            if not interview_question:
                logger.error(f"Interview question {interview_question_id} not found")
                return


            user_answer = interview_question.user_answer
            if not user_answer:
                logger.error(f"No user answer for interview question {interview_question_id}")
                return

            interview = interview_question.interview
            existing_follow_up = db.execute(
                select(InterviewQuestion.id).where(
                    InterviewQuestion.parent_question_id == interview_question_id,
                    InterviewQuestion.is_follow_up.is_(True),
                )
            ).scalar_one_or_none()
            if existing_follow_up is not None:
                logger.info(
                    "Follow-up already exists for interview question %s",
                    interview_question_id,
                )
                return

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

            llm_service = LLMService()
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

@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
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
                return {
                    "interview_question_id": interview_question_id,
                    "should_follow_up": False,
                }

            interview = interview_question.interview
            resume_context = interview.interview_context or {}
            is_personalized = True if interview_question.personalized_question else False
            question = interview_question.personalized_question or interview_question.original_question
            original_expected_answer = interview_question.original_expected_answer
            user_answer = interview_question.user_answer

            if not user_answer:
                logger.error(f"No user answer for interview question {interview_question_id}")
                return {
                    "interview_question_id": interview_question_id,
                    "should_follow_up": False,
                }

            llm_service = LLMService()
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
            should_follow_up = should_generate_follow_up(
                result.score,
                result.follow_ups,
            )

        return {
            "interview_question_id": interview_question_id,
            "should_follow_up": should_follow_up,
            "score": result.score,
        }

    except Exception as e:
        logger.error(f"Error evaluating answer for interview question {interview_question_id}: {e}")
        raise
