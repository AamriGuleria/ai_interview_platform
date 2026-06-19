import logging
from sqlalchemy import select
from models.Interview import Interview, InterviewQuestion
from services.embeddings import retrieve_questions_from_embedding
from services.llm_service import GeminiService
from database.session_manager import db_manager

logger = logging.getLogger(__name__)

PERSONALIZATION_BATCH_SIZE = 5


def prepare_interview(interview_id: int):
    try:
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()

            if not interview:
                raise Exception("Interview not found")

            interview.status = "preparing"
            db.commit()

            # Step 1: Retrieve questions via embedding similarity
            questions = retrieve_questions_from_embedding(
                db,
                interview.resume_embedding,
                limit=30
            )
            logger.info(f"Retrieved {len(questions)} questions for interview {interview_id}")

            # Step 2: Save all as InterviewQuestion records
            for question in questions:
                iq = InterviewQuestion(
                    interview_id=interview_id,
                    original_question=question.question_text,
                    original_expected_answer=question.expected_answer,
                    question_id=question.id
                )
                db.add(iq)
            db.commit()
            logger.info(f"Saved {len(questions)} interview questions for interview {interview_id}")

            # Step 3: Personalize in batches
            saved_iqs = db.execute(
                select(InterviewQuestion).where(
                    InterviewQuestion.interview_id == interview_id,
                    InterviewQuestion.personalized_question.is_(None)
                )
            ).scalars().all()

            gemini_service = GeminiService()
            resume_context = interview.interview_context or {}

            for i in range(0, len(saved_iqs), PERSONALIZATION_BATCH_SIZE):
                batch = saved_iqs[i: i + PERSONALIZATION_BATCH_SIZE]
                batch_num = i // PERSONALIZATION_BATCH_SIZE + 1
                batch_payload = [
                    {
                        "id": iq.id,
                        "question_text": iq.original_question,
                        "expected_answer": iq.original_expected_answer
                    }
                    for iq in batch
                ]
                try:
                    result = gemini_service.get_personalized_questions(
                        batch_payload,
                        resume_context
                    )
                    id_to_iq = {iq.id: iq for iq in batch}
                    for pq in result.questions:
                        iq = id_to_iq.get(pq.id)
                        if iq:
                            iq.personalized_question = pq.personalized_question
                    db.commit()
                    logger.info(f"Personalized batch {batch_num} for interview {interview_id}")
                except Exception as e:
                    logger.error(f"Personalization batch {batch_num} failed: {e}")
                    db.rollback()

            # Step 4: Mark as in_progress
            interview.status = "in_progress"
            db.commit()
            logger.info(f"Interview {interview_id} is ready to start")

    except Exception as e:
        logger.error(f"Failed to prepare interview {interview_id}: {e}")
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()
            if interview:
                interview.status = "preparation_failed"
                db.commit()
        raise
