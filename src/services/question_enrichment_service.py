from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from models.Interview import Question
from services.llm_service import GeminiService
from logging import getLogger

logger = getLogger(__name__)

class QuestionEnrichmentService():
    def __init__(
        self,
        db: Session
    ):
        self.db = db
        self.gemini_service = GeminiService()

    def enrich_question_bank(self):
        questions = (
            self.db.execute(
                select(Question)
                .where(
                    or_(
                        Question.difficulty.is_(None),
                        Question.difficulty.ilike("unknown"),
                    )
                )
            )
        ).scalars().all()
        logger.info(f"Found {len(questions)} questions to enrich")
        batch_size = 0
        for question in questions:
            metadata = (
                self.gemini_service
                .enrich_question_metadata(
                    question.question_text,
                    question.expected_answer
                )
            )
            question.category = metadata.category
            question.difficulty = metadata.difficulty
            question.skills = metadata.skills
            question.question_type = metadata.question_type
            batch_size += 1
            if batch_size >= 100:
                self.db.commit()
                batch_size = 0
        self.db.commit()
