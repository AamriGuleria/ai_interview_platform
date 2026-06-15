from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from models.Interview import Question
from services.llm_service import GeminiService
from logging import getLogger
import time

logger = getLogger(__name__)

BATCH_SIZE = 10
  
class QuestionEnrichmentService():
    def __init__(self, db: Session):
        self.db = db
        self.gemini_service = GeminiService()

    def enrich_question_bank(self):
        questions = self.db.execute(
            select(Question).where(
                or_(
                    Question.difficulty.is_(None),
                    Question.difficulty.ilike("unknown"),
                )
            )
        ).scalars().all()

        total = len(questions)
        logger.info(f"Found {total} questions to enrich")

        for i in range(0, total, BATCH_SIZE):
            batch = questions[i: i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            logger.info(f"Enriching batch {batch_num} ({len(batch)} questions)")

            batch_payload = [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "expected_answer": q.expected_answer
                }
                for q in batch
            ]

            result = None
            for attempt in range(3):
                try:
                    result = self.gemini_service.enrich_questions_metadata(batch_payload)
                    break
                except RuntimeError as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        wait = 60 * (attempt + 1)
                        logger.warning(f"Rate limited on batch {batch_num}, waiting {wait}s (attempt {attempt + 1}/3)")
                        time.sleep(wait)
                    else: 
                        logger.error(f"Batch {batch_num} failed: {e}")
                        break

            if result is None:
                logger.error(f"Batch {batch_num} skipped after retries")
                continue

            id_to_question = {q.id: q for q in batch}
            for item in result.questions:
                q = id_to_question.get(item.id)
                if not q:
                    logger.warning(f"Question id {item.id} not found in batch, skipping")
                    continue
                q.category = item.category
                q.difficulty = item.difficulty
                q.skills = item.skills
                q.question_type = item.question_type

            self.db.commit()
            logger.info(f"Batch {batch_num} committed")

        logger.info(f"Enrichment complete for {total} questions")
