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
    db: Session,
    questions: list,
    interview_context: dict
):
    try:
        # { "skills": [ "Python", "SQL", "FastAPI", "PostgreSQL", "RabbitMQ", "Docker", "Kubernetes", "REST APIs", "Async Programming", "Distributed Systems", "Event-Driven Architecture", "Git", "Grafana", "Ollama", "pgvector" ], 
        # "projects": [ { "name": "AI-Powered Interview Platform", "description": "Developed an AI-powered mock interview platform utilizing embedding-based semantic search with vector similarity retrieval (pgvector) across 600+ interview questions. Designed asynchronous pipelines for resume parsing, embedding generation, semantic retrieval, and LLM-based question personalization.", 
        # "technologies": [ "FastAPI", "Ollama", "Qwen 2.5", "PostgreSQL", "pgvector", "Sentence Transformers", "LLM" ] } ], 
        # "education": [ "B.Tech, Computer Science Engineering, Dehradun Institute of Technology, 2021 - 2025" ], 
        # "candidate_name": "AAMRI GULERIA", 
        # "strength_areas": [ "Backend Development (FastAPI, Async, REST APIs)", "Database Management & Optimization (PostgreSQL, GIN Indexing, Query Optimization)", "Distributed Systems & Messaging (RabbitMQ, Event-Driven Architecture)", "DevOps & Containerization (Docker, Kubernetes)", "Data Pipeline & PII/Security Workflows" ], 
        # "work_experience": [ { "role": "Software Developer", "company": "Appvin Technologies", "duration": "Jan 2025 - Present", "responsibilities": [ "Engineered FastAPI dashboard services with PII validation and security controls.", "Designed enterprise risk assessment workflows using weighted criticality and compliance scoring models.", "Re-engineered Backend-for-Frontend (BFF) layer with query streaming, cutting frontend API calls by 60-70%.", "Optimized PostgreSQL performance using GIN and composite indexing, reducing query latency by 60-70%.", "Architected an end-to-end RabbitMQ-based multi-channel notification system, achieving 99.5% delivery success.", "Built ingestion and profiling pipelines to classify and structure incoming data, detecting sensitive data (PII) patterns." ] }, { "role": "Software Development Engineer Intern", "company": "Bhejooo", "duration": "Jun 2024 - Sep 2024", "responsibilities": [ "Implemented custom validation features and data integrity checks that streamlined order management workflows and reduced manual data-entry errors." ] } ], "difficulty_level": "Medium", "recommended_topics": [ "Distributed Systems Design & Scalability", "Microservices Architecture with FastAPI", "PostgreSQL Performance Tuning & Advanced Features", "Cloud-Native Deployment (Docker, Kubernetes)", "Messaging Queues (RabbitMQ) & Event-Driven Patterns", "API Security & Data Validation" ], "years_of_experience": 2 }
        target_role = interview_context["target_role"]
        recommended_topics = interview_context["recommended_topics"]
        skills = interview_context["skills"]
        filtered_questions = []
        for question in questions:
            marking = 0
            original_question = db.execute(select(Question).where(question.question_id == Question.id)).scalars().one_or_none()
            if original_question is not None:
                # if original_question.role is not None:
                #     if any(role.lower() in target_role.lower() for role in original_question.role):
                #         marking += 1
                # if original_question.topics is not None:
                #     if any(topic.lower() in " ".join(recommended_topics).lower() for topic in original_question.topics):
                #         marking += 1
                if original_question.skills is not None:
                    if any(skill.lower() in " ".join(skills).lower() for skill in original_question.skills):
                        marking += 1
                if marking > 0:
                    filtered_questions.append((original_question, marking))
    except Exception as e:
        logger.error(f"Error filtering questions: {e}")
        return []
