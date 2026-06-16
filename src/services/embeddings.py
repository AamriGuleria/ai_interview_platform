from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from logging import getLogger

from torch import cosine_similarity
from models.Interview import Question
from sqlalchemy import select, text

logger = getLogger(__name__)


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

def create_question_embeddings(self, db: Session):
    try:
        result = self.db.execute(
            select(Question).where(
                Question.embedding.is_(None)).execution_options(stream_results=True)
        )
        for question in result:
            question_obj = question[0]
            embedding = model.encode(
                question_obj.question_text,
                show_progress_bar=False
            ).tolist()
            question_obj.embedding = embedding
            db.add(question_obj)
        db.commit()
    except Exception as ex:
        logger.error(f"Error creating question embeddings: {ex}")

def retrieve_question_by_resume(resume_summary: text, db: Session):
    try:
        resume_embedding = model.encode(
            resume_summary,
            show_progress_bar=False
        ).tolist()
        result = db.execute(
            select(Question).where(
                Question.embedding.is_not(None)
            ).execution_options(stream_results=True)
        )
        questions_with_embeddings = [
            question[0] for question in result
        ]

        if not questions_with_embeddings:
            logger.warning("No questions with embeddings found.")
            return []

        questions_with_similarity = []
        for question in questions_with_embeddings:
            similarity = cosine_similarity(resume_embedding, question.embedding)
            questions_with_similarity.append((question, similarity))

        questions_with_similarity.sort(key=lambda x: x[1], reverse=True)

        top_questions = [q[0] for q in questions_with_similarity[:50]]

        return top_questions

    except Exception as ex:
        logger.error(f"Error retrieving questions by resume: {ex}")
        return []