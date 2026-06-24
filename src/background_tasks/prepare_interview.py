import logging
from sqlalchemy import select
from models.Interview import Interview, InterviewQuestion, InterviewStatus
from services.embeddings import retrieve_questions_from_embedding
from services.llm_service import GeminiService
from database.session_manager import db_manager

logger = logging.getLogger(__name__)

PERSONALIZATION_BATCH_SIZE = 5
# RESUME_TECH_CATEGORIES = {
#     "Python",
#     "PostgreSQL",
#     "Docker",
#     "RabbitMQ",
#     "FastAPI",
#     "SQL",
#     "AWS"
# }
PERSONALIZABLE_TYPES = {
    "Behavioral",
    "Project",
    "System Design",
    "Scenario Based"
}
def should_personalize(question, resume_context):
    if question.question_type in PERSONALIZABLE_TYPES:
        return True

    question_skills = set(
        skill.lower()
        for skill in (question.skills or [])
    )

    resume_skills = set(
        skill.lower()
        for skill in resume_context.get("skills", [])
    )

    if not question_skills:
        return False

    overlap = len(
        question_skills.intersection(
            resume_skills
        )
    )

    overlap_ratio = overlap / len(question_skills)

    return overlap_ratio >= 0.5

def prepare_interview(interview_id: int):
    try:
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()

            if not interview:
                raise Exception("Interview not found")

            interview.status = InterviewStatus.PREPARING_QUESTIONS.value
            db.commit()

            questions = retrieve_questions_from_embedding(
                db,
                interview.resume_embedding,
                limit=30
            )
            logger.info(f"Retrieved {len(questions)} questions for interview {interview_id}")
            questions_to_personalize = []
            question_to_iq = {}
            resume_context = interview.interview_context or {}
            for question in questions:
                if should_personalize(
                    question,
                    resume_context
                ):
                    questions_to_personalize.append(question)

                iq = InterviewQuestion(
                    interview_id=interview_id,
                    original_question=question.question_text,
                    original_expected_answer=question.expected_answer,
                    question_id=question.id
                )
                db.add(iq)
                db.flush()
                question_to_iq[question.id] = iq
            db.commit()
            logger.info(f"Saved {len(questions)} interview questions for interview {interview_id}")

            personalizable_iqs = [
                question_to_iq[q.id]
                for q in questions_to_personalize
            ]

            gemini_service = GeminiService()
            for i in range(
                0,
                len(personalizable_iqs),
                PERSONALIZATION_BATCH_SIZE
            ):
                batch = personalizable_iqs[
                    i : i + PERSONALIZATION_BATCH_SIZE
                ]
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

            interview.status = InterviewStatus.QUESTIONS_READY.value
            db.commit()
            logger.info(f"Interview {interview_id} is ready to start")

    except Exception as e:
        logger.error(f"Failed to prepare interview {interview_id}: {e}")
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()
            if interview:
                interview.status = InterviewStatus.FAILED.value
                db.commit()
        raise
