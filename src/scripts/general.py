import re
from logging import getLogger
from database.session_manager import db_manager
from models.Interview import Question
from services.question_enrichment_service import QuestionEnrichmentService

logger = getLogger(__name__)


def clean_markdown(text: str) -> str:
    if not text:
        return ""

    # Remove bold/italic markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Remove markdown headings
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove bullet markers
    text = re.sub(r"^[\-\*\+]\s*", "", text, flags=re.MULTILINE)

    # Remove common emojis
    text = re.sub(r"[✅❌⚠️🔥📌👉]", "", text)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def store_questions_in_bank(questions: list):
    try:
        db_question_entries = []
        for question in questions:
            logger.info(
                f"Storing question: "
                f"{question['question_text'][:50]}..."
            )
            question_entry = Question(
                question_text=clean_markdown(question["question_text"]),
                expected_answer=clean_markdown(question["expected_answer"]),
                source=question["source"],
                category="general",
                difficulty="unknown",
                question_type="technical",
                skills=[]
            )
            db_question_entries.append(question_entry)

        with db_manager.sync_session_scope() as session:
            session.add_all(db_question_entries)
            session.commit()
            logger.info(
                f"Successfully stored "
                f"{len(db_question_entries)} questions"
            )
            enrichment_service = QuestionEnrichmentService(session)
            enrichment_service.enrich_question_bank()
    except Exception as e:
        logger.error(
            f"Failed to store questions in bank: {e}"
        )
        raise