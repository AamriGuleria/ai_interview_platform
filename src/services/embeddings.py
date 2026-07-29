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

def create_question_embeddings(db: Session):
    try:
        result = db.execute(
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
        logger.info("Question embeddings created successfully")
    except Exception as ex:
        logger.error(f"Error creating question embeddings: {ex}")

def create_resume_embeddings(resume_context: text):
    try:
        resume_embedding = model.encode(
            resume_context,
            show_progress_bar=False
        ).tolist()
        return resume_embedding
    except Exception as ex:
        logger.error(f"Error creating resume embedding: {ex}")
        return None
    
def retrieve_questions_from_embedding(
    db: Session,
    resume_embedding,
    limit=50
):
    try:
        distance =  Question.embedding.cosine_distance(resume_embedding)
        results =  (
            db.execute(
                select(Question, distance)
                .where(
                    Question.embedding.is_not(None)
                )
                .order_by(distance)
                .limit(limit)
            )
            .all()
        )
        question_results = []
        for question, dist_value in results:
            question.distance = float(dist_value)
            question.similarity = 1 - float(dist_value)
            question_results.append(question)
        return question_results
    except Exception as e:
        logger.error(f"Error retrieving questions from embedding: {e}")
        return []


def filter_questions(
    questions: list,
    interview_context: dict
):
    try:
        pass
    except Exception as e:
        logger.error(f"Error filtering questions: {e}")
        return []
