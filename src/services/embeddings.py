from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from logging import getLogger
from models.Interview import Question
from sqlalchemy import select

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